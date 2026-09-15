-- ============================================================
-- SISTEMA WEB DE GESTIÓN Y TRAZABILIDAD DE ACTIVOS OPERATIVOS
-- Diseño inicial de base de datos - PostgreSQL
-- 19 tablas
-- ============================================================

BEGIN;

-- ------------------------------------------------------------
-- 1. SEGURIDAD
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS rol (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre          VARCHAR(50) NOT NULL UNIQUE,
    descripcion     VARCHAR(255),
    estado          VARCHAR(20) NOT NULL DEFAULT 'activo',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_rol_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico'))
);

CREATE TABLE IF NOT EXISTS permiso (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL UNIQUE,
    codigo          VARCHAR(100) NOT NULL UNIQUE,
    descripcion     VARCHAR(255),
    estado          VARCHAR(20) NOT NULL DEFAULT 'activo',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_permiso_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico'))
);

CREATE TABLE IF NOT EXISTS rol_permiso (
    rol_id          BIGINT NOT NULL,
    permiso_id      BIGINT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (rol_id, permiso_id),
    CONSTRAINT fk_rol_permiso_rol
        FOREIGN KEY (rol_id) REFERENCES rol(id),
    CONSTRAINT fk_rol_permiso_permiso
        FOREIGN KEY (permiso_id) REFERENCES permiso(id)
);

CREATE TABLE IF NOT EXISTS area (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre          VARCHAR(120) NOT NULL UNIQUE,
    codigo          VARCHAR(30) UNIQUE,
    descripcion     VARCHAR(255),
    estado          VARCHAR(20) NOT NULL DEFAULT 'activo',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by      BIGINT,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by      BIGINT,
    CONSTRAINT ck_area_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico'))
);

CREATE TABLE IF NOT EXISTS usuario (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rol_id          BIGINT NOT NULL,
    area_id         BIGINT,
    nombre          VARCHAR(120) NOT NULL,
    email           VARCHAR(180) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    estado          VARCHAR(20) NOT NULL DEFAULT 'activo',
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by      BIGINT,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by      BIGINT,
    CONSTRAINT ck_usuario_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico')),
    CONSTRAINT fk_usuario_rol
        FOREIGN KEY (rol_id) REFERENCES rol(id),
    CONSTRAINT fk_usuario_area
        FOREIGN KEY (area_id) REFERENCES area(id),
    CONSTRAINT fk_usuario_created_by
        FOREIGN KEY (created_by) REFERENCES usuario(id),
    CONSTRAINT fk_usuario_updated_by
        FOREIGN KEY (updated_by) REFERENCES usuario(id)
);

ALTER TABLE area
    ADD CONSTRAINT fk_area_created_by FOREIGN KEY (created_by) REFERENCES usuario(id),
    ADD CONSTRAINT fk_area_updated_by FOREIGN KEY (updated_by) REFERENCES usuario(id);

-- ------------------------------------------------------------
-- 3. ACTIVOS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS categoria_activo (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre          VARCHAR(120) NOT NULL UNIQUE,
    codigo          VARCHAR(30) UNIQUE,
    descripcion     VARCHAR(255),
    estado          VARCHAR(20) NOT NULL DEFAULT 'activo',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by      BIGINT,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by      BIGINT,
    CONSTRAINT ck_categoria_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico')),
    CONSTRAINT fk_categoria_created_by
        FOREIGN KEY (created_by) REFERENCES usuario(id),
    CONSTRAINT fk_categoria_updated_by
        FOREIGN KEY (updated_by) REFERENCES usuario(id)
);

CREATE TABLE IF NOT EXISTS activo (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    categoria_id        BIGINT NOT NULL,
    codigo              VARCHAR(50) NOT NULL UNIQUE,
    nombre              VARCHAR(150) NOT NULL,
    descripcion         TEXT,
    unidad_medida       VARCHAR(30) NOT NULL DEFAULT 'unidad',
    estado               VARCHAR(20) NOT NULL DEFAULT 'activo',
    fecha_alta           DATE,
    fecha_baja           DATE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by           BIGINT,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by           BIGINT,
    CONSTRAINT ck_activo_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico')),
    CONSTRAINT ck_activo_fechas CHECK (fecha_baja IS NULL OR fecha_alta IS NULL OR fecha_baja >= fecha_alta),
    CONSTRAINT fk_activo_categoria
        FOREIGN KEY (categoria_id) REFERENCES categoria_activo(id),
    CONSTRAINT fk_activo_created_by
        FOREIGN KEY (created_by) REFERENCES usuario(id),
    CONSTRAINT fk_activo_updated_by
        FOREIGN KEY (updated_by) REFERENCES usuario(id)
);

