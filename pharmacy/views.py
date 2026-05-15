import json
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .decorators import MANAGE_ROLES, SALES_ROLES, WAREHOUSE_ROLES, role_required
from .forms import (
    CategoryForm, EmployeeForm, LoginForm, MedicineForm, SupplierForm, SupplyForm,
)
from .models import (
    AuditLog, Category, EmployeeProfile, Medicine, Sale, SaleItem, Supplier, Supply,
    SupplyItem, UserRole,
)
from .utils import log_action


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        log_action(user, 'Вход в систему', ip_address=request.META.get('REMOTE_ADDR'))
        return redirect('dashboard')
    return render(request, 'pharmacy/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        log_action(request.user, 'Выход из системы')
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    today = timezone.now().date()
    month_start = today.replace(day=1)
    stats = {
        'medicines_count': Medicine.objects.count(),
        'low_stock': Medicine.objects.filter(
            quantity__lte=10
        ).count(),
        'expiring': Medicine.objects.filter(
            expiry_date__lte=today + timedelta(days=30),
            expiry_date__gte=today,
        ).count(),
        'today_sales': Sale.objects.filter(sale_date__date=today).aggregate(
            total=Sum('total_price'), count=Count('id')
        ),
        'month_revenue': Sale.objects.filter(
            sale_date__date__gte=month_start
        ).aggregate(total=Sum('total_price'))['total'] or Decimal('0'),
        'suppliers_debt': Supplier.objects.aggregate(total=Sum('debt'))['total'] or Decimal('0'),
    }
    recent_sales = Sale.objects.select_related('cashier').order_by('-sale_date')[:5]
    low_stock_items = Medicine.objects.filter(quantity__lte=10).order_by('quantity')[:5]
    return render(request, 'pharmacy/dashboard.html', {
        'stats': stats,
        'recent_sales': recent_sales,
        'low_stock_items': low_stock_items,
    })


# --- Medicines ---

@login_required
@role_required(*MANAGE_ROLES, UserRole.WAREHOUSE)
def medicine_list(request):
    qs = Medicine.objects.select_related('category')
    q = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    sort = request.GET.get('sort', 'name')

    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(barcode__icontains=q) | Q(manufacturer__icontains=q)
        )
    if category_id:
        qs = qs.filter(category_id=category_id)

    sort_map = {
        'name': 'name', 'price': 'price', 'quantity': 'quantity',
        'expiry': 'expiry_date', 'category': 'category__name',
    }
    qs = qs.order_by(sort_map.get(sort, 'name'))

    return render(request, 'pharmacy/medicines/list.html', {
        'medicines': qs,
        'categories': Category.objects.all(),
        'q': q,
        'category_id': category_id,
        'sort': sort,
    })


@login_required
@role_required(*MANAGE_ROLES, UserRole.WAREHOUSE)
def medicine_create(request):
    form = MedicineForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        med = form.save()
        log_action(request.user, 'Создание медикамента', 'Medicine', med.pk, med.name)
        messages.success(request, f'Препарат «{med.name}» добавлен.')
        return redirect('medicine_list')
    return render(request, 'pharmacy/medicines/form.html', {'form': form, 'title': 'Добавить препарат'})


@login_required
@role_required(*MANAGE_ROLES, UserRole.WAREHOUSE)
def medicine_edit(request, pk):
    med = get_object_or_404(Medicine, pk=pk)
    form = MedicineForm(request.POST or None, instance=med)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_action(request.user, 'Редактирование медикамента', 'Medicine', pk)
        messages.success(request, 'Данные препарата обновлены.')
        return redirect('medicine_list')
    return render(request, 'pharmacy/medicines/form.html', {'form': form, 'title': 'Редактировать препарат', 'medicine': med})


@login_required
@role_required(UserRole.ADMIN)
def medicine_delete(request, pk):
    med = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        name = med.name
        med.delete()
        log_action(request.user, 'Удаление медикамента', 'Medicine', pk, name)
        messages.success(request, f'Препарат «{name}» удалён.')
        return redirect('medicine_list')
    return render(request, 'pharmacy/medicines/delete.html', {'medicine': med})


@login_required
def medicine_barcode_lookup(request):
    code = request.GET.get('barcode', '').strip()
    if not code:
        return JsonResponse({'error': 'Штрих-код не указан'}, status=400)
    try:
        med = Medicine.objects.get(barcode=code)
        return JsonResponse({
            'id': med.id, 'name': med.name, 'price': str(med.price),
            'quantity': med.quantity, 'barcode': med.barcode,
        })
    except Medicine.DoesNotExist:
        return JsonResponse({'error': 'Препарат не найден'}, status=404)


# --- Categories ---

