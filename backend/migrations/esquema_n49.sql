-- Baseline PostgreSQL vacío, congelado en revisión n49e15fa0d73.
--
-- PostgreSQL database dump
--


-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: activo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.activo (
    id bigint NOT NULL,
    categoria_id bigint NOT NULL,
    codigo character varying(50) NOT NULL,
    nombre character varying(150) NOT NULL,
    descripcion text,
    unidad_medida character varying(30) DEFAULT 'unidad'::character varying NOT NULL,
    estado character varying(20) DEFAULT 'activo'::character varying NOT NULL,
    fecha_alta date,
    fecha_baja date,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    CONSTRAINT ck_activo_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying])::text[]))),
    CONSTRAINT ck_activo_fechas CHECK (((fecha_baja IS NULL) OR (fecha_alta IS NULL) OR (fecha_baja >= fecha_alta)))
);


--
-- Name: activo_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.activo ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.activo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: alerta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alerta (
    id bigint NOT NULL,
    movimiento_id bigint NOT NULL,
    resultado_regla_id bigint,
    evaluacion_anomalia_id bigint,
    tipo_alerta character varying(50) NOT NULL,
    prioridad character varying(20) DEFAULT 'media'::character varying NOT NULL,
    estado character varying(30) DEFAULT 'generada'::character varying NOT NULL,
    titulo character varying(255) NOT NULL,
    descripcion text,
    generada_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    revisada_at timestamp with time zone,
    revisada_por bigint,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    CONSTRAINT ck_alerta_estado CHECK (((estado)::text = ANY ((ARRAY['generada'::character varying, 'revisada'::character varying, 'descartada'::character varying, 'convertida_en_caso'::character varying])::text[]))),
    CONSTRAINT ck_alerta_fuente CHECK (((resultado_regla_id IS NOT NULL) OR (evaluacion_anomalia_id IS NOT NULL))),
    CONSTRAINT ck_alerta_prioridad CHECK (((prioridad)::text = ANY ((ARRAY['baja'::character varying, 'media'::character varying, 'alta'::character varying, 'critica'::character varying])::text[])))
);


--
-- Name: alerta_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.alerta ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.alerta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: analitica_modelos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analitica_modelos (
    id character varying(36) NOT NULL,
    estado character varying(24) NOT NULL,
    plaza integer,
    usuario_id integer,
    creado_en timestamp with time zone NOT NULL,
    terminado_en timestamp with time zone,
    configuracion json NOT NULL,
    corte json NOT NULL,
    huella character varying(64) NOT NULL,
    metricas json,
    umbral double precision,
    artefacto_sha256 character varying(64),
    error text
);


--
-- Name: analitica_operativa_modelos; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analitica_operativa_modelos (
    id character varying(36) NOT NULL,
    estado character varying(24) NOT NULL,
    plaza integer,
    activo integer,
    usuario_id integer NOT NULL,
    creado_en timestamp with time zone NOT NULL,
    configuracion json NOT NULL,
    corte json NOT NULL,
    huella character varying(64) NOT NULL,
    metricas json,
    umbral double precision,
    artefacto_sha256 character varying(64),
    error text
);


--
-- Name: analitica_operativa_resultados; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analitica_operativa_resultados (
    id integer NOT NULL,
    modelo_id character varying(36) NOT NULL,
    recurso character varying(70) NOT NULL,
    articulo_id integer NOT NULL,
    movimiento_id integer,
    transferencia_id integer,
    custodia_id integer,
    evento_custodia_id integer,
    creado_en timestamp with time zone NOT NULL,
    snapshot json NOT NULL,
    contexto json NOT NULL,
    score double precision NOT NULL,
    alerta boolean NOT NULL,
    CONSTRAINT ck_resultado_operativo_origen CHECK (((((
CASE
    WHEN (movimiento_id IS NULL) THEN 0
    ELSE 1
END +
CASE
    WHEN (transferencia_id IS NULL) THEN 0
    ELSE 1
END) +
CASE
    WHEN (custodia_id IS NULL) THEN 0
    ELSE 1
END) +
CASE
    WHEN (evento_custodia_id IS NULL) THEN 0
    ELSE 1
END) = 1))
);


--
-- Name: analitica_operativa_resultados_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.analitica_operativa_resultados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: analitica_operativa_resultados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.analitica_operativa_resultados_id_seq OWNED BY public.analitica_operativa_resultados.id;


--
-- Name: analitica_resultados; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analitica_resultados (
    id integer NOT NULL,
    modelo_id character varying(36) NOT NULL,
    movimiento_id integer NOT NULL,
    gestion integer NOT NULL,
    articulo_id integer NOT NULL,
    nodo character varying(100),
    score double precision NOT NULL,
    alerta boolean NOT NULL,
    particion character varying(20) NOT NULL,
    muestra_control boolean NOT NULL,
    snapshot json NOT NULL,
    contexto json NOT NULL,
    estado_revision character varying(30) NOT NULL,
    revision_numero integer NOT NULL,
    etiqueta character varying(30)
);


--
-- Name: analitica_resultados_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.analitica_resultados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: analitica_resultados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.analitica_resultados_id_seq OWNED BY public.analitica_resultados.id;


--
-- Name: analitica_revisiones; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.analitica_revisiones (
    id integer NOT NULL,
    resultado_id integer NOT NULL,
    usuario_id integer NOT NULL,
    creado_en timestamp with time zone NOT NULL,
    anterior character varying(30) NOT NULL,
    estado character varying(30) NOT NULL,
    motivo text NOT NULL,
    etiqueta character varying(30)
);


--
-- Name: analitica_revisiones_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.analitica_revisiones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: analitica_revisiones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.analitica_revisiones_id_seq OWNED BY public.analitica_revisiones.id;


--
-- Name: apertura_inventario; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.apertura_inventario (
    articulo_id integer NOT NULL,
    cantidad_inicial integer NOT NULL,
    cantidad_actual integer NOT NULL,
    ultimo_moderno_id integer NOT NULL,
    aprobado_por integer NOT NULL,
    aprobado_en timestamp with time zone NOT NULL,
    referencia_documento character varying(255) NOT NULL,
    justificacion text NOT NULL,
    origen character varying(30) DEFAULT 'CONTEO_FISICO'::character varying NOT NULL,
    movimiento_historico_id integer,
    lote_historico_id integer,
    cantidad_sin_ubicacion integer DEFAULT 0 NOT NULL,
    cantidad_custodia_externa integer DEFAULT 0 NOT NULL,
    CONSTRAINT ck_apertura_actual CHECK (((cantidad_actual >= 0) AND (cantidad_actual <= 2147483647))),
    CONSTRAINT ck_apertura_custodia_externa CHECK (((cantidad_custodia_externa >= 0) AND (cantidad_custodia_externa <= 2147483647))),
    CONSTRAINT ck_apertura_inicial CHECK ((cantidad_inicial >= 0)),
    CONSTRAINT ck_apertura_origen CHECK (((origen)::text = ANY ((ARRAY['CONTEO_FISICO'::character varying, 'KARDEX_HISTORICO'::character varying])::text[]))),
    CONSTRAINT ck_apertura_sin_ubicacion CHECK ((cantidad_sin_ubicacion >= 0))
);


--
-- Name: area; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.area (
    id bigint NOT NULL,
    nombre character varying(120) NOT NULL,
    codigo character varying(30),
    descripcion character varying(255),
    estado character varying(20) DEFAULT 'activo'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    CONSTRAINT ck_area_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying])::text[])))
);


--
-- Name: area_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.area ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.area_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auditoria_sistema; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auditoria_sistema (
    id bigint NOT NULL,
    usuario_id bigint,
    accion character varying(50) NOT NULL,
    recurso character varying(100) NOT NULL,
    recurso_id bigint,
    resultado character varying(20) NOT NULL,
    fecha_hora timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    ip_origen inet,
    detalle jsonb,
    CONSTRAINT ck_auditoria_resultado CHECK (((resultado)::text = ANY ((ARRAY['exito'::character varying, 'rechazo'::character varying, 'error'::character varying])::text[])))
);


--
-- Name: auditoria_sistema_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.auditoria_sistema ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.auditoria_sistema_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: caso_auditoria; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.caso_auditoria (
    id bigint NOT NULL,
    alerta_id bigint NOT NULL,
    auditor_id bigint,
    estado_caso character varying(30) DEFAULT 'nuevo'::character varying NOT NULL,
    prioridad character varying(20),
    fecha_apertura timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    fecha_cierre timestamp with time zone,
    conclusion text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    CONSTRAINT ck_caso_estado CHECK (((estado_caso)::text = ANY ((ARRAY['nuevo'::character varying, 'en_revision'::character varying, 'resuelto'::character varying, 'descartado'::character varying])::text[]))),
    CONSTRAINT ck_caso_fechas CHECK (((fecha_cierre IS NULL) OR (fecha_cierre >= fecha_apertura))),
    CONSTRAINT ck_caso_prioridad CHECK (((prioridad IS NULL) OR ((prioridad)::text = ANY ((ARRAY['baja'::character varying, 'media'::character varying, 'alta'::character varying, 'critica'::character varying])::text[]))))
);


--
-- Name: caso_auditoria_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.caso_auditoria ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.caso_auditoria_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: caso_control; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.caso_control (
    id integer NOT NULL,
    articulo_id integer NOT NULL,
    movimiento_id integer,
    transferencia_id integer,
    custodia_id integer,
    evento_custodia_id integer,
    estado character varying(24) NOT NULL,
    prioridad character varying(10) NOT NULL,
    asignado_id integer,
    asignado_nombre character varying(120),
    revision_numero integer NOT NULL,
    creado_en timestamp with time zone NOT NULL,
    actualizado_en timestamp with time zone,
    conclusion character varying(30),
    snapshot json NOT NULL,
    codigos json NOT NULL,
    CONSTRAINT ck_caso_control_estado CHECK (((estado)::text = ANY ((ARRAY['PENDIENTE'::character varying, 'EN_REVISION'::character varying, 'SEGUIMIENTO'::character varying, 'JUSTIFICADO'::character varying, 'CERRADO'::character varying])::text[]))),
    CONSTRAINT ck_caso_control_origen CHECK (((((
CASE
    WHEN (movimiento_id IS NULL) THEN 0
    ELSE 1
END +
CASE
    WHEN (transferencia_id IS NULL) THEN 0
    ELSE 1
END) +
CASE
    WHEN (custodia_id IS NULL) THEN 0
    ELSE 1
END) +
CASE
    WHEN (evento_custodia_id IS NULL) THEN 0
    ELSE 1
END) = 1)),
    CONSTRAINT ck_caso_control_prioridad CHECK (((prioridad)::text = ANY ((ARRAY['ALTA'::character varying, 'MEDIA'::character varying, 'BAJA'::character varying])::text[])))
);