CREATE TABLE IF NOT EXISTS existencia (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    activo_id            BIGINT NOT NULL,
    area_id              BIGINT NOT NULL,
    cantidad             NUMERIC(14,2) NOT NULL DEFAULT 0,
    stock_minimo         NUMERIC(14,2),
    stock_maximo         NUMERIC(14,2),
    estado               VARCHAR(20) NOT NULL DEFAULT 'activo',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by           BIGINT,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by           BIGINT,
    CONSTRAINT uq_existencia_activo_area UNIQUE (activo_id, area_id),
    CONSTRAINT ck_existencia_cantidad CHECK (cantidad >= 0),
    CONSTRAINT ck_existencia_stock_min CHECK (stock_minimo IS NULL OR stock_minimo >= 0),
    CONSTRAINT ck_existencia_stock_max CHECK (stock_maximo IS NULL OR stock_maximo >= 0),
    CONSTRAINT ck_existencia_stock_range CHECK (
        stock_minimo IS NULL OR stock_maximo IS NULL OR stock_maximo >= stock_minimo
    ),
    CONSTRAINT ck_existencia_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico')),
    CONSTRAINT fk_existencia_activo
        FOREIGN KEY (activo_id) REFERENCES activo(id),
    CONSTRAINT fk_existencia_area
        FOREIGN KEY (area_id) REFERENCES area(id),
    CONSTRAINT fk_existencia_created_by
        FOREIGN KEY (created_by) REFERENCES usuario(id),
    CONSTRAINT fk_existencia_updated_by
        FOREIGN KEY (updated_by) REFERENCES usuario(id)
);

-- ------------------------------------------------------------
-- 4. MOVIMIENTOS / KARDEX
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tipo_movimiento (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre          VARCHAR(50) NOT NULL UNIQUE,
    codigo          VARCHAR(30) NOT NULL UNIQUE,
    descripcion     VARCHAR(255),
    afecta_stock    BOOLEAN NOT NULL DEFAULT TRUE,
    estado          VARCHAR(20) NOT NULL DEFAULT 'activo',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_tipo_mov_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico'))
);

CREATE TABLE IF NOT EXISTS movimiento (
    id                       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    activo_id                 BIGINT NOT NULL,
    tipo_movimiento_id        BIGINT NOT NULL,
    area_origen_id            BIGINT,
    area_destino_id           BIGINT,
    encargado_id              BIGINT NOT NULL,
    usuario_registrador_id    BIGINT NOT NULL,
    movimiento_origen_id      BIGINT,
    documento_legacy_id       BIGINT,
    cantidad                  NUMERIC(14,2) NOT NULL,
    saldo_resultante          NUMERIC(14,2),
    fecha_hora                TIMESTAMPTZ NOT NULL,
    motivo                    VARCHAR(255),
    observacion               TEXT,
    estado                    VARCHAR(20) NOT NULL DEFAULT 'activo',
    created_at                TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by                BIGINT,
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by                BIGINT,
    CONSTRAINT ck_movimiento_cantidad CHECK (cantidad > 0),
    CONSTRAINT ck_movimiento_saldo CHECK (saldo_resultante IS NULL OR saldo_resultante >= 0),
    CONSTRAINT ck_movimiento_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico')),
    CONSTRAINT fk_movimiento_activo
        FOREIGN KEY (activo_id) REFERENCES activo(id),
    CONSTRAINT fk_movimiento_tipo
        FOREIGN KEY (tipo_movimiento_id) REFERENCES tipo_movimiento(id),
    CONSTRAINT fk_movimiento_area_origen
        FOREIGN KEY (area_origen_id) REFERENCES area(id),
    CONSTRAINT fk_movimiento_area_destino
        FOREIGN KEY (area_destino_id) REFERENCES area(id),
    CONSTRAINT fk_movimiento_encargado
        FOREIGN KEY (encargado_id) REFERENCES usuario(id),
    CONSTRAINT fk_movimiento_registrador
        FOREIGN KEY (usuario_registrador_id) REFERENCES usuario(id),
    CONSTRAINT fk_movimiento_origen
        FOREIGN KEY (movimiento_origen_id) REFERENCES movimiento(id),
    -- Se agrega la FK hacia documento_legacy después de crear esa tabla.
    CONSTRAINT fk_movimiento_created_by
        FOREIGN KEY (created_by) REFERENCES usuario(id),
    CONSTRAINT fk_movimiento_updated_by
        FOREIGN KEY (updated_by) REFERENCES usuario(id),
    CONSTRAINT ck_movimiento_transferencia_areas CHECK (
        area_origen_id IS NULL OR area_destino_id IS NULL OR area_origen_id <> area_destino_id
    )
);

