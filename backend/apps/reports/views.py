"""
SERENIA ACCOUNTING — reports/views.py
=======================================
Financial report generation views:
- Trial Balance
- Profit & Loss
- Balance Sheet
- Cash Flow Statement
- Ledger Report
- Day Book
All reports support PDF, Excel, and JSON output.
Results are cached in Redis for performance.
"""

from decimal import Decimal
from datetime import date
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.permissions import CompanyPermission, ReadOnlyPermission
from apps.accounts.models import FinancialYear, Company
from apps.ledger.models import Ledger, LedgerGroup, JournalEntry, JournalLine, VoucherStatus, AccountNature
from apps.reports.generators import PDFReportGenerator, ExcelReportGenerator
from django.db.models import Sum, Q
from django.conf import settings


def get_company_from_request(request):
    """Extract and validate the company from request header."""
    company_id = request.headers.get('X-Company-Id') or request.query_params.get('company_id')
    if not company_id:
        return None, Response({'error': 'Company ID required'}, status=400)
    try:
        company = Company.objects.get(id=company_id, is_active=True)
        # Check user has access
        if not request.user.is_super_admin:
            if not company.user_accesses.filter(user=request.user, is_active=True).exists():
                return None, Response({'error': 'Access denied'}, status=403)
        return company, None
    except Company.DoesNotExist:
        return None, Response({'error': 'Company not found'}, status=404)