--
-- Name: caso_control_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.caso_control_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: caso_control_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.caso_control_id_seq OWNED BY public.caso_control.id;


--
-- Name: catalogo_areas; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.catalogo_areas (
    id integer NOT NULL,
    nombre_oficial character varying(100) NOT NULL,
    abreviatura character varying(30),
    descripcion text,
    tipo character varying(30) DEFAULT 'departamento'::character varying,
    activa boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: catalogo_areas_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.catalogo_areas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: catalogo_areas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.catalogo_areas_id_seq OWNED BY public.catalogo_areas.id;


--
-- Name: catalogo_ferias; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.catalogo_ferias (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    ciudad character varying(100),
    activa boolean DEFAULT true
);


--
-- Name: catalogo_ferias_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.catalogo_ferias_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: catalogo_ferias_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.catalogo_ferias_id_seq OWNED BY public.catalogo_ferias.id;


--
-- Name: categoria_activo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categoria_activo (
    id bigint NOT NULL,
    nombre character varying(120) NOT NULL,
    codigo character varying(30),
    descripcion character varying(255),
    estado character varying(20) DEFAULT 'activo'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    CONSTRAINT ck_categoria_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying])::text[])))
);


--
-- Name: categoria_activo_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.categoria_activo ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.categoria_activo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: cierre_anual; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cierre_anual (
    id integer NOT NULL,
    solicitud_id character varying(36) NOT NULL,
    solicitud_huella character varying(64) NOT NULL,
    gestion integer NOT NULL,
    gestion_activa integer,
    version integer NOT NULL,
    estado character varying(20) NOT NULL,
    snapshot json NOT NULL,
    huella character varying(64) NOT NULL,
    usuario_id integer NOT NULL,
    creado_en timestamp with time zone NOT NULL,
    documento character varying(200) NOT NULL,
    motivo text NOT NULL,
    reabierto_por integer,
    reabierto_en timestamp with time zone,
    motivo_reapertura text,
    CONSTRAINT ck_cierre_anual_estado CHECK (((estado)::text = ANY ((ARRAY['CERRADO'::character varying, 'REABIERTO'::character varying])::text[])))
);


--
-- Name: cierre_anual_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.cierre_anual_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: cierre_anual_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.cierre_anual_id_seq OWNED BY public.cierre_anual.id;


--
-- Name: cobertura_articulo; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cobertura_articulo (
    articulo_id integer NOT NULL,
    estado character varying(24) NOT NULL,
    referencia character varying(255) NOT NULL,
    observacion text NOT NULL,
    ultimo_lote_revisado_id integer,
    revisado_por integer NOT NULL,
    revisado_en timestamp with time zone NOT NULL,
    CONSTRAINT ck_cobertura_articulo_estado CHECK (((estado)::text = ANY ((ARRAY['SIN_CONFIRMAR'::character varying, 'PARCIAL'::character varying, 'CIERRE_CONFIRMADO'::character varying])::text[])))
);


--
-- Name: conciliacion_inicial; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conciliacion_inicial (
    articulo_id integer NOT NULL,
    cantidad_base integer NOT NULL,
    cantidad_fisica integer NOT NULL,
    diferencia integer NOT NULL,
    fecha_conteo date NOT NULL,
    distribucion_anterior json NOT NULL,
    areas json NOT NULL,
    referencia_documento character varying(255) NOT NULL,
    justificacion text NOT NULL,
    encargado_id integer NOT NULL,
    registrado_por integer NOT NULL,
    registrado_en timestamp with time zone NOT NULL,
    origen_base character varying(30) NOT NULL,
    movimiento_historico_id integer,
    ajuste_movimiento_id integer,
    CONSTRAINT ck_conciliacion_base CHECK ((cantidad_base >= 0)),
    CONSTRAINT ck_conciliacion_diferencia CHECK ((diferencia = (cantidad_fisica - cantidad_base))),
    CONSTRAINT ck_conciliacion_fisica CHECK ((cantidad_fisica >= 0))
);


--
-- Name: custodia_externa; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.custodia_externa (
    id integer NOT NULL,
    solicitud_id character varying(36) NOT NULL,
    solicitud_huella character varying(64) NOT NULL,
    articulo_id integer NOT NULL,
    tipo character varying(20) NOT NULL,
    area_origen_id integer NOT NULL,
    receptor_nombre character varying(200) NOT NULL,
    receptor_tipo character varying(24) NOT NULL,
    ubicacion_externa character varying(200) NOT NULL,
    ciudad character varying(100),
    cantidad_entregada integer NOT NULL,
    cantidad_fuera integer NOT NULL,
    cantidad_vendida integer DEFAULT 0 NOT NULL,
    cantidad_devuelta integer DEFAULT 0 NOT NULL,
    total_institucional_entrega integer NOT NULL,
    encargado_id integer NOT NULL,
    registrado_por integer NOT NULL,
    ocurrido_en timestamp with time zone NOT NULL,
    registrado_en timestamp with time zone NOT NULL,
    referencia_documento character varying(200) NOT NULL,
    observaciones text NOT NULL,
    alertas_control json,
    justificacion_alertas text,
    CONSTRAINT ck_custodia_balance CHECK ((cantidad_entregada = ((cantidad_fuera + cantidad_vendida) + cantidad_devuelta))),
    CONSTRAINT ck_custodia_cantidades CHECK (((cantidad_entregada > 0) AND (cantidad_fuera >= 0) AND (cantidad_vendida >= 0) AND (cantidad_devuelta >= 0))),
    CONSTRAINT ck_custodia_receptor_tipo CHECK (((receptor_tipo)::text = ANY ((ARRAY['PERSONA'::character varying, 'INSTITUCION'::character varying])::text[]))),
    CONSTRAINT ck_custodia_tipo CHECK (((tipo)::text = ANY ((ARRAY['FERIA'::character varying, 'CONSIGNACION'::character varying])::text[])))
);


--
-- Name: custodia_externa_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.custodia_externa_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: custodia_externa_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.custodia_externa_id_seq OWNED BY public.custodia_externa.id;


--
-- Name: documento_legacy; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documento_legacy (
    id bigint NOT NULL,
    codigo_documento character varying(100) NOT NULL,
    periodo_documental character varying(50),
    fecha_documento date,
    ruta_original text,
    checksum_original character varying(128),
    estado character varying(20) DEFAULT 'historico'::character varying NOT NULL,
    observacion text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    nombre_archivo character varying(255),
    ruta_almacenamiento text,
    fecha_carga timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_documento_legacy_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying, 'pendiente'::character varying, 'procesado'::character varying, 'error'::character varying, 'subido'::character varying])::text[])))
);


--
-- Name: documento_legacy_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.documento_legacy ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.documento_legacy_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: evaluacion_anomalia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.evaluacion_anomalia (
    id bigint NOT NULL,
    movimiento_id bigint NOT NULL,
    modelo_version character varying(100) NOT NULL,
    ciclo_evaluacion character varying(50),
    anomaly_score numeric(12,8) NOT NULL,
    es_anomalia boolean NOT NULL,
    umbral_aplicado numeric(12,8),
    evaluado_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    estado character varying(20) DEFAULT 'activo'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    CONSTRAINT ck_anomalia_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying])::text[])))
);


--
-- Name: evaluacion_anomalia_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.evaluacion_anomalia ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.evaluacion_anomalia_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: evento_custodia_externa; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.evento_custodia_externa (
    id integer NOT NULL,
    solicitud_id character varying(36) NOT NULL,
    solicitud_huella character varying(64) NOT NULL,
    custodia_id integer NOT NULL,
    articulo_id integer NOT NULL,
    tipo character varying(12) NOT NULL,
    cantidad integer NOT NULL,
    area_destino_id integer,
    comprador character varying(200),
    encargado_id integer NOT NULL,
    registrado_por integer NOT NULL,
    ocurrido_en timestamp with time zone NOT NULL,
    registrado_en timestamp with time zone NOT NULL,
    referencia_documento character varying(200) NOT NULL,
    observaciones text NOT NULL,
    alertas_control json,
    justificacion_alertas text,
    total_institucional_despues integer NOT NULL,
    cantidad_fuera_despues integer NOT NULL,
    CONSTRAINT ck_evento_custodia_cantidad CHECK ((cantidad > 0)),
    CONSTRAINT ck_evento_custodia_tipo CHECK (((tipo)::text = ANY ((ARRAY['VENTA'::character varying, 'RETORNO'::character varying])::text[])))
);


--
-- Name: evento_custodia_externa_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.evento_custodia_externa_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: evento_custodia_externa_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.evento_custodia_externa_id_seq OWNED BY public.evento_custodia_externa.id;


--
-- Name: existencia; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.existencia (
    id bigint NOT NULL,
    activo_id bigint NOT NULL,
    area_id bigint NOT NULL,
    cantidad numeric(14,2) DEFAULT 0 NOT NULL,
    stock_minimo numeric(14,2),
    stock_maximo numeric(14,2),
    estado character varying(20) DEFAULT 'activo'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    CONSTRAINT ck_existencia_cantidad CHECK ((cantidad >= (0)::numeric)),
    CONSTRAINT ck_existencia_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying])::text[]))),
    CONSTRAINT ck_existencia_stock_max CHECK (((stock_maximo IS NULL) OR (stock_maximo >= (0)::numeric))),
    CONSTRAINT ck_existencia_stock_min CHECK (((stock_minimo IS NULL) OR (stock_minimo >= (0)::numeric))),
    CONSTRAINT ck_existencia_stock_range CHECK (((stock_minimo IS NULL) OR (stock_maximo IS NULL) OR (stock_maximo >= stock_minimo)))
);


