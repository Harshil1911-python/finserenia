"""
SERENIA ACCOUNTING — ledger/bootstrap.py
===========================================
Creates the standard Indian Chart of Accounts template
when a new company is registered. Provides a sensible
starting structure that mirrors Tally/Zoho defaults.
"""

from decimal import Decimal
from apps.ledger.models import LedgerGroup, Ledger, AccountNature, AccountGroup


# Standard group structure: (name, nature, group_type, affects_gross_profit, children[])
STANDARD_GROUPS = [
    # ── ASSETS ──────────────────────────────────────────────
    {
        'name': 'Current Assets', 'nature': AccountNature.ASSETS, 'group_type': AccountGroup.CURRENT_ASSETS,
        'children': [
            {'name': 'Cash-in-Hand', 'ledgers': [{'name': 'Cash', 'opening': '0'}]},
            {'name': 'Bank Accounts', 'ledgers': []},
            {'name': 'Sundry Debtors', 'ledgers': []},
            {'name': 'Stock-in-Hand', 'ledgers': [{'name': 'Closing Stock', 'opening': '0'}]},
            {'name': 'Loans & Advances (Asset)', 'ledgers': []},
            {'name': 'Input Tax Credit', 'ledgers': [
                {'name': 'Input CGST', 'opening': '0'}, {'name': 'Input SGST', 'opening': '0'}, {'name': 'Input IGST', 'opening': '0'},
            ]},
        ],
    },
    {
        'name': 'Fixed Assets', 'nature': AccountNature.ASSETS, 'group_type': AccountGroup.FIXED_ASSETS,
        'children': [
            {'name': 'Furniture & Fixtures', 'ledgers': []},
            {'name': 'Plant & Machinery', 'ledgers': []},
            {'name': 'Computers & Equipment', 'ledgers': []},
            {'name': 'Vehicles', 'ledgers': []},
        ],
    },
    {'name': 'Investments', 'nature': AccountNature.ASSETS, 'group_type': AccountGroup.INVESTMENTS, 'children': []},

    # ── LIABILITIES ─────────────────────────────────────────
    {
        'name': 'Current Liabilities', 'nature': AccountNature.LIABILITIES, 'group_type': AccountGroup.CURRENT_LIABILITIES,
        'children': [
            {'name': 'Sundry Creditors', 'ledgers': []},
            {'name': 'Duties & Taxes', 'ledgers': [
                {'name': 'Output CGST', 'opening': '0'}, {'name': 'Output SGST', 'opening': '0'}, {'name': 'Output IGST', 'opening': '0'},
                {'name': 'TDS Payable', 'opening': '0'}, {'name': 'TCS Payable', 'opening': '0'},
            ]},
            {'name': 'Provisions', 'ledgers': []},
            {'name': 'Statutory Liabilities', 'ledgers': [
                {'name': 'PF Payable', 'opening': '0'}, {'name': 'ESI Payable', 'opening': '0'}, {'name': 'Professional Tax Payable', 'opening': '0'},
            ]},
        ],
    },
    {
        'name': 'Long-term Liabilities', 'nature': AccountNature.LIABILITIES, 'group_type': AccountGroup.LONG_TERM_LIABILITIES,
        'children': [
            {'name': 'Secured Loans', 'ledgers': []},
            {'name': 'Unsecured Loans', 'ledgers': []},
        ],
    },

    # ── CAPITAL ─────────────────────────────────────────────
    {
        'name': 'Capital Account', 'nature': AccountNature.CAPITAL, 'group_type': AccountGroup.SHARE_CAPITAL,
        'children': [
            {'name': "Owner's Capital", 'ledgers': []},
            {'name': "Owner's Drawings", 'ledgers': []},
        ],
    },
    {
        'name': 'Reserves & Surplus', 'nature': AccountNature.CAPITAL, 'group_type': AccountGroup.RESERVES_SURPLUS,
        'children': [{'name': 'Retained Earnings', 'ledgers': []}],
    },

    # ── INCOME ──────────────────────────────────────────────
    {
        'name': 'Sales Accounts', 'nature': AccountNature.INCOME, 'group_type': AccountGroup.SALES,
        'affects_gross_profit': True,
        'children': [
            {'name': 'Sales - Domestic', 'ledgers': []},
            {'name': 'Sales - Export', 'ledgers': []},
            {'name': 'Sales Returns', 'ledgers': []},
        ],
    },
    {
        'name': 'Other Income', 'nature': AccountNature.INCOME, 'group_type': AccountGroup.OTHER_INCOME,
        'affects_gross_profit': False,
        'children': [
            {'name': 'Interest Received', 'ledgers': []},
            {'name': 'Discount Received', 'ledgers': []},
            {'name': 'Commission Received', 'ledgers': []},
        ],
    },

    # ── EXPENSES ────────────────────────────────────────────
    {
        'name': 'Purchase Accounts', 'nature': AccountNature.EXPENSES, 'group_type': AccountGroup.PURCHASE,
        'affects_gross_profit': True,
        'children': [
            {'name': 'Purchases - Domestic', 'ledgers': []},
            {'name': 'Purchase Returns', 'ledgers': []},
        ],
    },
    {
        'name': 'Direct Expenses', 'nature': AccountNature.EXPENSES, 'group_type': AccountGroup.DIRECT_EXPENSES,
        'affects_gross_profit': True,
        'children': [
            {'name': 'Freight & Carriage Inward', 'ledgers': []},
            {'name': 'Wages', 'ledgers': []},
            {'name': 'Power & Fuel', 'ledgers': []},
        ],
    },
    {
        'name': 'Indirect Expenses', 'nature': AccountNature.EXPENSES, 'group_type': AccountGroup.INDIRECT_EXPENSES,
        'affects_gross_profit': False,
        'children': [
            {'name': 'Salaries & Wages', 'ledgers': []},
            {'name': 'Rent Expense', 'ledgers': []},
            {'name': 'Electricity Expense', 'ledgers': []},
            {'name': 'Telephone & Internet', 'ledgers': []},
            {'name': 'Office Expenses', 'ledgers': []},
            {'name': 'Printing & Stationery', 'ledgers': []},
            {'name': 'Professional Fees', 'ledgers': []},
            {'name': 'Bank Charges', 'ledgers': []},
            {'name': 'Travel & Conveyance', 'ledgers': []},
            {'name': 'Repairs & Maintenance', 'ledgers': []},
            {'name': 'Insurance Expense', 'ledgers': []},
            {'name': 'Audit Fees', 'ledgers': []},
        ],
    },
    {
        'name': 'Depreciation', 'nature': AccountNature.EXPENSES, 'group_type': AccountGroup.DEPRECIATION,
        'affects_gross_profit': False,
        'children': [{'name': 'Depreciation Expense', 'ledgers': []}],
    },
]


