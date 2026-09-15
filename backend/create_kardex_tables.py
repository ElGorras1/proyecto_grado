import psycopg2

DDL = """
CREATE TABLE IF NOT EXISTS lotes_carga (
    id SERIAL PRIMARY KEY,
    fecha_escaneo TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    total_imagenes INT NOT NULL
);

CREATE TABLE IF NOT EXISTS movimientos_kardex (
    id SERIAL PRIMARY KEY,
    articulo_id BIGINT NOT NULL REFERENCES activo(id) ON DELETE CASCADE,
    lote_id INT REFERENCES lotes_carga(id) ON DELETE SET NULL,
    fecha_movimiento DATE NOT NULL,
    detalle TEXT NOT NULL,
    referencia VARCHAR(100),
    area VARCHAR(100),
    ingresos INT DEFAULT NULL,
    salidas INT DEFAULT NULL,
    saldo_registrado INT NOT NULL,
    ruta_imagen_respaldo VARCHAR(512),
    numero_pagina INT,
    orden_fila INT,
    
    -- Campos de auditoria solicitados
    tiene_error_saldo BOOLEAN NOT NULL DEFAULT FALSE,
    saldo_calculado INT NULL,
    observaciones TEXT NULL
);
"""

conn = psycopg2.connect("postgresql://postgres:user@localhost:5432/activos_db")
conn.autocommit = True
cur = conn.cursor()
cur.execute(DDL)
print("Tablas de Kardex creadas exitosamente.")
