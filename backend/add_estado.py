import psycopg2
conn = psycopg2.connect('postgresql://postgres:user@localhost:5432/activos_db')
cur = conn.cursor()
cur.execute("ALTER TABLE movimientos_kardex ADD COLUMN IF NOT EXISTS estado VARCHAR(20) DEFAULT 'ACTIVO'")
conn.commit()
print("Columna estado agregada")
