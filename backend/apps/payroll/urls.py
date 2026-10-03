"""
SERENIA ACCOUNTING — payroll/urls.py
=======================================
Routes for /api/v1/payroll/
"""

from rest_framework.routers import DefaultRouter
from apps.payroll.serializers import EmployeeViewSet, SalaryStructureViewSet, PayrollRunViewSet

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet, basename='employee')
router.register(r'salary-structures', SalaryStructureViewSet, basename='salary-structure')
router.register(r'runs', PayrollRunViewSet, basename='payroll-run')

urlpatterns = router.urls