--
-- Name: existencia_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.existencia ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.existencia_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: extraccion_legacy; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.extraccion_legacy (
    id bigint NOT NULL,
    documento_legacy_id bigint NOT NULL,
    motor character varying(100) NOT NULL,
    modelo_version character varying(100),
    texto_extraido text,
    confianza_global numeric(6,5),
    procesado_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    estado character varying(20) DEFAULT 'activo'::character varying NOT NULL,
    observacion text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    texto_detectado_json jsonb,
    confianza_promedio numeric(6,5),
    CONSTRAINT ck_extraccion_confianza CHECK (((confianza_global IS NULL) OR ((confianza_global >= (0)::numeric) AND (confianza_global <= (1)::numeric)))),
    CONSTRAINT ck_extraccion_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying, 'pendiente'::character varying, 'pendiente_validacion'::character varying, 'validado'::character varying, 'error'::character varying])::text[])))
);


--
-- Name: extraccion_legacy_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.extraccion_legacy ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.extraccion_legacy_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: lotes_carga; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lotes_carga (
    id integer NOT NULL,
    fecha_escaneo timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    total_imagenes integer NOT NULL,
    tanda integer DEFAULT 2 NOT NULL,
    CONSTRAINT ck_lote_tanda CHECK ((tanda = ANY (ARRAY[1, 2])))
);


--
-- Name: lotes_carga_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.lotes_carga_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: lotes_carga_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.lotes_carga_id_seq OWNED BY public.lotes_carga.id;


--
-- Name: lotes_pendientes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.lotes_pendientes (
    id character varying(36) NOT NULL,
    articulo_id integer NOT NULL,
    usuario_id integer NOT NULL,
    extraccion json NOT NULL,
    estado character varying(20) NOT NULL,
    lote_id integer
);


--
-- Name: movimiento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.movimiento (
    id bigint NOT NULL,
    activo_id bigint NOT NULL,
    tipo_movimiento_id bigint NOT NULL,
    area_origen_id bigint,
    area_destino_id bigint,
    encargado_id bigint NOT NULL,
    usuario_registrador_id bigint NOT NULL,
    movimiento_origen_id bigint,
    documento_legacy_id bigint,
    cantidad numeric(14,2) NOT NULL,
    saldo_resultante numeric(14,2),
    fecha_hora timestamp with time zone NOT NULL,
    motivo character varying(255),
    observacion text,
    estado character varying(20) DEFAULT 'activo'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    ubicacion_evento_id bigint,
    CONSTRAINT ck_movimiento_cantidad CHECK ((cantidad > (0)::numeric)),
    CONSTRAINT ck_movimiento_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying])::text[]))),
    CONSTRAINT ck_movimiento_saldo CHECK (((saldo_resultante IS NULL) OR (saldo_resultante >= (0)::numeric))),
    CONSTRAINT ck_movimiento_transferencia_areas CHECK (((area_origen_id IS NULL) OR (area_destino_id IS NULL) OR (area_origen_id <> area_destino_id)))
);


--
-- Name: movimiento_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.movimiento ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.movimiento_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: movimientos_kardex; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.movimientos_kardex (
    id integer NOT NULL,
    articulo_id bigint NOT NULL,
    lote_id integer,
    fecha_movimiento date NOT NULL,
    detalle text NOT NULL,
    referencia character varying(100),
    area character varying(100),
    ingresos integer,
    salidas integer,
    saldo_registrado integer NOT NULL,
    ruta_imagen_respaldo character varying(512),
    numero_pagina integer,
    orden_fila integer,
    tiene_error_saldo boolean DEFAULT false NOT NULL,
    saldo_calculado integer,
    observaciones text,
    nodo_grafo character varying(100),
    requiere_auditoria_nodo boolean DEFAULT false,
    usuario_operador character varying(150),
    tipo_operacion character varying(50),
    receptor character varying(200),
    feria_id integer,
    ciudad_feria character varying(100),
    canal_venta character varying(100),
    motivo_baja character varying(200),
    referencia_documento character varying(200),
    estado character varying(20) DEFAULT 'ACTIVO'::character varying,
    area_estado character varying(40) DEFAULT 'PENDIENTE_HIL'::character varying NOT NULL,
    referencia_estado character varying(20) DEFAULT 'AUSENTE'::character varying NOT NULL,
    requiere_auditoria_referencia boolean DEFAULT false NOT NULL,
    fecha_original date,
    datos_originales json,
    tiene_error_fecha boolean DEFAULT false NOT NULL,
    fecha_estado character varying(30) DEFAULT 'SIN_ALERTA'::character varying NOT NULL,
    encargado_id integer,
    usuario_registrador_id integer,
    encargado_nombre character varying(120),
    registrado_en timestamp with time zone,
    alertas_control json,
    justificacion_alertas text,
    receptor_tipo character varying(24),
    area_operativa_id integer,
    ocurrido_en timestamp with time zone,
    solicitud_id character varying(36),
    solicitud_huella character varying(64),
    movimiento_origen_id integer,
    devuelto_por character varying(200),
    corrige_movimiento_id integer,
    cantidad_anterior integer,
    cantidad_corregida integer,
    motivo_correccion text,
    autorizado_por_id integer,
    CONSTRAINT ck_kardex_receptor_tipo CHECK (((receptor_tipo IS NULL) OR ((receptor_tipo)::text = ANY ((ARRAY['PERSONA'::character varying, 'INSTITUCION'::character varying, 'PUBLICO_GENERAL'::character varying])::text[])))),
    CONSTRAINT ck_movimiento_correccion_cantidades CHECK ((((cantidad_anterior IS NULL) OR (cantidad_anterior >= 0)) AND ((cantidad_corregida IS NULL) OR (cantidad_corregida >= 0)) AND ((corrige_movimiento_id IS NULL) OR (corrige_movimiento_id <> id)))),
    CONSTRAINT ck_movimiento_devolucion_no_reflexiva CHECK (((movimiento_origen_id IS NULL) OR (movimiento_origen_id <> id)))
);


--
-- Name: movimientos_kardex_archivados; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.movimientos_kardex_archivados (
    movimiento_id integer NOT NULL,
    lote_original_id integer NOT NULL,
    lote_canonico_id integer NOT NULL,
    datos json NOT NULL,
    archivado_en timestamp with time zone NOT NULL
);


--
-- Name: movimientos_kardex_archivados_movimiento_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.movimientos_kardex_archivados_movimiento_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: movimientos_kardex_archivados_movimiento_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.movimientos_kardex_archivados_movimiento_id_seq OWNED BY public.movimientos_kardex_archivados.movimiento_id;


--
-- Name: movimientos_kardex_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.movimientos_kardex_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: movimientos_kardex_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.movimientos_kardex_id_seq OWNED BY public.movimientos_kardex.id;


--
-- Name: permiso; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permiso (
    id bigint NOT NULL,
    nombre character varying(100) NOT NULL,
    codigo character varying(100) NOT NULL,
    descripcion character varying(255),
    estado character varying(20) DEFAULT 'activo'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_permiso_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying])::text[])))
);


--
-- Name: permiso_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.permiso ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.permiso_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: resultado_regla; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resultado_regla (
    id bigint NOT NULL,
    movimiento_id bigint NOT NULL,
    codigo_regla character varying(80) NOT NULL,
    resultado character varying(20) NOT NULL,
    detalle text,
    evaluado_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    estado character varying(20) DEFAULT 'activo'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    CONSTRAINT ck_regla_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying])::text[]))),
    CONSTRAINT ck_regla_resultado CHECK (((resultado)::text = ANY ((ARRAY['cumple'::character varying, 'advertencia'::character varying, 'viola'::character varying])::text[])))
);


--
-- Name: resultado_regla_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.resultado_regla ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.resultado_regla_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: revision_caso; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.revision_caso (
    id bigint NOT NULL,
    caso_id bigint NOT NULL,
    auditor_id bigint NOT NULL,
    estado_anterior character varying(30),
    estado_nuevo character varying(30) NOT NULL,
    comentario text,
    evidencia_ref text,
    revisado_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    CONSTRAINT ck_revision_estado_nuevo CHECK (((estado_nuevo)::text = ANY ((ARRAY['nuevo'::character varying, 'en_revision'::character varying, 'resuelto'::character varying, 'descartado'::character varying])::text[])))
);


--
-- Name: revision_caso_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.revision_caso ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.revision_caso_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: revision_control; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.revision_control (
    id integer NOT NULL,
    caso_id integer NOT NULL,
    solicitud_id character varying(36) NOT NULL,
    solicitud_huella character varying(64) NOT NULL,
    usuario_id integer NOT NULL,
    usuario_nombre character varying(120) NOT NULL,
    creado_en timestamp with time zone NOT NULL,
    anterior json NOT NULL,
    nuevo json NOT NULL,
    motivo text NOT NULL,
    documento character varying(200),
    correccion_movimiento_id integer,
    huella_contexto character varying(64) NOT NULL
);


--
-- Name: revision_control_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.revision_control_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: revision_control_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.revision_control_id_seq OWNED BY public.revision_control.id;


--
-- Name: rol; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rol (
    id bigint NOT NULL,
    nombre character varying(50) NOT NULL,
    descripcion character varying(255),
    estado character varying(20) DEFAULT 'activo'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_rol_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying])::text[])))
);


--
-- Name: rol_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.rol ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.rol_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: rol_permiso; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.rol_permiso (
    rol_id bigint NOT NULL,
    permiso_id bigint NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


--
-- Name: sinonimos_area; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sinonimos_area (
    id integer NOT NULL,
    texto_sucio character varying(200) NOT NULL,
    area_oficial_id integer,
    confirmado boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now()
);


--
-- Name: sinonimos_area_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.sinonimos_area_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: sinonimos_area_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.sinonimos_area_id_seq OWNED BY public.sinonimos_area.id;


--
-- Name: solicitudes_carga_kardex; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.solicitudes_carga_kardex (
    id integer NOT NULL,
    articulo_id integer NOT NULL,
    huella character varying(64) NOT NULL,
    estado character varying(20) NOT NULL,
    lote_id integer,
    pendiente_id character varying(36),
    usuario_id integer,
    creado_en timestamp with time zone NOT NULL,
    tanda integer DEFAULT 2 NOT NULL,
    intento integer DEFAULT 1 NOT NULL,
    servidor_instancia character varying(36),
    CONSTRAINT ck_solicitud_intento_positivo CHECK ((intento >= 1)),
    CONSTRAINT ck_solicitud_tanda CHECK ((tanda = ANY (ARRAY[1, 2])))
);


--
-- Name: solicitudes_carga_kardex_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.solicitudes_carga_kardex_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: solicitudes_carga_kardex_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.solicitudes_carga_kardex_id_seq OWNED BY public.solicitudes_carga_kardex.id;


--
-- Name: tipo_movimiento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tipo_movimiento (
    id bigint NOT NULL,
    nombre character varying(50) NOT NULL,
    codigo character varying(30) NOT NULL,
    descripcion character varying(255),
    afecta_stock boolean DEFAULT true NOT NULL,
    estado character varying(20) DEFAULT 'activo'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT ck_tipo_mov_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying])::text[])))
);


