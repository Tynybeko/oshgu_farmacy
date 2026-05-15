# Описание базы данных

## Таблица `pharmacy_category`

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | PK |
| name | Varchar | Название категории |

## Таблица `pharmacy_medicine` (Medicines)

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | PK |
| name | Varchar | Название |
| category_id | FK | Категория |
| manufacturer | Varchar | Производитель |
| price | Decimal | Цена |
| quantity | Integer | Количество |
| expiry_date | Date | Срок годности |
| barcode | Varchar | Штрих-код |
| description | Text | Описание |
| received_date | Date | Дата поступления |

## Таблица `pharmacy_supplier` (Suppliers)

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | PK |
| name | Varchar | Название |
| phone | Varchar | Телефон |
| address | Text | Адрес |
| debt | Decimal | Задолженность |

## Таблица `pharmacy_sale` (Sales)

| Поле | Тип | Описание |
|------|-----|----------|
| id | Integer | PK |
| cashier_id | FK → User | Кассир |
| sale_date | DateTime | Дата продажи |
| total_price | Decimal | Итоговая сумма |

## Таблица `pharmacy_saleitem`

| Поле | Тип | Описание |
|------|-----|----------|
| sale_id | FK | Продажа |
| medicine_id | FK | Медикамент |
| quantity | Integer | Количество |
| unit_price | Decimal | Цена за единицу |

## Таблица `pharmacy_employeeprofile` (Employees)

| Поле | Тип | Описание |
|------|-----|----------|
| user_id | FK → User | Учётная запись |
| fullname | Varchar | ФИО |
| position | Varchar | Должность |
| role | Varchar | Роль доступа |

## Связанные таблицы

- `pharmacy_supply` / `pharmacy_supplyitem` — поставки
- `pharmacy_auditlog` — журнал действий
