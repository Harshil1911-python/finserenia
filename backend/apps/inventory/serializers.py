"""
SERENIA ACCOUNTING — inventory/serializers.py
================================================
Item, Warehouse, StockEntry, PurchaseOrder serializers and viewsets.
"""

from decimal import Decimal
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, F
from django.db import transaction
from apps.inventory.models import (
    Item, ItemCategory, Unit, Warehouse, StockEntry, PurchaseOrder, PurchaseOrderLine,
)
from apps.ledger.views import CompanyScopedViewSet


# ── Serializers ───────────────────────────────────────────────
class ItemCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory
        fields = '__all__'
        read_only_fields = ['id', 'company']


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = '__all__'
        read_only_fields = ['id', 'company']


class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    unit_symbol = serializers.CharField(source='unit.symbol', read_only=True, allow_null=True)
    current_stock = serializers.SerializerMethodField()
    stock_value = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = '__all__'
        read_only_fields = ['id', 'company', 'created_at']

    def get_current_stock(self, obj):
        result = StockEntry.objects.filter(item=obj).aggregate(
            stock_in=Sum('quantity', filter=__import__('django.db.models').db.models.Q(entry_type__in=['in', 'opening'])),
            stock_out=Sum('quantity', filter=__import__('django.db.models').db.models.Q(entry_type='out')),
        )
        stock_in = result['stock_in'] or Decimal('0')
        stock_out = result['stock_out'] or Decimal('0')
        return str(stock_in - stock_out)

    def get_stock_value(self, obj):
        current_stock = Decimal(self.get_current_stock(obj))
        return str((current_stock * obj.purchase_price).quantize(Decimal('0.01')))


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'
        read_only_fields = ['id', 'company']


class StockEntrySerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = StockEntry
        fields = '__all__'
        read_only_fields = ['id', 'company', 'amount', 'created_by', 'created_at']


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = '__all__'
        read_only_fields = ['id', 'taxable_amount', 'tax_amount', 'total_amount']


class PurchaseOrderSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineSerializer(many=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        read_only_fields = ['id', 'company', 'po_number', 'subtotal', 'tax_amount', 'total_amount', 'created_by', 'created_at']

    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        request = self.context['request']
        company_id = request.headers.get('X-Company-Id')

        po_count = PurchaseOrder.objects.filter(company_id=company_id).count()
        po_number = f"PO-{po_count + 1:05d}"

        subtotal = Decimal('0')
        tax_total = Decimal('0')

        po = PurchaseOrder.objects.create(
            company_id=company_id, po_number=po_number, created_by=request.user, **validated_data
        )

        for line_data in lines_data:
            quantity = line_data['quantity']
            rate = line_data['rate']
            discount_pct = line_data.get('discount_percent', Decimal('0'))
            gst_rate = line_data.get('gst_rate', Decimal('18'))

            gross = quantity * rate
            taxable = (gross * (1 - discount_pct / 100)).quantize(Decimal('0.01'))
            tax_amount = (taxable * gst_rate / 100).quantize(Decimal('0.01'))
            total = taxable + tax_amount

            PurchaseOrderLine.objects.create(
                purchase_order=po, taxable_amount=taxable, tax_amount=tax_amount, total_amount=total, **line_data
            )

            subtotal += taxable
            tax_total += tax_amount

        po.subtotal = subtotal
        po.tax_amount = tax_total
        po.total_amount = subtotal + tax_total
        po.save()

        return po


# ── ViewSets ──────────────────────────────────────────────────
class ItemCategoryViewSet(CompanyScopedViewSet):
    serializer_class = ItemCategorySerializer

    def get_queryset(self):
        company_id = self.get_company_id()
        return ItemCategory.objects.filter(company_id=company_id) if company_id else ItemCategory.objects.none()


class UnitViewSet(CompanyScopedViewSet):
    serializer_class = UnitSerializer

    def get_queryset(self):
        company_id = self.get_company_id()
        return Unit.objects.filter(company_id=company_id) if company_id else Unit.objects.none()


class ItemViewSet(CompanyScopedViewSet):
    serializer_class = ItemSerializer
    filterset_fields = ['category', 'item_type', 'is_active']
    search_fields = ['name', 'code', 'barcode', 'hsn_sac_code']

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = Item.objects.filter(company_id=company_id) if company_id else Item.objects.none()
        return qs.select_related('category', 'unit')

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Returns items where current stock is at or below reorder level."""
        items = self.get_queryset().filter(maintain_stock=True)
        low_stock_items = []
        for item in items:
            serialized = self.get_serializer(item).data
            if Decimal(serialized['current_stock']) <= item.reorder_level:
                low_stock_items.append(serialized)
        return Response(low_stock_items)


class WarehouseViewSet(CompanyScopedViewSet):
    serializer_class = WarehouseSerializer

    def get_queryset(self):
        company_id = self.get_company_id()
        return Warehouse.objects.filter(company_id=company_id) if company_id else Warehouse.objects.none()


class StockEntryViewSet(CompanyScopedViewSet):
    serializer_class = StockEntrySerializer
    filterset_fields = ['item', 'warehouse', 'entry_type']

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = StockEntry.objects.filter(company_id=company_id) if company_id else StockEntry.objects.none()
        return qs.select_related('item', 'warehouse').order_by('-date', '-created_at')

    def perform_create(self, serializer):
        serializer.save(company_id=self.get_company_id(), created_by=self.request.user)


class PurchaseOrderViewSet(CompanyScopedViewSet):
    serializer_class = PurchaseOrderSerializer
    filterset_fields = ['status', 'supplier', 'warehouse']

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = PurchaseOrder.objects.filter(company_id=company_id) if company_id else PurchaseOrder.objects.none()
        return qs.select_related('supplier', 'warehouse').prefetch_related('lines__item').order_by('-order_date')

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """Marks PO lines as received and creates corresponding stock entries."""
        po = self.get_object()
        received_lines = request.data.get('lines', [])  # [{line_id, quantity}]

        with transaction.atomic():
            for item in received_lines:
                try:
                    line = po.lines.get(id=item['line_id'])
                except PurchaseOrderLine.DoesNotExist:
                    continue

                qty = Decimal(str(item['quantity']))
                line.received_quantity = F('received_quantity') + qty
                line.save()
                line.refresh_from_db()

                StockEntry.objects.create(
                    company=po.company, item=line.item, warehouse=po.warehouse,
                    entry_type='in', quantity=qty, rate=line.rate,
                    reference=po.po_number, date=request.data.get('date', po.order_date),
                    created_by=request.user,
                )

            # Update PO status
            all_lines = po.lines.all()
            if all(l.received_quantity >= l.quantity for l in all_lines):
                po.status = 'received'
            elif any(l.received_quantity > 0 for l in all_lines):
                po.status = 'partial'
            po.save()

        return Response(PurchaseOrderSerializer(po).data)
