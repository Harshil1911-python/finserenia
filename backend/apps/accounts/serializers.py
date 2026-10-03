"""
SERENIA ACCOUNTING — accounts/serializers.py
=============================================
JWT Auth, User, Company, Branch serializers.
"""

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from apps.accounts.models import User, Company, Branch, FinancialYear, UserCompanyAccess, UserRole


# ── Auth Serializers ──────────────────────────────────────────
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    company_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid email or password.')
        if not user.is_active:
            raise serializers.ValidationError('Your account has been deactivated.')
        if user.locked_until and user.locked_until > timezone.now():
            raise serializers.ValidationError(f'Account locked until {user.locked_until}.')
        data['user'] = user
        return data

    def create_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        # Add custom claims
        refresh['role'] = user.role
        refresh['name'] = user.get_full_name()
        refresh['email'] = user.email
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    company_accesses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone', 'qualification', 'membership_number',
            'avatar', 'bio', 'is_active', 'is_verified',
            'date_joined', 'timezone', 'date_format', 'theme',
            'company_accesses',
        ]
        read_only_fields = ['id', 'date_joined', 'is_verified']

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_company_accesses(self, obj):
        accesses = obj.company_accesses.filter(is_active=True).select_related('company', 'branch')
        return UserCompanyAccessSerializer(accesses, many=True).data


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'role', 'phone',
            'qualification', 'membership_number',
        ]

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['current_password']):
            raise serializers.ValidationError({'current_password': 'Incorrect current password.'})
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return data


# ── Company Serializers ───────────────────────────────────────
class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class FinancialYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialYear
        fields = '__all__'
        read_only_fields = ['id', 'closed_at']


class CompanySerializer(serializers.ModelSerializer):
    branches = BranchSerializer(many=True, read_only=True)
    financial_years = FinancialYearSerializer(many=True, read_only=True)
    current_fy = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'legal_name', 'company_type',
            'gstin', 'pan', 'tan', 'cin',
            'email', 'phone', 'website',
            'address_line1', 'address_line2', 'city', 'state',
            'state_code', 'pincode', 'country',
            'logo', 'currency', 'fiscal_year_start', 'accounting_method',
            'is_active', 'created_at', 'updated_at',
            'branches', 'financial_years', 'current_fy',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_current_fy(self, obj):
        fy = obj.current_financial_year
        return FinancialYearSerializer(fy).data if fy else None


class CompanyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for company listing."""
    class Meta:
        model = Company
        fields = ['id', 'name', 'gstin', 'city', 'state', 'currency', 'is_active', 'logo']


class UserCompanyAccessSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_id = serializers.UUIDField(source='company.id', read_only=True)
    company_gstin = serializers.CharField(source='company.gstin', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True, allow_null=True)

    class Meta:
        model = UserCompanyAccess
        fields = ['id', 'company_id', 'company_name', 'company_gstin', 'role', 'branch_name', 'is_active']


class GrantAccessSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    company_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=UserRole.choices)
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    permissions = serializers.DictField(required=False, default=dict)
