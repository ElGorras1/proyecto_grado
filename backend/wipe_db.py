import psycopg2

conn = psycopg2.connect("postgresql://postgres:user@localhost:5432/activos_db")
conn.autocommit = True
cur = conn.cursor()

try:
    cur.execute("TRUNCATE TABLE movimientos_kardex, lotes_carga, movimiento, existencia, activo, categoria_activo RESTART IDENTITY CASCADE;")
    print("Datos limpiados exitosamente. Comenzamos desde cero.")
except Exception as e:
    print(f"Error: {e}")