--
-- Name: tipo_movimiento_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.tipo_movimiento ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tipo_movimiento_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tramo_cobertura; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tramo_cobertura (
    id integer NOT NULL,
    articulo_id integer NOT NULL,
    gestion_desde integer NOT NULL,
    gestion_hasta integer NOT NULL,
    estado character varying(20) NOT NULL,
    paginas_faltantes integer,
    descripcion text NOT NULL,
    referencia character varying(255) NOT NULL,
    revisado_por integer NOT NULL,
    revisado_en timestamp with time zone NOT NULL,
    CONSTRAINT ck_tramo_estado CHECK (((estado)::text = ANY ((ARRAY['PENDIENTE'::character varying, 'SIN_CONFIRMAR'::character varying, 'CONFIRMADO'::character varying])::text[]))),
    CONSTRAINT ck_tramo_paginas_faltantes CHECK (((paginas_faltantes IS NULL) OR (paginas_faltantes >= 0))),
    CONSTRAINT ck_tramo_periodo CHECK ((gestion_desde <= gestion_hasta))
);


--
-- Name: tramo_cobertura_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.tramo_cobertura_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: tramo_cobertura_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.tramo_cobertura_id_seq OWNED BY public.tramo_cobertura.id;


--
-- Name: transferencia_area; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.transferencia_area (
    id integer NOT NULL,
    solicitud_id character varying(36) NOT NULL,
    solicitud_huella character varying(64) NOT NULL,
    articulo_id integer NOT NULL,
    area_origen_id integer NOT NULL,
    area_destino_id integer NOT NULL,
    cantidad integer NOT NULL,
    total_institucional integer NOT NULL,
    encargado_id integer NOT NULL,
    registrado_por integer NOT NULL,
    ocurrido_en timestamp with time zone NOT NULL,
    registrado_en timestamp with time zone NOT NULL,
    referencia_documento character varying(200) NOT NULL,
    observaciones text NOT NULL,
    alertas_control json,
    justificacion_alertas text,
    CONSTRAINT ck_transferencia_areas CHECK ((area_origen_id <> area_destino_id)),
    CONSTRAINT ck_transferencia_cantidad CHECK ((cantidad > 0))
);


--
-- Name: transferencia_area_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.transferencia_area_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transferencia_area_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.transferencia_area_id_seq OWNED BY public.transferencia_area.id;


--
-- Name: ubicacion_evento; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ubicacion_evento (
    id bigint NOT NULL,
    area_responsable_id bigint NOT NULL,
    nombre_lugar character varying(150) NOT NULL,
    tipo character varying(20) DEFAULT 'externo'::character varying NOT NULL,
    ciudad character varying(100),
    provincia character varying(100),
    departamento character varying(100),
    pais character varying(100) DEFAULT 'Bolivia'::character varying NOT NULL,
    fecha_inicio date,
    fecha_fin date,
    observacion text,
    estado character varying(20) DEFAULT 'activo'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    CONSTRAINT ck_ubicacion_evento_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying])::text[]))),
    CONSTRAINT ck_ubicacion_evento_fechas CHECK (((fecha_fin IS NULL) OR (fecha_inicio IS NULL) OR (fecha_fin >= fecha_inicio))),
    CONSTRAINT ck_ubicacion_evento_tipo CHECK (((tipo)::text = ANY ((ARRAY['interno'::character varying, 'externo'::character varying, 'evento'::character varying])::text[])))
);


--
-- Name: ubicacion_evento_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.ubicacion_evento ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.ubicacion_evento_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: usuario; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.usuario (
    id bigint NOT NULL,
    rol_id bigint NOT NULL,
    area_id bigint,
    nombre character varying(120) NOT NULL,
    email character varying(180) NOT NULL,
    password_hash character varying(255) NOT NULL,
    estado character varying(20) DEFAULT 'activo'::character varying NOT NULL,
    last_login_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    CONSTRAINT ck_usuario_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying])::text[])))
);


--
-- Name: usuario_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.usuario ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.usuario_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: validacion_legacy; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.validacion_legacy (
    id bigint NOT NULL,
    extraccion_id bigint NOT NULL,
    validador_id bigint NOT NULL,
    resultado character varying(20) NOT NULL,
    fecha_validacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    observacion text,
    correccion_aplicada boolean DEFAULT false NOT NULL,
    estado character varying(20) DEFAULT 'activo'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by bigint,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_by bigint,
    datos_validados_json jsonb,
    CONSTRAINT ck_validacion_estado CHECK (((estado)::text = ANY ((ARRAY['activo'::character varying, 'baja'::character varying, 'anulado'::character varying, 'historico'::character varying, 'pendiente'::character varying, 'validado'::character varying, 'error'::character varying])::text[]))),
    CONSTRAINT ck_validacion_resultado CHECK (((resultado)::text = ANY ((ARRAY['pendiente'::character varying, 'validado'::character varying, 'corregido'::character varying, 'rechazado'::character varying])::text[])))
);


--
-- Name: validacion_legacy_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.validacion_legacy ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.validacion_legacy_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: analitica_operativa_resultados id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_operativa_resultados ALTER COLUMN id SET DEFAULT nextval('public.analitica_operativa_resultados_id_seq'::regclass);


--
-- Name: analitica_resultados id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_resultados ALTER COLUMN id SET DEFAULT nextval('public.analitica_resultados_id_seq'::regclass);


--
-- Name: analitica_revisiones id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_revisiones ALTER COLUMN id SET DEFAULT nextval('public.analitica_revisiones_id_seq'::regclass);


--
-- Name: caso_control id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_control ALTER COLUMN id SET DEFAULT nextval('public.caso_control_id_seq'::regclass);


--
-- Name: catalogo_areas id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalogo_areas ALTER COLUMN id SET DEFAULT nextval('public.catalogo_areas_id_seq'::regclass);


--
-- Name: catalogo_ferias id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalogo_ferias ALTER COLUMN id SET DEFAULT nextval('public.catalogo_ferias_id_seq'::regclass);


--
-- Name: cierre_anual id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cierre_anual ALTER COLUMN id SET DEFAULT nextval('public.cierre_anual_id_seq'::regclass);


--
-- Name: custodia_externa id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.custodia_externa ALTER COLUMN id SET DEFAULT nextval('public.custodia_externa_id_seq'::regclass);


--
-- Name: evento_custodia_externa id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evento_custodia_externa ALTER COLUMN id SET DEFAULT nextval('public.evento_custodia_externa_id_seq'::regclass);


--
-- Name: lotes_carga id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lotes_carga ALTER COLUMN id SET DEFAULT nextval('public.lotes_carga_id_seq'::regclass);


--
-- Name: movimientos_kardex id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex ALTER COLUMN id SET DEFAULT nextval('public.movimientos_kardex_id_seq'::regclass);


--
-- Name: movimientos_kardex_archivados movimiento_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex_archivados ALTER COLUMN movimiento_id SET DEFAULT nextval('public.movimientos_kardex_archivados_movimiento_id_seq'::regclass);


--
-- Name: revision_control id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.revision_control ALTER COLUMN id SET DEFAULT nextval('public.revision_control_id_seq'::regclass);


--
-- Name: sinonimos_area id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sinonimos_area ALTER COLUMN id SET DEFAULT nextval('public.sinonimos_area_id_seq'::regclass);


--
-- Name: solicitudes_carga_kardex id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solicitudes_carga_kardex ALTER COLUMN id SET DEFAULT nextval('public.solicitudes_carga_kardex_id_seq'::regclass);


--
-- Name: tramo_cobertura id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tramo_cobertura ALTER COLUMN id SET DEFAULT nextval('public.tramo_cobertura_id_seq'::regclass);


--
-- Name: transferencia_area id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencia_area ALTER COLUMN id SET DEFAULT nextval('public.transferencia_area_id_seq'::regclass);


--
-- Name: activo activo_codigo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activo
    ADD CONSTRAINT activo_codigo_key UNIQUE (codigo);


--
-- Name: activo activo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activo
    ADD CONSTRAINT activo_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: alerta alerta_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerta
    ADD CONSTRAINT alerta_pkey PRIMARY KEY (id);


--
-- Name: analitica_modelos analitica_modelos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_modelos
    ADD CONSTRAINT analitica_modelos_pkey PRIMARY KEY (id);


--
-- Name: analitica_modelos analitica_modelos_plaza_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_modelos
    ADD CONSTRAINT analitica_modelos_plaza_key UNIQUE (plaza);


--
-- Name: analitica_operativa_modelos analitica_operativa_modelos_activo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_operativa_modelos
    ADD CONSTRAINT analitica_operativa_modelos_activo_key UNIQUE (activo);


--
-- Name: analitica_operativa_modelos analitica_operativa_modelos_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_operativa_modelos
    ADD CONSTRAINT analitica_operativa_modelos_pkey PRIMARY KEY (id);


--
-- Name: analitica_operativa_modelos analitica_operativa_modelos_plaza_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_operativa_modelos
    ADD CONSTRAINT analitica_operativa_modelos_plaza_key UNIQUE (plaza);


--
-- Name: analitica_operativa_resultados analitica_operativa_resultados_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_operativa_resultados
    ADD CONSTRAINT analitica_operativa_resultados_pkey PRIMARY KEY (id);


--
-- Name: analitica_resultados analitica_resultados_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_resultados
    ADD CONSTRAINT analitica_resultados_pkey PRIMARY KEY (id);


--
-- Name: analitica_revisiones analitica_revisiones_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_revisiones
    ADD CONSTRAINT analitica_revisiones_pkey PRIMARY KEY (id);


--
-- Name: apertura_inventario apertura_inventario_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.apertura_inventario
    ADD CONSTRAINT apertura_inventario_pkey PRIMARY KEY (articulo_id);


