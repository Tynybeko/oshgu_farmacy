# Руководство по установке

## Требования

- **Python** 3.10 или новее
- **pip** (обычно идёт с Python)
- **PostgreSQL** 14+ (рекомендуется для продакшена) **или** SQLite (для учёбы и быстрого старта)
- **Git** (по желанию)

Проверка версий:

```bash
python3 --version
pip --version
psql --version   # только если используете PostgreSQL
```

---

## 1. Подготовка проекта

Скопируйте проект в каталог, например `apteka`, и перейдите в него:

```bash
cd apteka
```

Создайте и активируйте виртуальное окружение:

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

Установите зависимости:

```bash
pip install -r requirements.txt
```

---

## 2. Настройка файла `.env`

Скопируйте пример конфигурации:

```bash
cp .env.example .env
```

Откройте `.env` в редакторе и задайте параметры.

### Вариант А — SQLite (проще всего, без установки PostgreSQL)

Подходит для разработки, диплома и локального тестирования. Файл базы создаётся автоматически в корне проекта.

```env
SECRET_KEY=замените-на-случайную-длинную-строку
DEBUG=True
DB_ENGINE=django.db.backends.sqlite3
```

Остальные переменные `DB_*` при SQLite **не нужны**.

### Вариант Б — PostgreSQL (как в ТЗ)

```env
SECRET_KEY=замените-на-случайную-длинную-строку
DEBUG=True
DB_ENGINE=django.db.backends.postgresql
DB_NAME=apteka_db
DB_USER=postgres
DB_PASSWORD=ваш_пароль
DB_HOST=localhost
DB_PORT=5432
```

| Переменная   | Описание                          |
|--------------|-----------------------------------|
| `SECRET_KEY` | Секретный ключ Django (обязателен)|
| `DEBUG`      | `True` — разработка, `False` — продакшен |
| `DB_ENGINE`  | Движок БД                         |
| `DB_NAME`    | Имя базы данных                   |
| `DB_USER`    | Пользователь PostgreSQL           |
| `DB_PASSWORD`| Пароль пользователя               |
| `DB_HOST`    | Обычно `localhost`                |
| `DB_PORT`    | Обычно `5432`                     |

Сгенерировать `SECRET_KEY` (в терминале с активированным venv):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 3. Установка PostgreSQL (если выбран вариант Б)

### macOS (Homebrew)

```bash
brew install postgresql@16
brew services start postgresql@16
```

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Windows