-- ------------------------------------------------------------
-- 5. LEGACY DATA / OCR / HITL
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS documento_legacy (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo_documento    VARCHAR(100) NOT NULL UNIQUE,
    periodo_documental  VARCHAR(50),
    fecha_documento     DATE,
    ruta_original       TEXT,
    checksum_original   VARCHAR(128),
    estado               VARCHAR(20) NOT NULL DEFAULT 'historico',
    observacion         TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by           BIGINT,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by           BIGINT,
    CONSTRAINT ck_documento_legacy_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico')),
    CONSTRAINT fk_documento_legacy_created_by
        FOREIGN KEY (created_by) REFERENCES usuario(id),
    CONSTRAINT fk_documento_legacy_updated_by
        FOREIGN KEY (updated_by) REFERENCES usuario(id)
);

CREATE TABLE IF NOT EXISTS extraccion_legacy (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    documento_legacy_id  BIGINT NOT NULL,
    motor                VARCHAR(100) NOT NULL,
    modelo_version       VARCHAR(100),
    texto_extraido       TEXT,
    confianza_global     NUMERIC(6,5),
    procesado_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado               VARCHAR(20) NOT NULL DEFAULT 'activo',
    observacion          TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by           BIGINT,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by           BIGINT,
    CONSTRAINT ck_extraccion_confianza CHECK (confianza_global IS NULL OR (confianza_global >= 0 AND confianza_global <= 1)),
    CONSTRAINT ck_extraccion_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico')),
    CONSTRAINT fk_extraccion_documento
        FOREIGN KEY (documento_legacy_id) REFERENCES documento_legacy(id),
    CONSTRAINT fk_extraccion_created_by
        FOREIGN KEY (created_by) REFERENCES usuario(id),
    CONSTRAINT fk_extraccion_updated_by
        FOREIGN KEY (updated_by) REFERENCES usuario(id)
);

CREATE TABLE IF NOT EXISTS validacion_legacy (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    extraccion_id       BIGINT NOT NULL,
    validador_id        BIGINT NOT NULL,
    resultado            VARCHAR(20) NOT NULL,
    fecha_validacion     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observacion          TEXT,
    correccion_aplicada  BOOLEAN NOT NULL DEFAULT FALSE,
    estado               VARCHAR(20) NOT NULL DEFAULT 'activo',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by           BIGINT,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by           BIGINT,
    CONSTRAINT ck_validacion_resultado CHECK (resultado IN ('pendiente', 'validado', 'corregido', 'rechazado')),
    CONSTRAINT ck_validacion_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico')),
    CONSTRAINT fk_validacion_extraccion
        FOREIGN KEY (extraccion_id) REFERENCES extraccion_legacy(id),
    CONSTRAINT fk_validacion_validador
        FOREIGN KEY (validador_id) REFERENCES usuario(id),
    CONSTRAINT fk_validacion_created_by
        FOREIGN KEY (created_by) REFERENCES usuario(id),
    CONSTRAINT fk_validacion_updated_by
        FOREIGN KEY (updated_by) REFERENCES usuario(id)
);

ALTER TABLE movimiento
    ADD CONSTRAINT fk_movimiento_documento_legacy
    FOREIGN KEY (documento_legacy_id) REFERENCES documento_legacy(id);