--
-- Name: area area_codigo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.area
    ADD CONSTRAINT area_codigo_key UNIQUE (codigo);


--
-- Name: area area_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.area
    ADD CONSTRAINT area_nombre_key UNIQUE (nombre);


--
-- Name: area area_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.area
    ADD CONSTRAINT area_pkey PRIMARY KEY (id);


--
-- Name: auditoria_sistema auditoria_sistema_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria_sistema
    ADD CONSTRAINT auditoria_sistema_pkey PRIMARY KEY (id);


--
-- Name: caso_auditoria caso_auditoria_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_auditoria
    ADD CONSTRAINT caso_auditoria_pkey PRIMARY KEY (id);


--
-- Name: caso_control caso_control_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_control
    ADD CONSTRAINT caso_control_pkey PRIMARY KEY (id);


--
-- Name: catalogo_areas catalogo_areas_nombre_oficial_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalogo_areas
    ADD CONSTRAINT catalogo_areas_nombre_oficial_key UNIQUE (nombre_oficial);


--
-- Name: catalogo_areas catalogo_areas_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalogo_areas
    ADD CONSTRAINT catalogo_areas_pkey PRIMARY KEY (id);


--
-- Name: catalogo_ferias catalogo_ferias_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalogo_ferias
    ADD CONSTRAINT catalogo_ferias_nombre_key UNIQUE (nombre);


--
-- Name: catalogo_ferias catalogo_ferias_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalogo_ferias
    ADD CONSTRAINT catalogo_ferias_pkey PRIMARY KEY (id);


--
-- Name: categoria_activo categoria_activo_codigo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categoria_activo
    ADD CONSTRAINT categoria_activo_codigo_key UNIQUE (codigo);


--
-- Name: categoria_activo categoria_activo_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categoria_activo
    ADD CONSTRAINT categoria_activo_nombre_key UNIQUE (nombre);


--
-- Name: categoria_activo categoria_activo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categoria_activo
    ADD CONSTRAINT categoria_activo_pkey PRIMARY KEY (id);


--
-- Name: cierre_anual cierre_anual_gestion_activa_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cierre_anual
    ADD CONSTRAINT cierre_anual_gestion_activa_key UNIQUE (gestion_activa);


--
-- Name: cierre_anual cierre_anual_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cierre_anual
    ADD CONSTRAINT cierre_anual_pkey PRIMARY KEY (id);


--
-- Name: cierre_anual cierre_anual_solicitud_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cierre_anual
    ADD CONSTRAINT cierre_anual_solicitud_id_key UNIQUE (solicitud_id);


--
-- Name: cobertura_articulo cobertura_articulo_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cobertura_articulo
    ADD CONSTRAINT cobertura_articulo_pkey PRIMARY KEY (articulo_id);


--
-- Name: conciliacion_inicial conciliacion_inicial_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conciliacion_inicial
    ADD CONSTRAINT conciliacion_inicial_pkey PRIMARY KEY (articulo_id);


--
-- Name: custodia_externa custodia_externa_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.custodia_externa
    ADD CONSTRAINT custodia_externa_pkey PRIMARY KEY (id);


--
-- Name: documento_legacy documento_legacy_codigo_documento_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento_legacy
    ADD CONSTRAINT documento_legacy_codigo_documento_key UNIQUE (codigo_documento);


--
-- Name: documento_legacy documento_legacy_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento_legacy
    ADD CONSTRAINT documento_legacy_pkey PRIMARY KEY (id);


--
-- Name: evaluacion_anomalia evaluacion_anomalia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluacion_anomalia
    ADD CONSTRAINT evaluacion_anomalia_pkey PRIMARY KEY (id);


--
-- Name: evento_custodia_externa evento_custodia_externa_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evento_custodia_externa
    ADD CONSTRAINT evento_custodia_externa_pkey PRIMARY KEY (id);


--
-- Name: existencia existencia_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.existencia
    ADD CONSTRAINT existencia_pkey PRIMARY KEY (id);


--
-- Name: extraccion_legacy extraccion_legacy_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.extraccion_legacy
    ADD CONSTRAINT extraccion_legacy_pkey PRIMARY KEY (id);


--
-- Name: lotes_carga lotes_carga_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lotes_carga
    ADD CONSTRAINT lotes_carga_pkey PRIMARY KEY (id);


--
-- Name: lotes_pendientes lotes_pendientes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lotes_pendientes
    ADD CONSTRAINT lotes_pendientes_pkey PRIMARY KEY (id);


--
-- Name: movimiento movimiento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimiento
    ADD CONSTRAINT movimiento_pkey PRIMARY KEY (id);


--
-- Name: movimientos_kardex_archivados movimientos_kardex_archivados_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex_archivados
    ADD CONSTRAINT movimientos_kardex_archivados_pkey PRIMARY KEY (movimiento_id);


--
-- Name: movimientos_kardex movimientos_kardex_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex
    ADD CONSTRAINT movimientos_kardex_pkey PRIMARY KEY (id);


--
-- Name: permiso permiso_codigo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permiso
    ADD CONSTRAINT permiso_codigo_key UNIQUE (codigo);


--
-- Name: permiso permiso_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permiso
    ADD CONSTRAINT permiso_nombre_key UNIQUE (nombre);


--
-- Name: permiso permiso_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permiso
    ADD CONSTRAINT permiso_pkey PRIMARY KEY (id);


--
-- Name: resultado_regla resultado_regla_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resultado_regla
    ADD CONSTRAINT resultado_regla_pkey PRIMARY KEY (id);


--
-- Name: revision_caso revision_caso_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.revision_caso
    ADD CONSTRAINT revision_caso_pkey PRIMARY KEY (id);


--
-- Name: revision_control revision_control_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.revision_control
    ADD CONSTRAINT revision_control_pkey PRIMARY KEY (id);


--
-- Name: rol rol_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_nombre_key UNIQUE (nombre);


--
-- Name: rol_permiso rol_permiso_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol_permiso
    ADD CONSTRAINT rol_permiso_pkey PRIMARY KEY (rol_id, permiso_id);


--
-- Name: rol rol_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol
    ADD CONSTRAINT rol_pkey PRIMARY KEY (id);


--
-- Name: sinonimos_area sinonimos_area_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sinonimos_area
    ADD CONSTRAINT sinonimos_area_pkey PRIMARY KEY (id);


--
-- Name: sinonimos_area sinonimos_area_texto_sucio_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sinonimos_area
    ADD CONSTRAINT sinonimos_area_texto_sucio_key UNIQUE (texto_sucio);


--
-- Name: solicitudes_carga_kardex solicitudes_carga_kardex_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solicitudes_carga_kardex
    ADD CONSTRAINT solicitudes_carga_kardex_pkey PRIMARY KEY (id);


--
-- Name: tipo_movimiento tipo_movimiento_codigo_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_movimiento
    ADD CONSTRAINT tipo_movimiento_codigo_key UNIQUE (codigo);


--
-- Name: tipo_movimiento tipo_movimiento_nombre_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_movimiento
    ADD CONSTRAINT tipo_movimiento_nombre_key UNIQUE (nombre);


--
-- Name: tipo_movimiento tipo_movimiento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tipo_movimiento
    ADD CONSTRAINT tipo_movimiento_pkey PRIMARY KEY (id);


--
-- Name: tramo_cobertura tramo_cobertura_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tramo_cobertura
    ADD CONSTRAINT tramo_cobertura_pkey PRIMARY KEY (id);


--
-- Name: transferencia_area transferencia_area_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencia_area
    ADD CONSTRAINT transferencia_area_pkey PRIMARY KEY (id);


--
-- Name: ubicacion_evento ubicacion_evento_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ubicacion_evento
    ADD CONSTRAINT ubicacion_evento_pkey PRIMARY KEY (id);


--
-- Name: analitica_resultados uq_analitica_modelo_movimiento; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_resultados
    ADD CONSTRAINT uq_analitica_modelo_movimiento UNIQUE (modelo_id, movimiento_id);


--
-- Name: solicitudes_carga_kardex uq_carga_articulo_huella; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solicitudes_carga_kardex
    ADD CONSTRAINT uq_carga_articulo_huella UNIQUE (articulo_id, huella);


--
-- Name: caso_control uq_caso_control_custodia; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_control
    ADD CONSTRAINT uq_caso_control_custodia UNIQUE (custodia_id);


--
-- Name: caso_control uq_caso_control_evento; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_control
    ADD CONSTRAINT uq_caso_control_evento UNIQUE (evento_custodia_id);


--
-- Name: caso_control uq_caso_control_movimiento; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_control
    ADD CONSTRAINT uq_caso_control_movimiento UNIQUE (movimiento_id);


--
-- Name: caso_control uq_caso_control_transferencia; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_control
    ADD CONSTRAINT uq_caso_control_transferencia UNIQUE (transferencia_id);


--
-- Name: cierre_anual uq_cierre_anual_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cierre_anual
    ADD CONSTRAINT uq_cierre_anual_version UNIQUE (gestion, version);


--
-- Name: custodia_externa uq_custodia_solicitud; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.custodia_externa
    ADD CONSTRAINT uq_custodia_solicitud UNIQUE (solicitud_id);


--
-- Name: evento_custodia_externa uq_evento_custodia_solicitud; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evento_custodia_externa
    ADD CONSTRAINT uq_evento_custodia_solicitud UNIQUE (solicitud_id);


--
-- Name: existencia uq_existencia_activo_area; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.existencia
    ADD CONSTRAINT uq_existencia_activo_area UNIQUE (activo_id, area_id);


--
-- Name: movimientos_kardex uq_movimiento_solicitud; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex
    ADD CONSTRAINT uq_movimiento_solicitud UNIQUE (solicitud_id);


--
-- Name: analitica_operativa_resultados uq_resultado_operativo_recurso; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_operativa_resultados
    ADD CONSTRAINT uq_resultado_operativo_recurso UNIQUE (modelo_id, recurso);


--
-- Name: revision_control uq_revision_control_solicitud; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.revision_control
    ADD CONSTRAINT uq_revision_control_solicitud UNIQUE (solicitud_id);


--
-- Name: transferencia_area uq_transferencia_solicitud; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencia_area
    ADD CONSTRAINT uq_transferencia_solicitud UNIQUE (solicitud_id);


--
-- Name: usuario usuario_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_email_key UNIQUE (email);


