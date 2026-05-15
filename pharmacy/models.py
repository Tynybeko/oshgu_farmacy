from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Администратор'
    PHARMACIST = 'pharmacist', 'Фармацевт'
    CASHIER = 'cashier', 'Кассир'
    WAREHOUSE = 'warehouse', 'Складской работник'


class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    fullname = models.CharField('ФИО', max_length=200)
    position = models.CharField('Должность', max_length=100)
    role = models.CharField('Роль', max_length=20, choices=UserRole.choices, default=UserRole.CASHIER)
    phone = models.CharField('Телефон', max_length=20, blank=True)

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

    def __str__(self):
        return self.fullname


class Category(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Medicine(models.Model):
    name = models.CharField('Название', max_length=255)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Категория', related_name='medicines'
    )
    manufacturer = models.CharField('Производитель', max_length=200)
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Количество', default=0)
    expiry_date = models.DateField('Срок годности')
    barcode = models.CharField('Штрих-код', max_length=50, unique=True, blank=True, null=True)
    description = models.TextField('Описание', blank=True)
    received_date = models.DateField('Дата поступления', default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Медикамент'
        verbose_name_plural = 'Медикаменты'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        threshold = getattr(settings, 'LOW_STOCK_THRESHOLD', 10)
        return self.quantity <= threshold

    @property
    def is_expiring_soon(self):
        days = getattr(settings, 'EXPIRY_WARNING_DAYS', 30)
        return self.expiry_date <= timezone.now().date() + timezone.timedelta(days=days)

    @property
    def is_expired(self):
        return self.expiry_date < timezone.now().date()


class Supplier(models.Model):
    name = models.CharField('Название', max_length=200)
    phone = models.CharField('Телефон', max_length=30)
    address = models.TextField('Адрес')
    debt = models.DecimalField('Задолженность', max_digits=12, decimal_places=2, default=0)
    email = models.EmailField('Email', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'
        ordering = ['name']

    def __str__(self):
        return self.name


class Supply(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='supplies', verbose_name='Поставщик')
    supply_date = models.DateTimeField('Дата поставки', default=timezone.now)
    total_amount = models.DecimalField('Сумма', max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField('Оплачено', max_digits=12, decimal_places=2, default=0)
    notes = models.TextField('Примечания', blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Оформил')

    class Meta:
        verbose_name = 'Поставка'
        verbose_name_plural = 'Поставки'
        ordering = ['-supply_date']

    def __str__(self):
        return f'Поставка #{self.pk} от {self.supplier}'

    @property
    def debt_amount(self):
        return self.total_amount - self.paid_amount

    def recalculate_total(self):
        total = self.items.aggregate(s=Sum('subtotal'))['s'] or Decimal('0')
        self.total_amount = total
        self.save(update_fields=['total_amount'])


class SupplyItem(models.Model):
    supply = models.ForeignKey(Supply, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, verbose_name='Медикамент')
    quantity = models.PositiveIntegerField('Количество')
    unit_price = models.DecimalField('Цена за ед.', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Позиция поставки'
        verbose_name_plural = 'Позиции поставки'

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class Sale(models.Model):
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='Кассир')
    sale_date = models.DateTimeField('Дата продажи', default=timezone.now)
    total_price = models.DecimalField('Итого', max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Продажа'
        verbose_name_plural = 'Продажи'
        ordering = ['-sale_date']

    def __str__(self):
        return f'Чек #{self.pk}'

    def recalculate_total(self):
        total = self.items.aggregate(s=Sum('subtotal'))['s'] or Decimal('0')
        self.total_price = total
        self.save(update_fields=['total_price'])


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, verbose_name='Медикамент')
    quantity = models.PositiveIntegerField('Количество')
    unit_price = models.DecimalField('Цена', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Позиция продажи'
        verbose_name_plural = 'Позиции продажи'

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField('Действие', max_length=50)
    model_name = models.CharField('Модель', max_length=50, blank=True)
    object_id = models.CharField('ID объекта', max_length=50, blank=True)
    details = models.TextField('Детали', blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Журнал действий'
        verbose_name_plural = 'Журнал действий'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.action} — {self.timestamp}'
