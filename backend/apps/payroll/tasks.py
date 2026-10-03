"""
SERENIA ACCOUNTING — payroll/tasks.py
========================================
Celery tasks for payroll processing.
Routed to the 'payroll' queue (see config/settings: CELERY_TASK_ROUTES).
"""

from decimal import Decimal
from celery import shared_task
from django.db import transaction
from django.utils import timezone


@shared_task(bind=True, max_retries=2)
def process_payroll_run(self, payroll_run_id: str, processed_by_id: str):
    """
    Calculates payslips for all active employees in the company,
    posts a consolidated journal entry (Salary Expense Dr / Bank Cr,
    plus statutory liability lines), and marks the run as completed.
    """
    from apps.payroll.models import PayrollRun, Payslip, Employee
    from apps.accounts.models import User
    from apps.ledger.models import JournalEntry, JournalLine, Ledger, VoucherType, VoucherStatus

    try:
        payroll_run = PayrollRun.objects.select_related('company', 'financial_year').get(id=payroll_run_id)
        processed_by = User.objects.get(id=processed_by_id)
        company = payroll_run.company

        employees = Employee.objects.filter(company=company, is_active=True).select_related('salary_structure')

        total_gross = Decimal('0')
        total_deductions = Decimal('0')
        total_net = Decimal('0')

        with transaction.atomic():
            for emp in employees:
                structure = emp.salary_structure
                if not structure:
                    continue

                # Simplified CTC-based calculation (assumes salary_structure stores % of an
                # employee-level base CTC field in a real implementation; here we use
                # a fixed placeholder base for demonstration — replace with emp.ctc).
                base_ctc = Decimal('50000')  # TODO: replace with employee.monthly_ctc field

                basic = (base_ctc * structure.basic_percent / 100).quantize(Decimal('0.01'))
                hra = (base_ctc * structure.hra_percent / 100).quantize(Decimal('0.01'))
                special = (base_ctc * structure.special_allowance_percent / 100).quantize(Decimal('0.01'))
                transport = structure.transport_allowance
                medical = structure.medical_allowance

                gross = basic + hra + special + transport + medical

                pf_employee = (basic * Decimal('0.12')).quantize(Decimal('0.01')) if structure.pf_applicable else Decimal('0')
                pf_employer = pf_employee
                esi_employee = (gross * Decimal('0.0075')).quantize(Decimal('0.01')) if structure.esi_applicable and gross <= 21000 else Decimal('0')
                esi_employer = (gross * Decimal('0.0325')).quantize(Decimal('0.01')) if structure.esi_applicable and gross <= 21000 else Decimal('0')
                professional_tax = Decimal('200') if structure.professional_tax_applicable and gross > 15000 else Decimal('0')

                deductions = pf_employee + esi_employee + professional_tax
                net = gross - deductions

                Payslip.objects.update_or_create(
                    payroll_run=payroll_run, employee=emp,
                    defaults={
                        'basic': basic, 'hra': hra, 'special_allowance': special,
                        'transport_allowance': transport, 'medical_allowance': medical,
                        'gross_salary': gross,
                        'pf_employee': pf_employee, 'pf_employer': pf_employer,
                        'esi_employee': esi_employee, 'esi_employer': esi_employer,
                        'professional_tax': professional_tax,
                        'total_deductions': deductions, 'net_salary': net,
                    }
                )

                total_gross += gross
                total_deductions += deductions
                total_net += net

            # Post consolidated journal entry
            salary_ledger = Ledger.objects.filter(company=company, name__icontains='Salaries').first()
            bank_ledger = Ledger.objects.filter(company=company, is_bank_account=True).first()
            pf_ledger = Ledger.objects.filter(company=company, name__icontains='PF Payable').first()
            pt_ledger = Ledger.objects.filter(company=company, name__icontains='Professional Tax Payable').first()

            journal_entry = None
            if salary_ledger and bank_ledger:
                fy = company.current_financial_year
                voucher_count = JournalEntry.objects.filter(
                    company=company, voucher_type=VoucherType.JOURNAL, financial_year=fy
                ).count()
                voucher_number = f"PAY-{fy.label.replace('FY ', '')}-{voucher_count + 1:05d}"

                journal_entry = JournalEntry.objects.create(
                    company=company, financial_year=fy, voucher_type=VoucherType.JOURNAL,
                    voucher_number=voucher_number, date=timezone.now().date(),
                    narration=f"Payroll for {payroll_run.month}/{payroll_run.year}",
                    status=VoucherStatus.POSTED, created_by=processed_by,
                    approved_by=processed_by, approved_at=timezone.now(),
                )

                JournalLine.objects.create(journal=journal_entry, ledger=salary_ledger, debit_amount=total_gross, sort_order=0)

                if pf_ledger:
                    pf_total = sum((p.pf_employee for p in payroll_run.payslips.all()), Decimal('0'))
                    if pf_total:
                        JournalLine.objects.create(journal=journal_entry, ledger=pf_ledger, credit_amount=pf_total, sort_order=1)

                if pt_ledger:
                    pt_total = sum((p.professional_tax for p in payroll_run.payslips.all()), Decimal('0'))
                    if pt_total:
                        JournalLine.objects.create(journal=journal_entry, ledger=pt_ledger, credit_amount=pt_total, sort_order=2)

                JournalLine.objects.create(journal=journal_entry, ledger=bank_ledger, credit_amount=total_net, sort_order=3)

            payroll_run.total_gross = total_gross
            payroll_run.total_deductions = total_deductions
            payroll_run.total_net = total_net
            payroll_run.status = 'completed'
            payroll_run.processed_at = timezone.now()
            payroll_run.processed_by = processed_by
            payroll_run.journal_entry = journal_entry
            payroll_run.save()

        # Trigger payslip email notifications
        send_payslip_notifications.delay(payroll_run_id)

        return {'status': 'completed', 'total_net': str(total_net)}

    except Exception as exc:
        from apps.payroll.models import PayrollRun
        PayrollRun.objects.filter(id=payroll_run_id).update(status='draft')
        raise self.retry(exc=exc, countdown=30)


@shared_task
def send_payslip_notifications(payroll_run_id: str):
    """Sends payslip-ready email notifications to all employees in the run."""
    from apps.payroll.models import PayrollRun
    from django.core.mail import send_mass_mail
    from django.conf import settings

    payroll_run = PayrollRun.objects.get(id=payroll_run_id)
    messages = []
    for payslip in payroll_run.payslips.select_related('employee'):
        if payslip.employee.user and payslip.employee.user.email:
            messages.append((
                f"Payslip for {payroll_run.month}/{payroll_run.year}",
                f"Dear {payslip.employee.first_name},\n\nYour payslip for "
                f"{payroll_run.month}/{payroll_run.year} is ready. "
                f"Net salary: {payslip.net_salary}\n\nRegards,\nSerenia HR",
                settings.DEFAULT_FROM_EMAIL,
                [payslip.employee.user.email],
            ))

    if messages:
        send_mass_mail(messages, fail_silently=True)

    return {'notifications_sent': len(messages)}