--
-- Name: usuario usuario_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT usuario_pkey PRIMARY KEY (id);


--
-- Name: validacion_legacy validacion_legacy_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.validacion_legacy
    ADD CONSTRAINT validacion_legacy_pkey PRIMARY KEY (id);


--
-- Name: idx_activo_categoria; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_activo_categoria ON public.activo USING btree (categoria_id);


--
-- Name: idx_alerta_estado_prioridad; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alerta_estado_prioridad ON public.alerta USING btree (estado, prioridad);


--
-- Name: idx_alerta_movimiento; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alerta_movimiento ON public.alerta USING btree (movimiento_id);


--
-- Name: idx_anomalia_movimiento_fecha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_anomalia_movimiento_fecha ON public.evaluacion_anomalia USING btree (movimiento_id, evaluado_at);


--
-- Name: idx_auditoria_recurso; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_auditoria_recurso ON public.auditoria_sistema USING btree (recurso, recurso_id);


--
-- Name: idx_auditoria_usuario_fecha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_auditoria_usuario_fecha ON public.auditoria_sistema USING btree (usuario_id, fecha_hora);


--
-- Name: idx_caso_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_caso_estado ON public.caso_auditoria USING btree (estado_caso);


--
-- Name: idx_documento_legacy_periodo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_documento_legacy_periodo ON public.documento_legacy USING btree (periodo_documental);


--
-- Name: idx_existencia_activo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_existencia_activo ON public.existencia USING btree (activo_id);


--
-- Name: idx_existencia_area; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_existencia_area ON public.existencia USING btree (area_id);


--
-- Name: idx_extraccion_documento; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_extraccion_documento ON public.extraccion_legacy USING btree (documento_legacy_id);


--
-- Name: idx_movimiento_activo_fecha; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_movimiento_activo_fecha ON public.movimiento USING btree (activo_id, fecha_hora);


--
-- Name: idx_movimiento_destino; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_movimiento_destino ON public.movimiento USING btree (area_destino_id);


--
-- Name: idx_movimiento_encargado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_movimiento_encargado ON public.movimiento USING btree (encargado_id);


--
-- Name: idx_movimiento_origen; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_movimiento_origen ON public.movimiento USING btree (area_origen_id);


--
-- Name: idx_movimiento_registrador; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_movimiento_registrador ON public.movimiento USING btree (usuario_registrador_id);


--
-- Name: idx_movimiento_ubicacion_evento; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_movimiento_ubicacion_evento ON public.movimiento USING btree (ubicacion_evento_id);


--
-- Name: idx_resultado_regla_movimiento; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_resultado_regla_movimiento ON public.resultado_regla USING btree (movimiento_id);


--
-- Name: idx_revision_caso; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_revision_caso ON public.revision_caso USING btree (caso_id, revisado_at);


--
-- Name: idx_ubicacion_evento_area; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ubicacion_evento_area ON public.ubicacion_evento USING btree (area_responsable_id);


--
-- Name: idx_usuario_area; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_usuario_area ON public.usuario USING btree (area_id);


--
-- Name: ix_analitica_operativa_resultados_articulo_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analitica_operativa_resultados_articulo_id ON public.analitica_operativa_resultados USING btree (articulo_id);


--
-- Name: ix_analitica_operativa_resultados_modelo_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analitica_operativa_resultados_modelo_id ON public.analitica_operativa_resultados USING btree (modelo_id);


--
-- Name: ix_analitica_resultados_alerta; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analitica_resultados_alerta ON public.analitica_resultados USING btree (alerta);


--
-- Name: ix_analitica_resultados_articulo_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analitica_resultados_articulo_id ON public.analitica_resultados USING btree (articulo_id);


--
-- Name: ix_analitica_resultados_gestion; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analitica_resultados_gestion ON public.analitica_resultados USING btree (gestion);


--
-- Name: ix_analitica_resultados_modelo_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analitica_resultados_modelo_id ON public.analitica_resultados USING btree (modelo_id);


--
-- Name: ix_analitica_resultados_movimiento_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analitica_resultados_movimiento_id ON public.analitica_resultados USING btree (movimiento_id);


--
-- Name: ix_analitica_revisiones_resultado_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_analitica_revisiones_resultado_id ON public.analitica_revisiones USING btree (resultado_id);


--
-- Name: ix_caso_control_articulo_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_caso_control_articulo_id ON public.caso_control USING btree (articulo_id);


--
-- Name: ix_caso_control_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_caso_control_estado ON public.caso_control USING btree (estado);


--
-- Name: ix_cierre_anual_gestion; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_cierre_anual_gestion ON public.cierre_anual USING btree (gestion);


--
-- Name: ix_custodia_articulo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_custodia_articulo ON public.custodia_externa USING btree (articulo_id);


--
-- Name: ix_evento_custodia_articulo; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_evento_custodia_articulo ON public.evento_custodia_externa USING btree (articulo_id);


--
-- Name: ix_evento_custodia_entrega; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_evento_custodia_entrega ON public.evento_custodia_externa USING btree (custodia_id);


--
-- Name: ix_kardex_fecha_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_kardex_fecha_estado ON public.movimientos_kardex USING btree (fecha_movimiento, estado);


--
-- Name: ix_movimiento_correccion_origen; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_movimiento_correccion_origen ON public.movimientos_kardex USING btree (corrige_movimiento_id);


--
-- Name: ix_movimiento_devolucion_origen; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_movimiento_devolucion_origen ON public.movimientos_kardex USING btree (movimiento_origen_id);


--
-- Name: ix_movimientos_kardex_area_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_movimientos_kardex_area_estado ON public.movimientos_kardex USING btree (area_estado);


--
-- Name: ix_movimientos_kardex_referencia_estado; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_movimientos_kardex_referencia_estado ON public.movimientos_kardex USING btree (referencia_estado);


--
-- Name: ix_revision_control_caso_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_revision_control_caso_id ON public.revision_control USING btree (caso_id);


--
-- Name: ix_tramo_cobertura_articulo_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_tramo_cobertura_articulo_id ON public.tramo_cobertura USING btree (articulo_id);


--
-- Name: analitica_modelos analitica_modelos_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_modelos
    ADD CONSTRAINT analitica_modelos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: analitica_operativa_modelos analitica_operativa_modelos_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_operativa_modelos
    ADD CONSTRAINT analitica_operativa_modelos_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: analitica_operativa_resultados analitica_operativa_resultados_articulo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_operativa_resultados
    ADD CONSTRAINT analitica_operativa_resultados_articulo_id_fkey FOREIGN KEY (articulo_id) REFERENCES public.activo(id);


--
-- Name: analitica_operativa_resultados analitica_operativa_resultados_custodia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_operativa_resultados
    ADD CONSTRAINT analitica_operativa_resultados_custodia_id_fkey FOREIGN KEY (custodia_id) REFERENCES public.custodia_externa(id);


--
-- Name: analitica_operativa_resultados analitica_operativa_resultados_evento_custodia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_operativa_resultados
    ADD CONSTRAINT analitica_operativa_resultados_evento_custodia_id_fkey FOREIGN KEY (evento_custodia_id) REFERENCES public.evento_custodia_externa(id);


--
-- Name: analitica_operativa_resultados analitica_operativa_resultados_modelo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_operativa_resultados
    ADD CONSTRAINT analitica_operativa_resultados_modelo_id_fkey FOREIGN KEY (modelo_id) REFERENCES public.analitica_operativa_modelos(id);


--
-- Name: analitica_operativa_resultados analitica_operativa_resultados_movimiento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_operativa_resultados
    ADD CONSTRAINT analitica_operativa_resultados_movimiento_id_fkey FOREIGN KEY (movimiento_id) REFERENCES public.movimientos_kardex(id);


--
-- Name: analitica_operativa_resultados analitica_operativa_resultados_transferencia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_operativa_resultados
    ADD CONSTRAINT analitica_operativa_resultados_transferencia_id_fkey FOREIGN KEY (transferencia_id) REFERENCES public.transferencia_area(id);


--
-- Name: analitica_resultados analitica_resultados_articulo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_resultados
    ADD CONSTRAINT analitica_resultados_articulo_id_fkey FOREIGN KEY (articulo_id) REFERENCES public.activo(id);


--
-- Name: analitica_resultados analitica_resultados_modelo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_resultados
    ADD CONSTRAINT analitica_resultados_modelo_id_fkey FOREIGN KEY (modelo_id) REFERENCES public.analitica_modelos(id);


--
-- Name: analitica_resultados analitica_resultados_movimiento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_resultados
    ADD CONSTRAINT analitica_resultados_movimiento_id_fkey FOREIGN KEY (movimiento_id) REFERENCES public.movimientos_kardex(id);


--
-- Name: analitica_revisiones analitica_revisiones_resultado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_revisiones
    ADD CONSTRAINT analitica_revisiones_resultado_id_fkey FOREIGN KEY (resultado_id) REFERENCES public.analitica_resultados(id);


--
-- Name: analitica_revisiones analitica_revisiones_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.analitica_revisiones
    ADD CONSTRAINT analitica_revisiones_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: apertura_inventario apertura_inventario_aprobado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.apertura_inventario
    ADD CONSTRAINT apertura_inventario_aprobado_por_fkey FOREIGN KEY (aprobado_por) REFERENCES public.usuario(id);


--
-- Name: apertura_inventario apertura_inventario_articulo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.apertura_inventario
    ADD CONSTRAINT apertura_inventario_articulo_id_fkey FOREIGN KEY (articulo_id) REFERENCES public.activo(id);


--
-- Name: caso_control caso_control_articulo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_control
    ADD CONSTRAINT caso_control_articulo_id_fkey FOREIGN KEY (articulo_id) REFERENCES public.activo(id);


--
-- Name: caso_control caso_control_asignado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_control
    ADD CONSTRAINT caso_control_asignado_id_fkey FOREIGN KEY (asignado_id) REFERENCES public.usuario(id);


--
-- Name: caso_control caso_control_custodia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_control
    ADD CONSTRAINT caso_control_custodia_id_fkey FOREIGN KEY (custodia_id) REFERENCES public.custodia_externa(id);


--
-- Name: caso_control caso_control_evento_custodia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_control
    ADD CONSTRAINT caso_control_evento_custodia_id_fkey FOREIGN KEY (evento_custodia_id) REFERENCES public.evento_custodia_externa(id);


