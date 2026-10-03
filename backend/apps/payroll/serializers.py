"""
SERENIA ACCOUNTING — payroll/serializers.py
==============================================
Employee, SalaryStructure, PayrollRun, Payslip serializers
and viewsets. Payroll processing is delegated to Celery (tasks.py).
"""

from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from apps.payroll.models import Employee, SalaryStructure, PayrollRun, Payslip
from apps.ledger.views import CompanyScopedViewSet


# ── Serializers ───────────────────────────────────────────────
class SalaryStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryStructure
        fields = '__all__'
        read_only_fields = ['id', 'company', 'created_at']


class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    salary_structure_name = serializers.CharField(source='salary_structure.name', read_only=True, allow_null=True)

    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ['id', 'company', 'created_at']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class PayslipSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_code = serializers.CharField(source='employee.employee_code', read_only=True)

    class Meta:
        model = Payslip
        fields = '__all__'

    def get_employee_name(self, obj):
        return f"{obj.employee.first_name} {obj.employee.last_name}"


class PayrollRunSerializer(serializers.ModelSerializer):
    payslips = PayslipSerializer(many=True, read_only=True)
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = PayrollRun
        fields = '__all__'
        read_only_fields = ['id', 'company', 'total_gross', 'total_deductions', 'total_net', 'processed_at', 'processed_by', 'journal_entry']

    def get_employee_count(self, obj):
        return obj.payslips.count()


# ── ViewSets ──────────────────────────────────────────────────
class EmployeeViewSet(CompanyScopedViewSet):
    serializer_class = EmployeeSerializer
    filterset_fields = ['department', 'employment_type', 'is_active']
    search_fields = ['first_name', 'last_name', 'employee_code', 'pan']

    def get_queryset(self):
        company_id = self.get_company_id()
        return Employee.objects.filter(company_id=company_id) if company_id else Employee.objects.none()


class SalaryStructureViewSet(CompanyScopedViewSet):
    serializer_class = SalaryStructureSerializer

    def get_queryset(self):
        company_id = self.get_company_id()
        return SalaryStructure.objects.filter(company_id=company_id) if company_id else SalaryStructure.objects.none()


class PayrollRunViewSet(CompanyScopedViewSet):
    serializer_class = PayrollRunSerializer
    filterset_fields = ['status', 'month', 'year']

    def get_queryset(self):
        company_id = self.get_company_id()
        return PayrollRun.objects.filter(company_id=company_id) if company_id else PayrollRun.objects.none()

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Triggers Celery task to calculate payslips for all active employees
        and post the consolidated payroll journal entry.
        Returns immediately with task_id; frontend polls for completion.
        """
        payroll_run = self.get_object()
        if payroll_run.status != 'draft':
            return Response({'error': 'Only draft payroll runs can be processed.'}, status=status.HTTP_400_BAD_REQUEST)

        from apps.payroll.tasks import process_payroll_run
        task = process_payroll_run.delay(str(payroll_run.id), str(request.user.id))

        payroll_run.status = 'processing'
        payroll_run.save(update_fields=['status'])

        return Response({'task_id': task.id, 'status': 'processing'})
