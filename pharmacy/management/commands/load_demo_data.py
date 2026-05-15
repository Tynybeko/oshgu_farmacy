from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from pharmacy.models import (
    Category, EmployeeProfile, Medicine, Supplier, UserRole,
)


class Command(BaseCommand):
    help = 'Загрузка демонстрационных данных для аптеки «Здоровый Мир»'

    def handle(self, *args, **options):
        if Medicine.objects.exists():
            self.stdout.write('Данные уже загружены.')
            return

        categories = {
            'Обезболивающие': Category.objects.create(name='Обезболивающие'),
            'Антибиотики': Category.objects.create(name='Антибиотики'),
            'Витамины': Category.objects.create(name='Витамины'),
            'Сердечно-сосудистые': Category.objects.create(name='Сердечно-сосудистые'),
        }

        Supplier.objects.bulk_create([
            Supplier(name='ООО «ФармСнаб»', phone='+996 555 111 222', address='г. Ош, ул. Ленина 15'),
            Supplier(name='ИП Ахмедов', phone='+996 700 333 444', address='г. Ош, ул. Курманжан 8'),
        ])

        today = timezone.now().date()
        medicines_data = [
            ('Парацетамол 500мг', 'Обезболивающие', 'Байер', '45.00', 120, '4601234567890'),
            ('Ибупрофен 200мг', 'Обезболивающие', 'Тева', '65.00', 80, '4601234567891'),
            ('Амоксициллин 500мг', 'Антибиотики', 'Сандоз', '180.00', 45, '4601234567892'),
            ('Витамин C 1000мг', 'Витамины', 'Эвалар', '320.00', 60, '4601234567893'),
            ('Аспирин Кардио', 'Сердечно-сосудистые', 'Байер', '95.00', 8, '4601234567894'),
            ('Нурофен', 'Обезболивающие', 'Reckitt', '210.00', 35, '4601234567895'),
        ]
        for name, cat, mfr, price, qty, barcode in medicines_data:
            Medicine.objects.create(
                name=name,
                category=categories[cat],
                manufacturer=mfr,
                price=Decimal(price),
                quantity=qty,
                expiry_date=today + timedelta(days=180 if qty > 10 else 25),
                barcode=barcode,
                description=f'Препарат {name}',
                received_date=today - timedelta(days=30),
            )

        users = [
            ('admin', 'admin123', 'Администратор Системы', 'Директор', UserRole.ADMIN),
            ('pharmacist', 'pharm123', 'Иванова Мария Петровна', 'Фармацевт', UserRole.PHARMACIST),
            ('cashier', 'cash123', 'Сыдыков Айбек', 'Кассир', UserRole.CASHIER),
            ('warehouse', 'wh123', 'Ким Алексей', 'Складской работник', UserRole.WAREHOUSE),
        ]
        for login, pwd, fullname, position, role in users:
            user, created = User.objects.get_or_create(username=login)
            if created:
                user.set_password(pwd)
                user.save()
            EmployeeProfile.objects.update_or_create(
                user=user,
                defaults={'fullname': fullname, 'position': position, 'role': role},
            )

        self.stdout.write(self.style.SUCCESS('Демо-данные успешно загружены.'))
        self.stdout.write('Логины: admin, pharmacist, cashier, warehouse (пароли: admin123, pharm123, cash123, wh123)')
