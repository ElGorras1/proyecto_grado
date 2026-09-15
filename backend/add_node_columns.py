import psycopg2

conn = psycopg2.connect("postgresql://postgres:user@localhost:5432/activos_db")
conn.autocommit = True
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE movimientos_kardex ADD COLUMN IF NOT EXISTS nodo_grafo VARCHAR(100);")
    cur.execute("ALTER TABLE movimientos_kardex ADD COLUMN IF NOT EXISTS requiere_auditoria_nodo BOOLEAN DEFAULT FALSE;")
    print("Columnas nodo_grafo y requiere_auditoria_nodo agregadas exitosamente.")
except Exception as e:
    print(f"Error: {e}")
