"""
SERENIA ACCOUNTING — inventory/models.py
==========================================
Items, Warehouses, Stock Movements, Purchase Orders,
Sales Orders, Batch Tracking, Inventory Valuation.
"""

import uuid
from decimal import Decimal
from django.db import models
from apps.accounts.models import Company, User


class ItemCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='item_categories')
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_categories')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'item_categories'
        unique_together = ['company', 'name']

    def __str__(self):
        return self.name


class Unit(models.Model):
    """Unit of measurement: kg, pcs, litre, box, etc."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='units')
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'units'
        unique_together = ['company', 'symbol']

    def __str__(self):
        return self.symbol


class Item(models.Model):
    """Product or service item in inventory."""
    ITEM_TYPES = [('goods', 'Goods'), ('service', 'Service'), ('composite', 'Composite')]
    VALUATION_METHODS = [('fifo', 'FIFO'), ('lifo', 'LIFO'), ('weighted_avg', 'Weighted Average'), ('specific', 'Specific Identification')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(ItemCategory, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=50, blank=True, db_index=True)
    barcode = models.CharField(max_length=100, blank=True)
    item_type = models.CharField(max_length=15, choices=ITEM_TYPES, default='goods')
    description = models.TextField(blank=True)

    # Units
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    alternate_unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='alternate_items')
    unit_conversion_factor = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('1'))

    # Pricing
    purchase_price = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    selling_price = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    mrp = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    # GST
    hsn_sac_code = models.CharField(max_length=10, blank=True)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18'))
    is_nil_rated = models.BooleanField(default=False)
    is_exempt = models.BooleanField(default=False)

    # Inventory settings
    valuation_method = models.CharField(max_length=15, choices=VALUATION_METHODS, default='weighted_avg')
    maintain_stock = models.BooleanField(default=True)
    reorder_level = models.DecimalField(max_digits=15, decimal_places=3, default=Decimal('0'))
    reorder_quantity = models.DecimalField(max_digits=15, decimal_places=3, default=Decimal('0'))
    is_batch_tracked = models.BooleanField(default=False)
    is_serial_tracked = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'items'
        unique_together = ['company', 'code']
        indexes = [models.Index(fields=['company', 'name']), models.Index(fields=['hsn_sac_code'])]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Warehouse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='warehouses')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'warehouses'
        unique_together = ['company', 'code']

    def __str__(self):
        return f"{self.name} ({self.company.name})"


class StockEntry(models.Model):
    """Records stock movement in or out of a warehouse."""
    ENTRY_TYPES = [
        ('in', 'Stock In'), ('out', 'Stock Out'), ('transfer', 'Transfer'),
        ('adjustment', 'Adjustment'), ('opening', 'Opening Stock')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='stock_entries')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='stock_entries')
    destination_warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_transfers')
    entry_type = models.CharField(max_length=15, choices=ENTRY_TYPES)
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    rate = models.DecimalField(max_digits=20, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    batch_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    date = models.DateField(db_index=True)
    journal_entry = models.ForeignKey('ledger.JournalEntry', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_entries'
        indexes = [models.Index(fields=['company', 'item', 'date']), models.Index(fields=['warehouse', 'item'])]

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.rate
        super().save(*args, **kwargs)


class PurchaseOrder(models.Model):
    STATUS = [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('partial', 'Partially Received'), ('received', 'Fully Received'), ('cancelled', 'Cancelled')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='purchase_orders')
    po_number = models.CharField(max_length=50)
    supplier = models.ForeignKey('ledger.Ledger', on_delete=models.PROTECT, related_name='purchase_orders')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    order_date = models.DateField()
    expected_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS, default='draft')
    subtotal = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    tax_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'purchase_orders'
        unique_together = ['company', 'po_number']


class PurchaseOrderLine(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=15, decimal_places=3)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True)
    rate = models.DecimalField(max_digits=20, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    taxable_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('18'))
    tax_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    received_quantity = models.DecimalField(max_digits=15, decimal_places=3, default=Decimal('0'))

    class Meta:
        db_table = 'purchase_order_lines'