@login_required
@role_required(*MANAGE_ROLES)
def category_list(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Категория добавлена.')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'pharmacy/categories/list.html', {
        'categories': Category.objects.annotate(med_count=Count('medicines')),
        'form': form,
    })


# --- Warehouse / Supplies ---

@login_required
@role_required(*WAREHOUSE_ROLES)
def warehouse(request):
    medicines = Medicine.objects.select_related('category').order_by('name')
    filter_type = request.GET.get('filter', '')
    if filter_type == 'low':
        medicines = medicines.filter(quantity__lte=10)
    elif filter_type == 'expiring':
        today = timezone.now().date()
        medicines = medicines.filter(
            expiry_date__lte=today + timedelta(days=30),
            expiry_date__gte=today,
        )
    elif filter_type == 'expired':
        medicines = medicines.filter(expiry_date__lt=timezone.now().date())
    return render(request, 'pharmacy/warehouse/index.html', {
        'medicines': medicines,
        'filter_type': filter_type,
    })


@login_required
@role_required(*WAREHOUSE_ROLES)
def supply_list(request):
    supplies = Supply.objects.select_related('supplier', 'created_by').order_by('-supply_date')
    return render(request, 'pharmacy/supplies/list.html', {'supplies': supplies})


@login_required
@role_required(*WAREHOUSE_ROLES)
def supply_create(request):
    if request.method == 'POST':
        form = SupplyForm(request.POST)
        items_data = json.loads(request.POST.get('items', '[]'))
        if form.is_valid() and items_data:
            with transaction.atomic():
                supply = form.save(commit=False)
                supply.created_by = request.user
                supply.save()
                total = Decimal('0')
                for item in items_data:
                    med = get_object_or_404(Medicine, pk=item['medicine_id'])
                    qty = int(item['quantity'])
                    price = Decimal(str(item['unit_price']))
                    SupplyItem.objects.create(
                        supply=supply, medicine=med, quantity=qty, unit_price=price
                    )
                    med.quantity += qty
                    med.save(update_fields=['quantity'])
                    total += price * qty
                supply.total_amount = total
                supply.save()
                supplier = supply.supplier
                supplier.debt += total - supply.paid_amount
                supplier.save(update_fields=['debt'])
                log_action(request.user, 'Регистрация поставки', 'Supply', supply.pk)
            messages.success(request, 'Поставка зарегистрирована.')
            return redirect('supply_list')
        messages.error(request, 'Проверьте данные поставки.')
    else:
        form = SupplyForm()
    return render(request, 'pharmacy/supplies/form.html', {
        'form': form,
        'medicines': Medicine.objects.all(),
        'suppliers': Supplier.objects.all(),
    })


# --- Sales ---

@login_required
@role_required(*SALES_ROLES)
def sale_pos(request):
    return render(request, 'pharmacy/sales/pos.html', {
        'medicines': Medicine.objects.filter(quantity__gt=0).order_by('name'),
    })