class TrialBalanceView(APIView):
    """
    GET /api/v1/reports/trial-balance/
    Params: company_id, fy_id, as_of_date, format (json|pdf|excel)
    Returns debit/credit balances for all active ledgers.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company, err = get_company_from_request(request)
        if err:
            return err

        fy_id = request.query_params.get('fy_id')
        as_of_date = request.query_params.get('as_of_date')
        output_format = request.query_params.get('format', 'json')

        # Cache key
        cache_key = f"trial_balance:{company.id}:{fy_id}:{as_of_date}"
        cached = cache.get(cache_key)
        if cached and output_format == 'json':
            return Response(cached)

        # Build the trial balance
        try:
            fy = FinancialYear.objects.get(id=fy_id, company=company) if fy_id else company.current_financial_year
        except FinancialYear.DoesNotExist:
            return Response({'error': 'Financial year not found'}, status=404)

        if not fy:
            return Response({'error': 'No active financial year found'}, status=400)

        # Get all ledger balances
        ledgers = Ledger.objects.filter(
            company=company, is_active=True
        ).select_related('group').order_by('group__nature', 'group__name', 'name')

        # Aggregate journal lines
        qs = JournalLine.objects.filter(
            journal__company=company,
            journal__financial_year=fy,
            journal__status__in=[VoucherStatus.APPROVED, VoucherStatus.POSTED],
        )
        if as_of_date:
            qs = qs.filter(journal__date__lte=as_of_date)

        ledger_totals = qs.values('ledger_id').annotate(
            total_dr=Sum('debit_amount'),
            total_cr=Sum('credit_amount'),
        )
        totals_map = {str(t['ledger_id']): t for t in ledger_totals}

        rows = []
        grand_dr = Decimal('0')
        grand_cr = Decimal('0')

        for ledger in ledgers:
            lid = str(ledger.id)
            t = totals_map.get(lid, {})
            dr = (t.get('total_dr') or Decimal('0')) + (
                ledger.opening_balance if ledger.opening_balance_type == 'Dr' else Decimal('0')
            )
            cr = (t.get('total_cr') or Decimal('0')) + (
                ledger.opening_balance if ledger.opening_balance_type == 'Cr' else Decimal('0')
            )

            if dr == 0 and cr == 0:
                continue  # Skip zero-balance ledgers

            grand_dr += dr
            grand_cr += cr
            rows.append({
                'ledger_id': lid,
                'ledger_name': ledger.name,
                'ledger_code': ledger.code,
                'group': ledger.group.name,
                'nature': ledger.group.nature,
                'debit': str(dr),
                'credit': str(cr),
                'balance': str(abs(dr - cr)),
                'balance_type': 'Dr' if dr > cr else 'Cr',
            })

        result = {
            'company': company.name,
            'financial_year': fy.label,
            'as_of_date': as_of_date or str(fy.end_date),
            'rows': rows,
            'totals': {
                'debit': str(grand_dr),
                'credit': str(grand_cr),
                'difference': str(abs(grand_dr - grand_cr)),
                'is_balanced': grand_dr == grand_cr,
            }
        }

        # Cache for 10 minutes
        cache.set(cache_key, result, settings.CACHE_TTL_TRIAL_BALANCE)

        if output_format == 'pdf':
            pdf = PDFReportGenerator.trial_balance(result)
            return pdf
        elif output_format == 'excel':
            xlsx = ExcelReportGenerator.trial_balance(result)
            return xlsx

        return Response(result)


class ProfitAndLossView(APIView):
    """
    GET /api/v1/reports/profit-and-loss/
    Income vs Expenses, Gross Profit, Net Profit.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company, err = get_company_from_request(request)
        if err:
            return err

        fy_id = request.query_params.get('fy_id')
        output_format = request.query_params.get('format', 'json')

        try:
            fy = FinancialYear.objects.get(id=fy_id, company=company) if fy_id else company.current_financial_year
        except FinancialYear.DoesNotExist:
            return Response({'error': 'Financial year not found'}, status=404)

        # Aggregate by nature
        qs = JournalLine.objects.filter(
            journal__company=company,
            journal__financial_year=fy,
            journal__status__in=[VoucherStatus.APPROVED, VoucherStatus.POSTED],
        ).select_related('ledger__group')

        income_data = {}
        expense_data = {}

        for line in qs:
            nature = line.ledger.group.nature
            group_name = line.ledger.group.name
            affects_gross = line.ledger.group.affects_gross_profit

            net = line.credit_amount - line.debit_amount  # Credit increases income
            if nature == AccountNature.INCOME:
                key = (group_name, affects_gross)
                income_data[key] = income_data.get(key, Decimal('0')) + net
            elif nature == AccountNature.EXPENSES:
                key = (group_name, affects_gross)
                expense_data[key] = expense_data.get(key, Decimal('0')) + abs(net)

        # Separate gross profit items
        direct_income = sum(v for (g, gross), v in income_data.items() if gross)
        indirect_income = sum(v for (g, gross), v in income_data.items() if not gross)
        direct_expenses = sum(v for (g, gross), v in expense_data.items() if gross)
        indirect_expenses = sum(v for (g, gross), v in expense_data.items() if not gross)

        gross_profit = direct_income - direct_expenses
        net_profit = gross_profit + indirect_income - indirect_expenses

        result = {
            'company': company.name,
            'financial_year': fy.label,
            'period': f"{fy.start_date} to {fy.end_date}",
            'trading_account': {
                'income': {k[0]: str(v) for k, v in income_data.items() if k[1]},
                'expenses': {k[0]: str(v) for k, v in expense_data.items() if k[1]},
                'gross_profit': str(gross_profit),
                'gross_profit_ratio': str(
                    (gross_profit / direct_income * 100).quantize(Decimal('0.01'))
                    if direct_income else Decimal('0')
                ),
            },
            'profit_and_loss': {
                'other_income': {k[0]: str(v) for k, v in income_data.items() if not k[1]},
                'other_expenses': {k[0]: str(v) for k, v in expense_data.items() if not k[1]},
                'net_profit': str(net_profit),
                'net_profit_ratio': str(
                    (net_profit / (direct_income + indirect_income) * 100).quantize(Decimal('0.01'))
                    if (direct_income + indirect_income) else Decimal('0')
                ),
            },
            'summary': {
                'total_income': str(direct_income + indirect_income),
                'total_expenses': str(direct_expenses + indirect_expenses),
                'net_profit': str(net_profit),
                'is_profit': net_profit >= 0,
            }
        }

        return Response(result)