-- ------------------------------------------------------------
-- 6. ANALÍTICA
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS resultado_regla (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    movimiento_id       BIGINT NOT NULL,
    codigo_regla        VARCHAR(80) NOT NULL,
    resultado            VARCHAR(20) NOT NULL,
    detalle              TEXT,
    evaluado_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado               VARCHAR(20) NOT NULL DEFAULT 'activo',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by           BIGINT,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by           BIGINT,
    CONSTRAINT ck_regla_resultado CHECK (resultado IN ('cumple', 'advertencia', 'viola')),
    CONSTRAINT ck_regla_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico')),
    CONSTRAINT fk_regla_movimiento
        FOREIGN KEY (movimiento_id) REFERENCES movimiento(id),
    CONSTRAINT fk_regla_created_by
        FOREIGN KEY (created_by) REFERENCES usuario(id),
    CONSTRAINT fk_regla_updated_by
        FOREIGN KEY (updated_by) REFERENCES usuario(id)
);

CREATE TABLE IF NOT EXISTS evaluacion_anomalia (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    movimiento_id       BIGINT NOT NULL,
    modelo_version      VARCHAR(100) NOT NULL,
    ciclo_evaluacion    VARCHAR(50),
    anomaly_score       NUMERIC(12,8) NOT NULL,
    es_anomalia         BOOLEAN NOT NULL,
    umbral_aplicado     NUMERIC(12,8),
    evaluado_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado               VARCHAR(20) NOT NULL DEFAULT 'activo',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by           BIGINT,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by           BIGINT,
    CONSTRAINT ck_anomalia_estado CHECK (estado IN ('activo', 'baja', 'anulado', 'historico')),
    CONSTRAINT fk_anomalia_movimiento
        FOREIGN KEY (movimiento_id) REFERENCES movimiento(id),
    CONSTRAINT fk_anomalia_created_by
        FOREIGN KEY (created_by) REFERENCES usuario(id),
    CONSTRAINT fk_anomalia_updated_by
        FOREIGN KEY (updated_by) REFERENCES usuario(id)
);

-- ------------------------------------------------------------
-- 7. AUDITORÍA
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS alerta (
    id                      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    movimiento_id           BIGINT NOT NULL,
    resultado_regla_id      BIGINT,
    evaluacion_anomalia_id  BIGINT,
    tipo_alerta              VARCHAR(50) NOT NULL,
    prioridad                VARCHAR(20) NOT NULL DEFAULT 'media',
    estado                  VARCHAR(30) NOT NULL DEFAULT 'generada',
    titulo                  VARCHAR(255) NOT NULL,
    descripcion             TEXT,
    generada_at             TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revisada_at             TIMESTAMPTZ,
    revisada_por            BIGINT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by              BIGINT,
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by              BIGINT,
    CONSTRAINT ck_alerta_prioridad CHECK (prioridad IN ('baja', 'media', 'alta', 'critica')),
    CONSTRAINT ck_alerta_estado CHECK (estado IN ('generada', 'revisada', 'descartada', 'convertida_en_caso')),
    CONSTRAINT ck_alerta_fuente CHECK (resultado_regla_id IS NOT NULL OR evaluacion_anomalia_id IS NOT NULL),
    CONSTRAINT fk_alerta_movimiento
        FOREIGN KEY (movimiento_id) REFERENCES movimiento(id),
    CONSTRAINT fk_alerta_regla
        FOREIGN KEY (resultado_regla_id) REFERENCES resultado_regla(id),
    CONSTRAINT fk_alerta_anomalia
        FOREIGN KEY (evaluacion_anomalia_id) REFERENCES evaluacion_anomalia(id),
    CONSTRAINT fk_alerta_revisada_por
        FOREIGN KEY (revisada_por) REFERENCES usuario(id),
    CONSTRAINT fk_alerta_created_by
        FOREIGN KEY (created_by) REFERENCES usuario(id),
    CONSTRAINT fk_alerta_updated_by
        FOREIGN KEY (updated_by) REFERENCES usuario(id)
);

