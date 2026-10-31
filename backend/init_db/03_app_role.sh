#!/bin/sh
# Solo se ejecuta al inicializar el volumen nuevo, después del baseline vacío.
set -eu
: "${APP_DB_PASSWORD:?Falta la contraseña privada de la aplicación}"
psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --set=ON_ERROR_STOP=1 \
     --set=app_password="$APP_DB_PASSWORD" <<'SQL'
CREATE ROLE activos_app LOGIN PASSWORD :'app_password';
GRANT CONNECT ON DATABASE activos_db TO activos_app;
GRANT USAGE ON SCHEMA public TO activos_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO activos_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO activos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO activos_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO activos_app;
REVOKE INSERT, UPDATE, DELETE ON public.alembic_version FROM activos_app;
SQL
