FROM python:3.12-slim-bookworm AS production

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    POSTGRES_BIN=/usr/lib/postgresql/18/bin

# Cliente de la misma versión mayor que la base de producción, para respaldo/restauración.
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && install -d /usr/share/postgresql-common/pgdg \
    && curl --fail --silent --show-error https://www.postgresql.org/media/keys/ACCC4CF8.asc \
       -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
    && echo 'deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main' > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update && apt-get install -y --no-install-recommends postgresql-client-18 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/runtime.lock /tmp/runtime.lock
RUN pip install --no-cache-dir --require-hashes -r /tmp/runtime.lock
RUN groupadd --gid 10001 activos && useradd --uid 10001 --gid activos --no-create-home activos
COPY --chown=activos:activos . .
RUN mkdir -p storage/kardex_images .analytics .analytics_operativa backups logs \
    && chown -R activos:activos storage .analytics .analytics_operativa backups logs
USER activos

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# El compose existente mantiene su modo de desarrollo; producción selecciona el target anterior.
FROM production AS development
USER root
COPY requirements/development.lock /tmp/development.lock
RUN pip install --no-cache-dir --require-hashes -r /tmp/development.lock
USER activos
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
