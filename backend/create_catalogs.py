import psycopg2

conn = psycopg2.connect('postgresql://postgres:user@localhost:5432/activos_db')
cur = conn.cursor()

# 1. Crear tabla catalogo_areas
cur.execute("""
CREATE TABLE IF NOT EXISTS catalogo_areas (
    id SERIAL PRIMARY KEY,
    nombre_oficial VARCHAR(100) UNIQUE NOT NULL,
    abreviatura VARCHAR(30),
    descripcion TEXT,
    tipo VARCHAR(30) DEFAULT 'departamento',
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
""")

# 2. Crear tabla sinonimos_area  
cur.execute("""
CREATE TABLE IF NOT EXISTS sinonimos_area (
    id SERIAL PRIMARY KEY,
    texto_sucio VARCHAR(200) NOT NULL,
    area_oficial_id INTEGER REFERENCES catalogo_areas(id),
    confirmado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(texto_sucio)
);
""")

# 3. Crear tabla catalogo_ferias
cur.execute("""
CREATE TABLE IF NOT EXISTS catalogo_ferias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    ciudad VARCHAR(100),
    activa BOOLEAN DEFAULT TRUE
);
""")

print("Tablas creadas.")

# 4. Semilla de áreas (solo las que tienen +7 usos en los datos escaneados y son claramente reales)
areas_semilla = [
    ("CEDOAL", "CEDOAL", "Centro de Documentación de Arte Latinoamericano", "departamento", True),
    ("Dirección", "DIR", "Dirección General", "departamento", True),
    ("Administración", "ADM", "Área Administrativa", "departamento", True),
    ("Capacitación", "CAP", "Área de Capacitación", "departamento", True),
    ("Galería", "GAL", "Galería de Arte", "departamento", True),
    ("Sala", "SALA", "Sala de Exhibiciones", "departamento", True),
    ("CID", "CID", "Centro de Información y Documentación", "departamento", True),
    ("CEDOC", "CEDOC", "Centro de Documentación", "departamento", True),
    ("C+C", "C+C", "Área de Comics (histórica, cerrada)", "departamento", False),
    ("ESIP", "ESIP", "Espacio Patiño", "departamento", True),
    ("Coordinación Literaria", "COOD.L", "Coordinación del área literaria", "departamento", True),
    # Nodos de tipo operación (no son departamentos)
    ("Ventas", None, "Salida por venta directa o en feria", "operacion", True),
    ("Obsequios y Donaciones", None, "Salida por obsequio o donación", "operacion", True),
    ("Consignación", None, "Salida por consignación", "operacion", True),
    ("Inventario / Compra", None, "Entrada por compra o inventario inicial", "operacion", True),
    ("Baja / Pérdida", None, "Salida por deterioro o extravío", "operacion", True),
]

for nombre, abrev, desc, tipo, activa in areas_semilla:
    cur.execute("""
        INSERT INTO catalogo_areas (nombre_oficial, abreviatura, descripcion, tipo, activa) 
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (nombre_oficial) DO NOTHING
    """, (nombre, abrev, desc, tipo, activa))

print(f"Áreas semilla insertadas.")

# 5. Semilla de sinónimos conocidos (mapa OCR → área oficial)
sinonimos = {
    # CEDOAL y sus variantes OCR
    "CEDODL": "CEDOAL", "CEDOOL": "CEDOAL", "CEDECL": "CEDOAL", "CEDECOL": "CEDOAL",
    "CDD00L": "CEDOAL", "CSD00L": "CEDOAL", "CDOAL": "CEDOAL", "CODOL": "CEDOAL",
    "CROOTL": "CEDOAL",
    # DIR
    "DIR.": "Dirección", "DIRECCIÓN": "Dirección", "DERECCIÓN": "Dirección",
    # ADM
    "ADM.": "Administración", "ADM": "Administración",
    # CAP
    "CAP.": "Capacitación", "CAP": "Capacitación",
    # GALERÍA
    "GALERIA": "Galería", "GALERÍA": "Galería",
    # CID
    "CID": "CID",
    # Coordinación Literaria
    "COOD. L.": "Coordinación Literaria",
    # CEDOC
    "CEDOC": "CEDOC",
    # Ventas
    "VENTAS": "Ventas",
    # C+C
    "C+C": "C+C",
}

for texto_sucio, nombre_oficial in sinonimos.items():
    cur.execute("SELECT id FROM catalogo_areas WHERE nombre_oficial = %s", (nombre_oficial,))
    area = cur.fetchone()
    if area:
        cur.execute("""
            INSERT INTO sinonimos_area (texto_sucio, area_oficial_id, confirmado) 
            VALUES (%s, %s, TRUE)
            ON CONFLICT (texto_sucio) DO NOTHING
        """, (texto_sucio, area[0]))

print(f"Sinónimos insertados.")

# 6. Semilla de ferias
ferias = [
    ("FIL La Paz", "La Paz", True),
    ("FIL Cochabamba", "Cochabamba", True),
    ("FIL Santa Cruz", "Santa Cruz", True),
    ("FIC", "Cochabamba", True),
]

for nombre, ciudad, activa in ferias:
    cur.execute("""
        INSERT INTO catalogo_ferias (nombre, ciudad, activa) 
        VALUES (%s, %s, %s)
        ON CONFLICT (nombre) DO NOTHING
    """, (nombre, ciudad, activa))

print("Ferias insertadas.")

conn.commit()
conn.close()
print("DONE - Catálogo Maestro creado exitosamente.")
