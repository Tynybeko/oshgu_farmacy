-- Запуск от суперпользователя (postgres):
--   psql postgres -f scripts/grant_apteka_user.sql
--
-- Или в psql: \i scripts/grant_apteka_user.sql

-- Права на базу (если БД и пользователь уже созданы)
GRANT ALL PRIVILEGES ON DATABASE apteka_db TO apteka_user;

\c apteka_db

-- PostgreSQL 15+: без этого migrate выдаёт "permission denied for schema public"
GRANT ALL ON SCHEMA public TO apteka_user;
GRANT CREATE ON SCHEMA public TO apteka_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO apteka_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO apteka_user;

-- Уже существующие объекты (если есть)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO apteka_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO apteka_user;
