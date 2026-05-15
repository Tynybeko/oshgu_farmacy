from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/add/', views.medicine_create, name='medicine_create'),
    path('medicines/<int:pk>/edit/', views.medicine_edit, name='medicine_edit'),
    path('medicines/<int:pk>/delete/', views.medicine_delete, name='medicine_delete'),
    path('api/barcode/', views.medicine_barcode_lookup, name='barcode_lookup'),

    path('categories/', views.category_list, name='category_list'),

    path('warehouse/', views.warehouse, name='warehouse'),
    path('supplies/', views.supply_list, name='supply_list'),
    path('supplies/add/', views.supply_create, name='supply_create'),

    path('sales/', views.sale_pos, name='sale_pos'),
    path('sales/checkout/', views.sale_checkout, name='sale_checkout'),
    path('sales/<int:pk>/receipt/', views.sale_receipt, name='sale_receipt'),
    path('sales/history/', views.sale_history, name='sale_history'),

    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),

    path('reports/', views.reports, name='reports'),

    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),

    path('audit/', views.audit_log, name='audit_log'),
]
