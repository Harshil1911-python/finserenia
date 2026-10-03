"""
SERENIA ACCOUNTING — core/urls/dashboard.py + dashboard view
================================================================
GET /api/v1/dashboard/summary/
Returns the consolidated dashboard payload (Revenue, Expenses,
Profit, Cash Position, Receivables, Payables, Tax Summary,
Payroll Summary, Inventory Value, Banking Summary).

Cached in Redis for CACHE_TTL_DASHBOARD seconds (default 5 min).
"""

from decimal import Decimal
from datetime import date, timedelta
from django.urls import path
from django.core.cache import cache
from django.conf import settings
from django.db.models import Sum, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.accounts.models import Company
from apps.ledger.models import Ledger, LedgerGroup, JournalEntry, JournalLine, VoucherStatus, AccountNature
from apps.inventory.models import Item, StockEntry
from apps.payroll.models import PayrollRun


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company_id = request.headers.get('X-Company-Id')
        if not company_id:
            return Response({'error': 'Company ID required'}, status=400)

        try:
            company = Company.objects.get(id=company_id, is_active=True)
        except Company.DoesNotExist:
            return Response({'error': 'Company not found'}, status=404)

        if not request.user.is_super_admin:
            if not company.user_accesses.filter(user=request.user, is_active=True).exists():
                return Response({'error': 'Access denied'}, status=403)

        cache_key = f"dashboard_summary:{company.id}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        fy = company.current_financial_year
        if not fy:
            return Response({
                'revenue': '0', 'expenses': '0', 'profit': '0', 'profit_percent': '0',
                'cash_position': '0', 'receivables': '0', 'payables': '0',
                'tax_liability': '0', 'inventory_value': '0', 'payroll_this_month': '0',
                'bank_balance': '0', 'recent_transactions': [], 'monthly_trend': [],
                'top_ledgers_by_balance': [],
            })

        posted_filter = Q(journal__status__in=[VoucherStatus.APPROVED, VoucherStatus.POSTED])

        # Revenue & Expenses (from journal lines, current FY)
        lines = JournalLine.objects.filter(
            journal__company=company, journal__financial_year=fy
        ).filter(posted_filter).select_related('ledger__group')

        revenue = Decimal('0')
        expenses = Decimal('0')
        for line in lines:
            nature = line.ledger.group.nature
            if nature == AccountNature.INCOME:
                revenue += line.credit_amount - line.debit_amount
            elif nature == AccountNature.EXPENSES:
                expenses += line.debit_amount - line.credit_amount

        profit = revenue - expenses
        profit_percent = (profit / revenue * 100).quantize(Decimal('0.01')) if revenue else Decimal('0')

        # Cash & bank position
        cash_bank_ledgers = Ledger.objects.filter(
            company=company, is_active=True
        ).filter(Q(is_bank_account=True) | Q(group__group_type='current_assets', name__icontains='cash'))

        cash_position = sum((l.get_balance(financial_year=fy) for l in cash_bank_ledgers), Decimal('0'))
        bank_balance = sum(
            (l.get_balance(financial_year=fy) for l in cash_bank_ledgers.filter(is_bank_account=True)),
            Decimal('0')
        )

        # Receivables / Payables (party ledgers)
        receivable_ledgers = Ledger.objects.filter(company=company, is_party_ledger=True, is_active=True)
        receivables = Decimal('0')
        payables = Decimal('0')
        for l in receivable_ledgers:
            bal = l.get_balance(financial_year=fy)
            if bal > 0:
                receivables += bal
            else:
                payables += abs(bal)

        # Tax liability (GST output - input, simplified)
        tax_ledgers = Ledger.objects.filter(company=company, name__iregex=r'(gst|igst|cgst|sgst|tds)', is_active=True)
        tax_liability = sum((l.get_balance(financial_year=fy) for l in tax_ledgers), Decimal('0'))

        # Inventory value
        inventory_value = Item.objects.filter(company=company, is_active=True, maintain_stock=True).aggregate(
            total=Sum('purchase_price')
        )['total'] or Decimal('0')

        # Payroll this month
        today = date.today()
        payroll_run = PayrollRun.objects.filter(company=company, month=today.month, year=today.year).first()
        payroll_this_month = payroll_run.total_net if payroll_run else Decimal('0')

        # Recent transactions
        recent = JournalEntry.objects.filter(company=company).select_related('party').order_by('-created_at')[:8]
        recent_transactions = [{
            'id': str(j.id),
            'date': str(j.date),
            'voucher_type': j.voucher_type,
            'voucher_number': j.voucher_number,
            'party_name': j.party.name if j.party else None,
            'status': j.status,
            'total_amount': str(j.total_amount),
        } for j in recent]

        # Monthly trend (last 6 months)
        monthly_trend = []
        for i in range(5, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=30 * i)
            month_lines = JournalLine.objects.filter(
                journal__company=company,
                journal__date__year=month_date.year,
                journal__date__month=month_date.month,
            ).filter(posted_filter).select_related('ledger__group')

            m_rev = Decimal('0')
            m_exp = Decimal('0')
            for line in month_lines:
                nature = line.ledger.group.nature
                if nature == AccountNature.INCOME:
                    m_rev += line.credit_amount - line.debit_amount
                elif nature == AccountNature.EXPENSES:
                    m_exp += line.debit_amount - line.credit_amount

            monthly_trend.append({
                'month': month_date.strftime('%b %Y'),
                'revenue': float(m_rev),
                'expenses': float(m_exp),
                'profit': float(m_rev - m_exp),
            })

        # Top ledgers by balance
        top_ledgers = []
        for l in Ledger.objects.filter(company=company, is_active=True)[:50]:
            bal = l.get_balance(financial_year=fy)
            if bal != 0:
                top_ledgers.append({'name': l.name, 'balance': str(abs(bal)), 'type': 'Dr' if bal > 0 else 'Cr', '_sort': abs(bal)})
        top_ledgers = sorted(top_ledgers, key=lambda x: x['_sort'], reverse=True)[:5]
        for l in top_ledgers:
            l.pop('_sort')

        result = {
            'revenue': str(revenue),
            'expenses': str(expenses),
            'profit': str(profit),
            'profit_percent': str(profit_percent),
            'cash_position': str(cash_position),
            'receivables': str(receivables),
            'payables': str(payables),
            'tax_liability': str(tax_liability),
            'inventory_value': str(inventory_value),
            'payroll_this_month': str(payroll_this_month),
            'bank_balance': str(bank_balance),
            'recent_transactions': recent_transactions,
            'monthly_trend': monthly_trend,
            'top_ledgers_by_balance': top_ledgers,
        }

        cache.set(cache_key, result, settings.CACHE_TTL_DASHBOARD)
        return Response(result)


urlpatterns = [
    path('summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
]

dashboard_urlpatterns = urlpatterns