CREATE TABLE IF NOT EXISTS caso_auditoria (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    alerta_id           BIGINT NOT NULL,
    auditor_id          BIGINT,
    estado_caso         VARCHAR(30) NOT NULL DEFAULT 'nuevo',
    prioridad           VARCHAR(20),
    fecha_apertura      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre        TIMESTAMPTZ,
    conclusion          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by          BIGINT,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by          BIGINT,
    CONSTRAINT ck_caso_estado CHECK (estado_caso IN ('nuevo', 'en_revision', 'resuelto', 'descartado')),
    CONSTRAINT ck_caso_prioridad CHECK (prioridad IS NULL OR prioridad IN ('baja', 'media', 'alta', 'critica')),
    CONSTRAINT ck_caso_fechas CHECK (fecha_cierre IS NULL OR fecha_cierre >= fecha_apertura),
    CONSTRAINT fk_caso_alerta
        FOREIGN KEY (alerta_id) REFERENCES alerta(id),
    CONSTRAINT fk_caso_auditor
        FOREIGN KEY (auditor_id) REFERENCES usuario(id),
    CONSTRAINT fk_caso_created_by
        FOREIGN KEY (created_by) REFERENCES usuario(id),
    CONSTRAINT fk_caso_updated_by
        FOREIGN KEY (updated_by) REFERENCES usuario(id)
);

CREATE TABLE IF NOT EXISTS revision_caso (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    caso_id             BIGINT NOT NULL,
    auditor_id          BIGINT NOT NULL,
    estado_anterior     VARCHAR(30),
    estado_nuevo        VARCHAR(30) NOT NULL,
    comentario          TEXT,
    evidencia_ref       TEXT,
    revisado_at         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by          BIGINT,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by          BIGINT,
    CONSTRAINT ck_revision_estado_nuevo CHECK (estado_nuevo IN ('nuevo', 'en_revision', 'resuelto', 'descartado')),
    CONSTRAINT fk_revision_caso
        FOREIGN KEY (caso_id) REFERENCES caso_auditoria(id),
    CONSTRAINT fk_revision_auditor
        FOREIGN KEY (auditor_id) REFERENCES usuario(id),
    CONSTRAINT fk_revision_created_by
        FOREIGN KEY (created_by) REFERENCES usuario(id),
    CONSTRAINT fk_revision_updated_by
        FOREIGN KEY (updated_by) REFERENCES usuario(id)
);

CREATE TABLE IF NOT EXISTS auditoria_sistema (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id          BIGINT,
    accion              VARCHAR(50) NOT NULL,
    recurso             VARCHAR(100) NOT NULL,
    recurso_id          BIGINT,
    resultado            VARCHAR(20) NOT NULL,
    fecha_hora           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_origen            INET,
    detalle              JSONB,
    CONSTRAINT ck_auditoria_resultado CHECK (resultado IN ('exito', 'rechazo', 'error')),
    CONSTRAINT fk_auditoria_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);

-- ------------------------------------------------------------
-- ÍNDICES PRINCIPALES
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_usuario_area ON usuario(area_id);
CREATE INDEX IF NOT EXISTS idx_activo_categoria ON activo(categoria_id);
CREATE INDEX IF NOT EXISTS idx_existencia_area ON existencia(area_id);
CREATE INDEX IF NOT EXISTS idx_existencia_activo ON existencia(activo_id);
CREATE INDEX IF NOT EXISTS idx_movimiento_activo_fecha ON movimiento(activo_id, fecha_hora);
CREATE INDEX IF NOT EXISTS idx_movimiento_origen ON movimiento(area_origen_id);
CREATE INDEX IF NOT EXISTS idx_movimiento_destino ON movimiento(area_destino_id);
CREATE INDEX IF NOT EXISTS idx_movimiento_encargado ON movimiento(encargado_id);
CREATE INDEX IF NOT EXISTS idx_movimiento_registrador ON movimiento(usuario_registrador_id);
CREATE INDEX IF NOT EXISTS idx_documento_legacy_periodo ON documento_legacy(periodo_documental);
CREATE INDEX IF NOT EXISTS idx_extraccion_documento ON extraccion_legacy(documento_legacy_id);
CREATE INDEX IF NOT EXISTS idx_resultado_regla_movimiento ON resultado_regla(movimiento_id);
CREATE INDEX IF NOT EXISTS idx_anomalia_movimiento_fecha ON evaluacion_anomalia(movimiento_id, evaluado_at);
CREATE INDEX IF NOT EXISTS idx_alerta_movimiento ON alerta(movimiento_id);
CREATE INDEX IF NOT EXISTS idx_alerta_estado_prioridad ON alerta(estado, prioridad);
CREATE INDEX IF NOT EXISTS idx_caso_estado ON caso_auditoria(estado_caso);
CREATE INDEX IF NOT EXISTS idx_revision_caso ON revision_caso(caso_id, revisado_at);
CREATE INDEX IF NOT EXISTS idx_auditoria_usuario_fecha ON auditoria_sistema(usuario_id, fecha_hora);
CREATE INDEX IF NOT EXISTS idx_auditoria_recurso ON auditoria_sistema(recurso, recurso_id);