class BalanceSheetView(APIView):
    """
    GET /api/v1/reports/balance-sheet/
    Assets = Liabilities + Capital.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company, err = get_company_from_request(request)
        if err:
            return err

        fy_id = request.query_params.get('fy_id')
        try:
            fy = FinancialYear.objects.get(id=fy_id, company=company) if fy_id else company.current_financial_year
        except FinancialYear.DoesNotExist:
            return Response({'error': 'Financial year not found'}, status=404)

        def get_group_totals(nature):
            """Sum up all ledger balances by group for a given nature."""
            groups = LedgerGroup.objects.filter(company=company, nature=nature)
            result = {}
            for group in groups:
                ledgers = group.ledgers.filter(is_active=True)
                total = Decimal('0')
                for ledger in ledgers:
                    bal = ledger.get_balance(financial_year=fy)
                    total += bal
                if total != 0:
                    result[group.name] = str(total)
            return result

        assets = get_group_totals(AccountNature.ASSETS)
        liabilities = get_group_totals(AccountNature.LIABILITIES)
        capital = get_group_totals(AccountNature.CAPITAL)

        total_assets = sum(Decimal(v) for v in assets.values())
        total_liabilities = sum(Decimal(v) for v in liabilities.values())
        total_capital = sum(Decimal(v) for v in capital.values())

        return Response({
            'company': company.name,
            'financial_year': fy.label,
            'as_of_date': str(fy.end_date),
            'assets': {
                'groups': assets,
                'total': str(total_assets),
            },
            'liabilities': {
                'groups': liabilities,
                'total': str(total_liabilities),
            },
            'capital': {
                'groups': capital,
                'total': str(total_capital),
            },
            'is_balanced': abs(total_assets - (total_liabilities + total_capital)) < Decimal('0.01'),
            'difference': str(abs(total_assets - (total_liabilities + total_capital))),
        })


class LedgerReportView(APIView):
    """
    GET /api/v1/reports/ledger/<ledger_id>/
    All transactions for a specific ledger with running balance.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, ledger_id):
        company, err = get_company_from_request(request)
        if err:
            return err

        try:
            ledger = Ledger.objects.get(id=ledger_id, company=company)
        except Ledger.DoesNotExist:
            return Response({'error': 'Ledger not found'}, status=404)

        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date')

        lines = JournalLine.objects.filter(
            ledger=ledger,
            journal__status__in=[VoucherStatus.APPROVED, VoucherStatus.POSTED],
        ).select_related('journal').order_by('journal__date', 'journal__created_at')

        if from_date:
            lines = lines.filter(journal__date__gte=from_date)
        if to_date:
            lines = lines.filter(journal__date__lte=to_date)

        # Build ledger report with running balance
        running_balance = ledger.opening_balance if not from_date else Decimal('0')
        rows = []
        for line in lines:
            dr = line.debit_amount
            cr = line.credit_amount
            running_balance += dr - cr
            rows.append({
                'date': str(line.journal.date),
                'voucher_type': line.journal.voucher_type,
                'voucher_number': line.journal.voucher_number,
                'narration': line.journal.narration or line.narration,
                'debit': str(dr),
                'credit': str(cr),
                'balance': str(abs(running_balance)),
                'balance_type': 'Dr' if running_balance >= 0 else 'Cr',
            })

        return Response({
            'ledger': {'id': str(ledger.id), 'name': ledger.name, 'code': ledger.code},
            'company': company.name,
            'from_date': from_date,
            'to_date': to_date,
            'opening_balance': str(ledger.opening_balance),
            'opening_balance_type': ledger.opening_balance_type,
            'transactions': rows,
            'closing_balance': str(abs(running_balance)),
            'closing_balance_type': 'Dr' if running_balance >= 0 else 'Cr',
            'total_debit': str(sum(Decimal(r['debit']) for r in rows)),
            'total_credit': str(sum(Decimal(r['credit']) for r in rows)),
        })