def create_standard_chart_of_accounts(company):
    """
    Idempotently creates the standard chart of accounts for a company.
    Safe to call multiple times — uses get_or_create throughout.
    """
    sort_order = 0
    for root_def in STANDARD_GROUPS:
        sort_order += 10
        root_group, _ = LedgerGroup.objects.get_or_create(
            company=company, name=root_def['name'],
            defaults={
                'nature': root_def['nature'],
                'group_type': root_def.get('group_type', ''),
                'affects_gross_profit': root_def.get('affects_gross_profit', False),
                'is_system_group': True,
                'sort_order': sort_order,
            },
        )

        child_sort = 0
        for child_def in root_def.get('children', []):
            child_sort += 10
            child_group, _ = LedgerGroup.objects.get_or_create(
                company=company, name=child_def['name'], parent=root_group,
                defaults={
                    'nature': root_def['nature'],
                    'group_type': root_def.get('group_type', ''),
                    'affects_gross_profit': root_def.get('affects_gross_profit', False),
                    'is_system_group': True,
                    'sort_order': child_sort,
                },
            )

            for ledger_def in child_def.get('ledgers', []):
                Ledger.objects.get_or_create(
                    company=company, name=ledger_def['name'],
                    defaults={
                        'group': child_group,
                        'opening_balance': Decimal(ledger_def.get('opening', '0')),
                        'is_system_ledger': True,
                        'is_bank_account': 'bank' in ledger_def['name'].lower() and child_def['name'] == 'Bank Accounts',
                    },
                )

    return True