-- ------------------------------------------------------------
-- DATOS INICIALES DE CATÁLOGO
-- ------------------------------------------------------------

INSERT INTO rol (nombre, descripcion)
VALUES
    ('Administrador', 'Administración general del sistema'),
    ('Operador', 'Registro y consulta de activos y movimientos'),
    ('Auditor', 'Revisión de trazabilidad, alertas, casos y reportes')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO permiso (nombre, codigo, descripcion)
VALUES
    ('Gestionar usuarios', 'USUARIOS_GESTIONAR', 'Crear, modificar y consultar usuarios'),
    ('Gestionar roles', 'ROLES_GESTIONAR', 'Gestionar roles y asignaciones'),
    ('Gestionar activos', 'ACTIVOS_GESTIONAR', 'Gestionar activos, categorías y existencias'),
    ('Gestionar movimientos', 'MOVIMIENTOS_GESTIONAR', 'Registrar y consultar movimientos'),
    ('Consultar trazabilidad', 'TRAZABILIDAD_CONSULTAR', 'Consultar historial y recorridos'),
    ('Revisar alertas', 'ALERTAS_REVISAR', 'Consultar y revisar alertas'),
    ('Gestionar casos', 'CASOS_GESTIONAR', 'Gestionar casos de auditoría'),
    ('Consultar auditoría', 'AUDITORIA_CONSULTAR', 'Consultar auditoría del sistema'),
    ('Consultar reportes', 'REPORTES_CONSULTAR', 'Consultar reportes')
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO tipo_movimiento (nombre, codigo, descripcion)
VALUES
    ('Entrada', 'ENTRADA', 'Ingreso de un activo o cantidad al inventario'),
    ('Salida', 'SALIDA', 'Salida de un activo o cantidad del inventario'),
    ('Transferencia', 'TRANSFERENCIA', 'Traslado de un activo o cantidad entre áreas')
ON CONFLICT (codigo) DO NOTHING;

COMMIT;

-- ============================================================
-- FIN DEL ESQUEMA INICIAL
-- ============================================================

 - -   K a r d e x   C o n t i n u o 
 C R E A T E   T A B L E   I F   N O T   E X I S T S   l o t e s _ c a r g a   (   i d   S E R I A L   P R I M A R Y   K E Y ,   f e c h a _ e s c a n e o   T I M E S T A M P T Z   D E F A U L T   C U R R E N T _ T I M E S T A M P ,   t o t a l _ i m a g e n e s   I N T   N O T   N U L L   ) ; 
 
 C R E A T E   T A B L E   I F   N O T   E X I S T S   m o v i m i e n t o s _ k a r d e x   (   i d   S E R I A L   P R I M A R Y   K E Y ,   a r t i c u l o _ i d   B I G I N T   N O T   N U L L   R E F E R E N C E S   a c t i v o ( i d )   O N   D E L E T E   C A S C A D E ,   l o t e _ i d   I N T   R E F E R E N C E S   l o t e s _ c a r g a ( i d )   O N   D E L E T E   S E T   N U L L ,   f e c h a _ m o v i m i e n t o   D A T E   N O T   N U L L ,   d e t a l l e   T E X T   N O T   N U L L ,   r e f e r e n c i a   V A R C H A R ( 1 0 0 ) ,   a r e a   V A R C H A R ( 1 0 0 ) ,   i n g r e s o s   I N T   D E F A U L T   N U L L ,   s a l i d a s   I N T   D E F A U L T   N U L L ,   s a l d o _ r e g i s t r a d o   I N T   N O T   N U L L ,   r u t a _ i m a g e n _ r e s p a l d o   V A R C H A R ( 5 1 2 ) ,   n u m e r o _ p a g i n a   I N T ,   o r d e n _ f i l a   I N T ,   t i e n e _ e r r o r _ s a l d o   B O O L E A N   N O T   N U L L   D E F A U L T   F A L S E ,   s a l d o _ c a l c u l a d o   I N T   N U L L ,   o b s e r v a c i o n e s   T E X T   N U L L   ) ;  
 