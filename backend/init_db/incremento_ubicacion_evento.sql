-- Ejecutar en la base de datos activos_db que ya creaste.
-- Agrega la tabla ubicacion_evento y la columna opcional en movimiento,
-- sin afectar ninguna de las 19 tablas ya existentes.

BEGIN;

CREATE TABLE IF NOT EXISTS ubicacion_evento (
    id                      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    area_responsable_id     BIGINT NOT NULL,
    nombre_lugar            VARCHAR(150) NOT NULL,
    tipo                    VARCHAR(20) NOT NULL DEFAULT 'externo',
    ciudad                  VARCHAR(100),
    provincia               VARCHAR(100),
    departamento            VARCHAR(100),
    pais                    VARCHAR(100) NOT NULL DEFAULT 'Bolivia',
    fecha_inicio            DATE,
    fecha_fin               DATE,
    observacion             TEXT,
    estado                  VARCHAR(20) NOT NULL DEFAULT 'activo',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by              BIGINT,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by              BIGINT,
    CONSTRAINT ck_ubicacion_evento_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico')),
    CONSTRAINT ck_ubicacion_evento_tipo CHECK (tipo IN ('interno', 'externo', 'evento')),
    CONSTRAINT ck_ubicacion_evento_fechas CHECK (fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin >= fecha_inicio),
    CONSTRAINT fk_ubicacion_evento_area
        FOREIGN KEY (area_responsable_id) REFERENCES area(id),
    CONSTRAINT fk_ubicacion_evento_created_by
        FOREIGN KEY (created_by) REFERENCES usuario(id),
    CONSTRAINT fk_ubicacion_evento_updated_by
        FOREIGN KEY (updated_by) REFERENCES usuario(id)
);

ALTER TABLE movimiento
    ADD COLUMN IF NOT EXISTS ubicacion_evento_id BIGINT
    REFERENCES ubicacion_evento(id);

CREATE INDEX IF NOT EXISTS idx_movimiento_ubicacion_evento ON movimiento(ubicacion_evento_id);
CREATE INDEX IF NOT EXISTS idx_ubicacion_evento_area ON ubicacion_evento(area_responsable_id);

COMMIT;
