# Информационная система аптеки «Здоровый Мир»

Веб-приложение для автоматизации учёта медикаментов, продаж, складских операций, поставок и отчётности аптеки (г. Ош).

## Технологии

- **Python** / **Django**
- **PostgreSQL** (или SQLite для разработки)
- **HTML**, **CSS**, **Bootstrap 5**, **JavaScript**

## Быстрый старт

```bash
cd apteka
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py load_demo_data
python manage.py runserver
```

Откройте http://127.0.0.1:8000/

### Демо-учётные записи

| Логин       | Пароль    | Роль                |
|-------------|-----------|---------------------|
| admin       | admin123  | Администратор       |
| pharmacist  | pharm123  | Фармацевт           |
| cashier     | cash123   | Кассир              |
| warehouse   | wh123     | Складской работник  |

## PostgreSQL

В файле `.env` укажите:

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=apteka_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

Создайте базу: `createdb apteka_db`

## Функции системы

- Авторизация с разграничением прав (4 роли)
- Учёт медикаментов (CRUD, поиск, категории, штрих-код)
- Складской учёт (остатки, поставки, контроль сроков, уведомления о малом остатке)
- Касса (продажи, чек, списание со склада, поиск по штрих-коду)
- Поставщики (задолженность, история поставок)
- Отчёты (ежедневные, месячные, остатки, срок годности, топ продаж, сотрудники)
- Журнал действий пользователей

## Документация

- [Руководство по установке](docs/INSTALL.md)
- [Руководство пользователя](docs/USER_GUIDE.md)
- [Инструкция администратора](docs/ADMIN_GUIDE.md)
- [Описание базы данных](docs/DATABASE.md)

## Резервное копирование

```bash
# PostgreSQL
pg_dump apteka_db > backup.sql

# SQLite
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3
```
# oshgu_farmacy
