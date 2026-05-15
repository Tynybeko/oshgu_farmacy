from django.contrib import admin
from .models import (
    AuditLog, Category, EmployeeProfile, Medicine, Sale, SaleItem,
    Supplier, Supply, SupplyItem,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'manufacturer', 'price', 'quantity', 'expiry_date', 'barcode')
    list_filter = ('category', 'manufacturer')
    search_fields = ('name', 'barcode', 'manufacturer')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'debt')


class SupplyItemInline(admin.TabularInline):
    model = SupplyItem
    extra = 1


@admin.register(Supply)
class SupplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'supply_date', 'total_amount', 'paid_amount')
    inlines = [SupplyItemInline]


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ('medicine', 'quantity', 'unit_price')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'cashier', 'sale_date', 'total_price')
    inlines = [SaleItemInline]


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'position', 'role', 'user')
    list_filter = ('role',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name')
    list_filter = ('action', 'model_name')
    readonly_fields = ('user', 'action', 'model_name', 'object_id', 'details', 'ip_address', 'timestamp')