--
-- Name: caso_control caso_control_movimiento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_control
    ADD CONSTRAINT caso_control_movimiento_id_fkey FOREIGN KEY (movimiento_id) REFERENCES public.movimientos_kardex(id);


--
-- Name: caso_control caso_control_transferencia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_control
    ADD CONSTRAINT caso_control_transferencia_id_fkey FOREIGN KEY (transferencia_id) REFERENCES public.transferencia_area(id);


--
-- Name: cierre_anual cierre_anual_reabierto_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cierre_anual
    ADD CONSTRAINT cierre_anual_reabierto_por_fkey FOREIGN KEY (reabierto_por) REFERENCES public.usuario(id);


--
-- Name: cierre_anual cierre_anual_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cierre_anual
    ADD CONSTRAINT cierre_anual_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: cobertura_articulo cobertura_articulo_articulo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cobertura_articulo
    ADD CONSTRAINT cobertura_articulo_articulo_id_fkey FOREIGN KEY (articulo_id) REFERENCES public.activo(id);


--
-- Name: cobertura_articulo cobertura_articulo_revisado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cobertura_articulo
    ADD CONSTRAINT cobertura_articulo_revisado_por_fkey FOREIGN KEY (revisado_por) REFERENCES public.usuario(id);


--
-- Name: conciliacion_inicial conciliacion_inicial_ajuste_movimiento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conciliacion_inicial
    ADD CONSTRAINT conciliacion_inicial_ajuste_movimiento_id_fkey FOREIGN KEY (ajuste_movimiento_id) REFERENCES public.movimientos_kardex(id);


--
-- Name: conciliacion_inicial conciliacion_inicial_articulo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conciliacion_inicial
    ADD CONSTRAINT conciliacion_inicial_articulo_id_fkey FOREIGN KEY (articulo_id) REFERENCES public.activo(id);


--
-- Name: conciliacion_inicial conciliacion_inicial_encargado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conciliacion_inicial
    ADD CONSTRAINT conciliacion_inicial_encargado_id_fkey FOREIGN KEY (encargado_id) REFERENCES public.usuario(id);


--
-- Name: conciliacion_inicial conciliacion_inicial_registrado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conciliacion_inicial
    ADD CONSTRAINT conciliacion_inicial_registrado_por_fkey FOREIGN KEY (registrado_por) REFERENCES public.usuario(id);


--
-- Name: custodia_externa custodia_externa_area_origen_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.custodia_externa
    ADD CONSTRAINT custodia_externa_area_origen_id_fkey FOREIGN KEY (area_origen_id) REFERENCES public.area(id);


--
-- Name: custodia_externa custodia_externa_articulo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.custodia_externa
    ADD CONSTRAINT custodia_externa_articulo_id_fkey FOREIGN KEY (articulo_id) REFERENCES public.activo(id);


--
-- Name: custodia_externa custodia_externa_encargado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.custodia_externa
    ADD CONSTRAINT custodia_externa_encargado_id_fkey FOREIGN KEY (encargado_id) REFERENCES public.usuario(id);


--
-- Name: custodia_externa custodia_externa_registrado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.custodia_externa
    ADD CONSTRAINT custodia_externa_registrado_por_fkey FOREIGN KEY (registrado_por) REFERENCES public.usuario(id);


--
-- Name: evento_custodia_externa evento_custodia_externa_area_destino_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evento_custodia_externa
    ADD CONSTRAINT evento_custodia_externa_area_destino_id_fkey FOREIGN KEY (area_destino_id) REFERENCES public.area(id);


--
-- Name: evento_custodia_externa evento_custodia_externa_articulo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evento_custodia_externa
    ADD CONSTRAINT evento_custodia_externa_articulo_id_fkey FOREIGN KEY (articulo_id) REFERENCES public.activo(id);


--
-- Name: evento_custodia_externa evento_custodia_externa_custodia_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evento_custodia_externa
    ADD CONSTRAINT evento_custodia_externa_custodia_id_fkey FOREIGN KEY (custodia_id) REFERENCES public.custodia_externa(id);


--
-- Name: evento_custodia_externa evento_custodia_externa_encargado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evento_custodia_externa
    ADD CONSTRAINT evento_custodia_externa_encargado_id_fkey FOREIGN KEY (encargado_id) REFERENCES public.usuario(id);


--
-- Name: evento_custodia_externa evento_custodia_externa_registrado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evento_custodia_externa
    ADD CONSTRAINT evento_custodia_externa_registrado_por_fkey FOREIGN KEY (registrado_por) REFERENCES public.usuario(id);


--
-- Name: activo fk_activo_categoria; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activo
    ADD CONSTRAINT fk_activo_categoria FOREIGN KEY (categoria_id) REFERENCES public.categoria_activo(id);


--
-- Name: activo fk_activo_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activo
    ADD CONSTRAINT fk_activo_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: activo fk_activo_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activo
    ADD CONSTRAINT fk_activo_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: alerta fk_alerta_anomalia; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerta
    ADD CONSTRAINT fk_alerta_anomalia FOREIGN KEY (evaluacion_anomalia_id) REFERENCES public.evaluacion_anomalia(id);


--
-- Name: alerta fk_alerta_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerta
    ADD CONSTRAINT fk_alerta_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: alerta fk_alerta_movimiento; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerta
    ADD CONSTRAINT fk_alerta_movimiento FOREIGN KEY (movimiento_id) REFERENCES public.movimiento(id);


--
-- Name: alerta fk_alerta_regla; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerta
    ADD CONSTRAINT fk_alerta_regla FOREIGN KEY (resultado_regla_id) REFERENCES public.resultado_regla(id);


--
-- Name: alerta fk_alerta_revisada_por; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerta
    ADD CONSTRAINT fk_alerta_revisada_por FOREIGN KEY (revisada_por) REFERENCES public.usuario(id);


--
-- Name: alerta fk_alerta_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alerta
    ADD CONSTRAINT fk_alerta_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: evaluacion_anomalia fk_anomalia_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluacion_anomalia
    ADD CONSTRAINT fk_anomalia_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: evaluacion_anomalia fk_anomalia_movimiento; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluacion_anomalia
    ADD CONSTRAINT fk_anomalia_movimiento FOREIGN KEY (movimiento_id) REFERENCES public.movimiento(id);


--
-- Name: evaluacion_anomalia fk_anomalia_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.evaluacion_anomalia
    ADD CONSTRAINT fk_anomalia_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: area fk_area_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.area
    ADD CONSTRAINT fk_area_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: area fk_area_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.area
    ADD CONSTRAINT fk_area_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: auditoria_sistema fk_auditoria_usuario; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auditoria_sistema
    ADD CONSTRAINT fk_auditoria_usuario FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: caso_auditoria fk_caso_alerta; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_auditoria
    ADD CONSTRAINT fk_caso_alerta FOREIGN KEY (alerta_id) REFERENCES public.alerta(id);


--
-- Name: caso_auditoria fk_caso_auditor; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_auditoria
    ADD CONSTRAINT fk_caso_auditor FOREIGN KEY (auditor_id) REFERENCES public.usuario(id);


--
-- Name: caso_auditoria fk_caso_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_auditoria
    ADD CONSTRAINT fk_caso_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: caso_auditoria fk_caso_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.caso_auditoria
    ADD CONSTRAINT fk_caso_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: categoria_activo fk_categoria_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categoria_activo
    ADD CONSTRAINT fk_categoria_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: categoria_activo fk_categoria_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categoria_activo
    ADD CONSTRAINT fk_categoria_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: documento_legacy fk_documento_legacy_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento_legacy
    ADD CONSTRAINT fk_documento_legacy_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: documento_legacy fk_documento_legacy_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documento_legacy
    ADD CONSTRAINT fk_documento_legacy_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: existencia fk_existencia_activo; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.existencia
    ADD CONSTRAINT fk_existencia_activo FOREIGN KEY (activo_id) REFERENCES public.activo(id);


--
-- Name: existencia fk_existencia_area; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.existencia
    ADD CONSTRAINT fk_existencia_area FOREIGN KEY (area_id) REFERENCES public.area(id);


--
-- Name: existencia fk_existencia_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.existencia
    ADD CONSTRAINT fk_existencia_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: existencia fk_existencia_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.existencia
    ADD CONSTRAINT fk_existencia_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: extraccion_legacy fk_extraccion_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.extraccion_legacy
    ADD CONSTRAINT fk_extraccion_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: extraccion_legacy fk_extraccion_documento; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.extraccion_legacy
    ADD CONSTRAINT fk_extraccion_documento FOREIGN KEY (documento_legacy_id) REFERENCES public.documento_legacy(id);


--
-- Name: extraccion_legacy fk_extraccion_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.extraccion_legacy
    ADD CONSTRAINT fk_extraccion_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: movimiento fk_movimiento_activo; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimiento
    ADD CONSTRAINT fk_movimiento_activo FOREIGN KEY (activo_id) REFERENCES public.activo(id);


--
-- Name: movimiento fk_movimiento_area_destino; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimiento
    ADD CONSTRAINT fk_movimiento_area_destino FOREIGN KEY (area_destino_id) REFERENCES public.area(id);


--
-- Name: movimiento fk_movimiento_area_origen; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimiento
    ADD CONSTRAINT fk_movimiento_area_origen FOREIGN KEY (area_origen_id) REFERENCES public.area(id);


--
-- Name: movimientos_kardex fk_movimiento_correccion_autorizado; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex
    ADD CONSTRAINT fk_movimiento_correccion_autorizado FOREIGN KEY (autorizado_por_id) REFERENCES public.usuario(id);


--
-- Name: movimientos_kardex fk_movimiento_correccion_origen; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex
    ADD CONSTRAINT fk_movimiento_correccion_origen FOREIGN KEY (corrige_movimiento_id) REFERENCES public.movimientos_kardex(id);


--
-- Name: movimiento fk_movimiento_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimiento
    ADD CONSTRAINT fk_movimiento_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: movimientos_kardex fk_movimiento_devolucion_origen; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex
    ADD CONSTRAINT fk_movimiento_devolucion_origen FOREIGN KEY (movimiento_origen_id) REFERENCES public.movimientos_kardex(id);


--
-- Name: movimiento fk_movimiento_documento_legacy; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimiento
    ADD CONSTRAINT fk_movimiento_documento_legacy FOREIGN KEY (documento_legacy_id) REFERENCES public.documento_legacy(id);