@login_required
@role_required(*SALES_ROLES)
def sale_checkout(request):
    if request.method != 'POST':
        return redirect('sale_pos')
    try:
        cart = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Неверный формат данных'}, status=400)

    if not cart:
        return JsonResponse({'error': 'Корзина пуста'}, status=400)

    try:
        with transaction.atomic():
            sale = Sale.objects.create(cashier=request.user, total_price=0)
            total = Decimal('0')
            for item in cart:
                med = Medicine.objects.select_for_update().get(pk=item['medicine_id'])
                qty = int(item['quantity'])
                if qty > med.quantity:
                    raise ValueError(f'Недостаточно «{med.name}» на складе')
                if med.is_expired:
                    raise ValueError(f'Срок годности «{med.name}» истёк')
                subtotal = med.price * qty
                SaleItem.objects.create(
                    sale=sale, medicine=med, quantity=qty,
                    unit_price=med.price,
                )
                med.quantity -= qty
                med.save(update_fields=['quantity'])
                total += subtotal
            sale.total_price = total
            sale.save(update_fields=['total_price'])
            log_action(request.user, 'Продажа', 'Sale', sale.pk, f'Сумма: {total}')
        return JsonResponse({'sale_id': sale.pk, 'total': str(total)})
    except (Medicine.DoesNotExist, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@role_required(*SALES_ROLES)
def sale_receipt(request, pk):
    sale = get_object_or_404(Sale.objects.prefetch_related('items__medicine'), pk=pk)
    return render(request, 'pharmacy/sales/receipt.html', {'sale': sale})


@login_required
@role_required(*SALES_ROLES, UserRole.ADMIN)
def sale_history(request):
    sales = Sale.objects.select_related('cashier').prefetch_related('items__medicine')
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')
    if date_from:
        sales = sales.filter(sale_date__date__gte=date_from)
    if date_to:
        sales = sales.filter(sale_date__date__lte=date_to)
    return render(request, 'pharmacy/sales/history.html', {
        'sales': sales.order_by('-sale_date')[:100],
        'date_from': date_from,
        'date_to': date_to,
    })


# --- Suppliers ---

@login_required
@role_required(*WAREHOUSE_ROLES, UserRole.ADMIN)
def supplier_list(request):
    return render(request, 'pharmacy/suppliers/list.html', {
        'suppliers': Supplier.objects.annotate(
            supply_count=Count('supplies')
        ).order_by('name'),
    })


@login_required
@role_required(*WAREHOUSE_ROLES, UserRole.ADMIN)
def supplier_create(request):
    form = SupplierForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        s = form.save()
        log_action(request.user, 'Создание поставщика', 'Supplier', s.pk)
        messages.success(request, 'Поставщик добавлен.')
        return redirect('supplier_list')
    return render(request, 'pharmacy/suppliers/form.html', {'form': form, 'title': 'Добавить поставщика'})


@login_required
@role_required(*WAREHOUSE_ROLES, UserRole.ADMIN)
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Данные поставщика обновлены.')
        return redirect('supplier_list')
    return render(request, 'pharmacy/suppliers/form.html', {
        'form': form, 'title': 'Редактировать поставщика', 'supplier': supplier,
    })


@login_required
@role_required(*WAREHOUSE_ROLES, UserRole.ADMIN)
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    supplies = supplier.supplies.prefetch_related('items__medicine').order_by('-supply_date')
    return render(request, 'pharmacy/suppliers/detail.html', {
        'supplier': supplier, 'supplies': supplies,
    })


# --- Reports ---

@login_required
@role_required(UserRole.ADMIN, UserRole.PHARMACIST)
def reports(request):
    report_type = request.GET.get('type', 'daily')
    today = timezone.now().date()
    context = {'report_type': report_type}

    if report_type == 'daily':
        context['sales'] = Sale.objects.filter(sale_date__date=today).select_related('cashier')
        context['total'] = context['sales'].aggregate(t=Sum('total_price'))['t'] or 0
        context['title'] = f'Продажи за {today.strftime("%d.%m.%Y")}'

    elif report_type == 'monthly':
        month_start = today.replace(day=1)
        context['total'] = Sale.objects.filter(
            sale_date__date__gte=month_start
        ).aggregate(t=Sum('total_price'))['t'] or 0
        context['title'] = f'Выручка за {today.strftime("%B %Y")}'

    elif report_type == 'stock':
        context['medicines'] = Medicine.objects.select_related('category').order_by('name')
        context['title'] = 'Остатки товаров'

    elif report_type == 'expiring':
        context['medicines'] = Medicine.objects.filter(
            expiry_date__lte=today + timedelta(days=30)
        ).order_by('expiry_date')
        context['title'] = 'Препараты с истекающим сроком'

    elif report_type == 'top':
        context['items'] = SaleItem.objects.values(
            'medicine__name'
        ).annotate(
            total_qty=Sum('quantity'), total_sum=Sum(F('unit_price') * F('quantity'))
        ).order_by('-total_qty')[:10]
        context['title'] = 'Наиболее продаваемые товары'

    elif report_type == 'employees':
        context['employees'] = Sale.objects.values(
            'cashier__profile__fullname', 'cashier__username'
        ).annotate(
            sales_count=Count('id'), total_sum=Sum('total_price')
        ).order_by('-total_sum')
        context['title'] = 'Отчёт по сотрудникам'

    return render(request, 'pharmacy/reports/index.html', context)


# --- Employees ---

@login_required
@role_required(UserRole.ADMIN)
def employee_list(request):
    employees = EmployeeProfile.objects.select_related('user').order_by('fullname')
    return render(request, 'pharmacy/employees/list.html', {'employees': employees})


@login_required
@role_required(UserRole.ADMIN)
def employee_create(request):
    form = EmployeeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        profile = form.save()
        log_action(request.user, 'Создание сотрудника', 'Employee', profile.pk)
        messages.success(request, 'Сотрудник добавлен.')
        return redirect('employee_list')
    return render(request, 'pharmacy/employees/form.html', {'form': form, 'title': 'Добавить сотрудника'})


@login_required
@role_required(UserRole.ADMIN)
def employee_edit(request, pk):
    profile = get_object_or_404(EmployeeProfile, pk=pk)
    form = EmployeeForm(request.POST or None, instance=profile, user_instance=profile.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Данные сотрудника обновлены.')
        return redirect('employee_list')
    return render(request, 'pharmacy/employees/form.html', {
        'form': form, 'title': 'Редактировать сотрудника',
    })


# --- Audit log ---

@login_required
@role_required(UserRole.ADMIN)
def audit_log(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:200]
    return render(request, 'pharmacy/audit/list.html', {'logs': logs})
