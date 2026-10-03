"""
SERENIA ACCOUNTING — reports/urls.py
=======================================
Routes for /api/v1/reports/
"""

from django.urls import path
from apps.reports.views import (
    TrialBalanceView, ProfitAndLossView, BalanceSheetView, LedgerReportView,
)

urlpatterns = [
    path('trial-balance/', TrialBalanceView.as_view(), name='report-trial-balance'),
    path('profit-and-loss/', ProfitAndLossView.as_view(), name='report-profit-and-loss'),
    path('balance-sheet/', BalanceSheetView.as_view(), name='report-balance-sheet'),
    path('ledger/<uuid:ledger_id>/', LedgerReportView.as_view(), name='report-ledger'),
]