1. Скачайте установщик с [postgresql.org](https://www.postgresql.org/download/windows/).
2. Установите PostgreSQL, запомните пароль пользователя `postgres`.
3. pgAdmin или командная строка `psql` будут доступны после установки.

---

## 4. Создание базы данных PostgreSQL

### Способ 1 — через `psql` (рекомендуется)

Войдите в консоль PostgreSQL:

```bash
# macOS / Linux (пользователь postgres в системе)
sudo -u postgres psql

# или, если PostgreSQL установлен через Homebrew на Mac:
psql postgres
```

Выполните SQL-команды (подставьте свой пароль вместо `your_password`):

```sql
-- Создать базу данных
CREATE DATABASE apteka_db
    WITH ENCODING 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE template0;

-- Создать отдельного пользователя (необязательно, можно использовать postgres)
CREATE USER apteka_user WITH PASSWORD 'your_password';

-- Выдать права на базу
GRANT ALL PRIVILEGES ON DATABASE apteka_db TO apteka_user;
```

**Важно:** команду `\c` и `GRANT` для схемы `public` выполняйте **по одной строке** (после каждой нажимайте Enter).  
Не вставляйте блок целиком — иначе `psql` склеит строки и выдаст ошибку  
`invalid integer value "ON" for connection option "port"`.

Сначала переключитесь на базу (отдельной строкой):

```sql
\c apteka_db
```

Должно появиться: `You are now connected to database "apteka_db"`.  
Затем по очереди:

```sql
GRANT ALL ON SCHEMA public TO apteka_user;
GRANT CREATE ON SCHEMA public TO apteka_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO apteka_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO apteka_user;
```

Выйти: `\q`

#### Способ 1б — скрипт из проекта (удобнее)

Из каталога `apteka`, **вне** интерактивного `psql`:

```bash
psql postgres -f scripts/grant_apteka_user.sql
```

Если база и пользователь ещё не созданы — сначала выполните в `psql` только `CREATE DATABASE` и `CREATE USER`, затем скрипт выше.

В `.env` укажите:

```env
DB_NAME=apteka_db
DB_USER=apteka_user
DB_PASSWORD=your_password
```

### Способ 2 — одной командой в терминале

```bash
createdb apteka_db
```

Если команда не найдена, используйте полный путь или способ 1.

### Способ 3 — через pgAdmin

1. Откройте **pgAdmin** → подключитесь к серверу.
2. ПКМ по **Databases** → **Create** → **Database**.
3. Имя: `apteka_db`, кодировка: `UTF8` → **Save**.

---

## 5. Проверка подключения к БД

С активированным `venv` и настроенным `.env`:

```bash
python manage.py check --database default
```

Если PostgreSQL недоступен, вы увидите ошибку подключения — проверьте, что сервер запущен:

```bash
# macOS (Homebrew)
brew services list

# Linux
sudo systemctl status postgresql
```

Проверка входа в PostgreSQL с вашими данными из `.env`:

```bash
psql -h localhost -p 5432 -U apteka_user -d apteka_db
```

---

## 6. Миграции и начальные данные

Применить структуру таблиц:

```bash
python manage.py migrate
```

Загрузить демонстрационные данные (медикаменты, поставщики, пользователи):

```bash
python manage.py load_demo_data
```

Опционально — суперпользователь для панели `/admin/`:

```bash
python manage.py createsuperuser
```

---

## 7. Запуск сервера

```bash
python manage.py runserver
```

Откройте в браузере: **http://127.0.0.1:8000/**

Для доступа с других устройств в локальной сети:

```bash
python manage.py runserver 0.0.0.0:8000
```

### Демо-учётные записи (после `load_demo_data`)

| Логин       | Пароль    | Роль                |
|-------------|-----------|---------------------|
| admin       | admin123  | Администратор       |
| pharmacist  | pharm123  | Фармацевт           |
| cashier     | cash123   | Кассир              |
| warehouse   | wh123     | Складской работник  |

---

## 8. Резервное копирование

**PostgreSQL:**

```bash
pg_dump -h localhost -U apteka_user apteka_db > backup_$(date +%Y%m%d).sql
```

Восстановление:

```bash
psql -h localhost -U apteka_user -d apteka_db < backup_20260515.sql
```

**SQLite:**

```bash
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3
```

---

## 9. Частые ошибки

| Ошибка | Решение |
|--------|---------|
| `connection refused` | Запустите PostgreSQL (`brew services start` / `systemctl start`) |
| `database "apteka_db" does not exist` | Выполните `CREATE DATABASE apteka_db` (раздел 4) |
| `password authentication failed` | Проверьте `DB_USER` и `DB_PASSWORD` в `.env` |
| `permission denied for schema public` | Выполните `scripts/grant_apteka_user.sql` или `GRANT` из раздела 4 (PostgreSQL 15+) |
| `invalid integer value "ON" for connection option "port"` | В `psql` не вставляйте `\c` и `GRANT` одним блоком — сначала только `\c apteka_db`, затем `GRANT` по строкам |
| `No module named 'psycopg2'` | `pip install psycopg2-binary` |
| Порт 8000 занят | `python manage.py runserver 8080` |

---

## 10. Продакшен (кратко)

- Установите `DEBUG=False` и уникальный `SECRET_KEY` в `.env`.
- Задайте `ALLOWED_HOSTS=your-domain.com` в `.env` (через запятую).
- Соберите статику: `python manage.py collectstatic`.
- Запускайте через **Gunicorn** + **Nginx**.
- Настройте ежедневный `pg_dump` в cron.