--
-- Name: movimiento fk_movimiento_encargado; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimiento
    ADD CONSTRAINT fk_movimiento_encargado FOREIGN KEY (encargado_id) REFERENCES public.usuario(id);


--
-- Name: movimientos_kardex fk_movimiento_encargado; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex
    ADD CONSTRAINT fk_movimiento_encargado FOREIGN KEY (encargado_id) REFERENCES public.usuario(id);


--
-- Name: movimiento fk_movimiento_origen; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimiento
    ADD CONSTRAINT fk_movimiento_origen FOREIGN KEY (movimiento_origen_id) REFERENCES public.movimiento(id);


--
-- Name: movimiento fk_movimiento_registrador; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimiento
    ADD CONSTRAINT fk_movimiento_registrador FOREIGN KEY (usuario_registrador_id) REFERENCES public.usuario(id);


--
-- Name: movimientos_kardex fk_movimiento_registrador; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex
    ADD CONSTRAINT fk_movimiento_registrador FOREIGN KEY (usuario_registrador_id) REFERENCES public.usuario(id);


--
-- Name: movimiento fk_movimiento_tipo; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimiento
    ADD CONSTRAINT fk_movimiento_tipo FOREIGN KEY (tipo_movimiento_id) REFERENCES public.tipo_movimiento(id);


--
-- Name: movimiento fk_movimiento_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimiento
    ADD CONSTRAINT fk_movimiento_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: resultado_regla fk_regla_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resultado_regla
    ADD CONSTRAINT fk_regla_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: resultado_regla fk_regla_movimiento; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resultado_regla
    ADD CONSTRAINT fk_regla_movimiento FOREIGN KEY (movimiento_id) REFERENCES public.movimiento(id);


--
-- Name: resultado_regla fk_regla_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resultado_regla
    ADD CONSTRAINT fk_regla_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: revision_caso fk_revision_auditor; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.revision_caso
    ADD CONSTRAINT fk_revision_auditor FOREIGN KEY (auditor_id) REFERENCES public.usuario(id);


--
-- Name: revision_caso fk_revision_caso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.revision_caso
    ADD CONSTRAINT fk_revision_caso FOREIGN KEY (caso_id) REFERENCES public.caso_auditoria(id);


--
-- Name: revision_caso fk_revision_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.revision_caso
    ADD CONSTRAINT fk_revision_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: revision_caso fk_revision_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.revision_caso
    ADD CONSTRAINT fk_revision_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: rol_permiso fk_rol_permiso_permiso; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol_permiso
    ADD CONSTRAINT fk_rol_permiso_permiso FOREIGN KEY (permiso_id) REFERENCES public.permiso(id);


--
-- Name: rol_permiso fk_rol_permiso_rol; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.rol_permiso
    ADD CONSTRAINT fk_rol_permiso_rol FOREIGN KEY (rol_id) REFERENCES public.rol(id);


--
-- Name: ubicacion_evento fk_ubicacion_evento_area; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ubicacion_evento
    ADD CONSTRAINT fk_ubicacion_evento_area FOREIGN KEY (area_responsable_id) REFERENCES public.area(id);


--
-- Name: ubicacion_evento fk_ubicacion_evento_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ubicacion_evento
    ADD CONSTRAINT fk_ubicacion_evento_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: ubicacion_evento fk_ubicacion_evento_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ubicacion_evento
    ADD CONSTRAINT fk_ubicacion_evento_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: usuario fk_usuario_area; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT fk_usuario_area FOREIGN KEY (area_id) REFERENCES public.area(id);


--
-- Name: usuario fk_usuario_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT fk_usuario_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: usuario fk_usuario_rol; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT fk_usuario_rol FOREIGN KEY (rol_id) REFERENCES public.rol(id);


--
-- Name: usuario fk_usuario_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.usuario
    ADD CONSTRAINT fk_usuario_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: validacion_legacy fk_validacion_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.validacion_legacy
    ADD CONSTRAINT fk_validacion_created_by FOREIGN KEY (created_by) REFERENCES public.usuario(id);


--
-- Name: validacion_legacy fk_validacion_extraccion; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.validacion_legacy
    ADD CONSTRAINT fk_validacion_extraccion FOREIGN KEY (extraccion_id) REFERENCES public.extraccion_legacy(id);


--
-- Name: validacion_legacy fk_validacion_updated_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.validacion_legacy
    ADD CONSTRAINT fk_validacion_updated_by FOREIGN KEY (updated_by) REFERENCES public.usuario(id);


--
-- Name: validacion_legacy fk_validacion_validador; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.validacion_legacy
    ADD CONSTRAINT fk_validacion_validador FOREIGN KEY (validador_id) REFERENCES public.usuario(id);


--
-- Name: lotes_pendientes lotes_pendientes_articulo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lotes_pendientes
    ADD CONSTRAINT lotes_pendientes_articulo_id_fkey FOREIGN KEY (articulo_id) REFERENCES public.activo(id);


--
-- Name: lotes_pendientes lotes_pendientes_lote_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lotes_pendientes
    ADD CONSTRAINT lotes_pendientes_lote_id_fkey FOREIGN KEY (lote_id) REFERENCES public.lotes_carga(id);


--
-- Name: lotes_pendientes lotes_pendientes_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.lotes_pendientes
    ADD CONSTRAINT lotes_pendientes_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: movimiento movimiento_ubicacion_evento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimiento
    ADD CONSTRAINT movimiento_ubicacion_evento_id_fkey FOREIGN KEY (ubicacion_evento_id) REFERENCES public.ubicacion_evento(id);


--
-- Name: movimientos_kardex_archivados movimientos_kardex_archivados_lote_canonico_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex_archivados
    ADD CONSTRAINT movimientos_kardex_archivados_lote_canonico_id_fkey FOREIGN KEY (lote_canonico_id) REFERENCES public.lotes_carga(id);


--
-- Name: movimientos_kardex_archivados movimientos_kardex_archivados_lote_original_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex_archivados
    ADD CONSTRAINT movimientos_kardex_archivados_lote_original_id_fkey FOREIGN KEY (lote_original_id) REFERENCES public.lotes_carga(id);


--
-- Name: movimientos_kardex movimientos_kardex_area_operativa_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex
    ADD CONSTRAINT movimientos_kardex_area_operativa_id_fkey FOREIGN KEY (area_operativa_id) REFERENCES public.area(id);


--
-- Name: movimientos_kardex movimientos_kardex_articulo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex
    ADD CONSTRAINT movimientos_kardex_articulo_id_fkey FOREIGN KEY (articulo_id) REFERENCES public.activo(id) ON DELETE CASCADE;


--
-- Name: movimientos_kardex movimientos_kardex_lote_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.movimientos_kardex
    ADD CONSTRAINT movimientos_kardex_lote_id_fkey FOREIGN KEY (lote_id) REFERENCES public.lotes_carga(id) ON DELETE SET NULL;


--
-- Name: revision_control revision_control_caso_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.revision_control
    ADD CONSTRAINT revision_control_caso_id_fkey FOREIGN KEY (caso_id) REFERENCES public.caso_control(id);


--
-- Name: revision_control revision_control_correccion_movimiento_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.revision_control
    ADD CONSTRAINT revision_control_correccion_movimiento_id_fkey FOREIGN KEY (correccion_movimiento_id) REFERENCES public.movimientos_kardex(id);


--
-- Name: revision_control revision_control_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.revision_control
    ADD CONSTRAINT revision_control_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: sinonimos_area sinonimos_area_area_oficial_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sinonimos_area
    ADD CONSTRAINT sinonimos_area_area_oficial_id_fkey FOREIGN KEY (area_oficial_id) REFERENCES public.catalogo_areas(id);


--
-- Name: solicitudes_carga_kardex solicitudes_carga_kardex_articulo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solicitudes_carga_kardex
    ADD CONSTRAINT solicitudes_carga_kardex_articulo_id_fkey FOREIGN KEY (articulo_id) REFERENCES public.activo(id);


--
-- Name: solicitudes_carga_kardex solicitudes_carga_kardex_lote_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solicitudes_carga_kardex
    ADD CONSTRAINT solicitudes_carga_kardex_lote_id_fkey FOREIGN KEY (lote_id) REFERENCES public.lotes_carga(id);


--
-- Name: solicitudes_carga_kardex solicitudes_carga_kardex_pendiente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solicitudes_carga_kardex
    ADD CONSTRAINT solicitudes_carga_kardex_pendiente_id_fkey FOREIGN KEY (pendiente_id) REFERENCES public.lotes_pendientes(id);


--
-- Name: solicitudes_carga_kardex solicitudes_carga_kardex_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.solicitudes_carga_kardex
    ADD CONSTRAINT solicitudes_carga_kardex_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuario(id);


--
-- Name: tramo_cobertura tramo_cobertura_articulo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tramo_cobertura
    ADD CONSTRAINT tramo_cobertura_articulo_id_fkey FOREIGN KEY (articulo_id) REFERENCES public.activo(id);


--
-- Name: tramo_cobertura tramo_cobertura_revisado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tramo_cobertura
    ADD CONSTRAINT tramo_cobertura_revisado_por_fkey FOREIGN KEY (revisado_por) REFERENCES public.usuario(id);


--
-- Name: transferencia_area transferencia_area_area_destino_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencia_area
    ADD CONSTRAINT transferencia_area_area_destino_id_fkey FOREIGN KEY (area_destino_id) REFERENCES public.area(id);


--
-- Name: transferencia_area transferencia_area_area_origen_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencia_area
    ADD CONSTRAINT transferencia_area_area_origen_id_fkey FOREIGN KEY (area_origen_id) REFERENCES public.area(id);


--
-- Name: transferencia_area transferencia_area_articulo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencia_area
    ADD CONSTRAINT transferencia_area_articulo_id_fkey FOREIGN KEY (articulo_id) REFERENCES public.activo(id);


--
-- Name: transferencia_area transferencia_area_encargado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencia_area
    ADD CONSTRAINT transferencia_area_encargado_id_fkey FOREIGN KEY (encargado_id) REFERENCES public.usuario(id);


--
-- Name: transferencia_area transferencia_area_registrado_por_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.transferencia_area
    ADD CONSTRAINT transferencia_area_registrado_por_fkey FOREIGN KEY (registrado_por) REFERENCES public.usuario(id);


--
-- PostgreSQL database dump complete
--


