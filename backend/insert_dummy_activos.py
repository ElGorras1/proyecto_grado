import psycopg2
conn = psycopg2.connect("postgresql://postgres:user@localhost:5432/activos_db")
conn.autocommit = True
cur = conn.cursor()
try:
    cur.execute("INSERT INTO categoria_activo (nombre, descripcion) VALUES ('Herramientas', 'Test') ON CONFLICT DO NOTHING RETURNING id")
    row = cur.fetchone()
    cat_id = row[0] if row else 1
except Exception:
    cat_id = 1

try:
    cur.execute(f"INSERT INTO activo (categoria_id, codigo, nombre) VALUES ({cat_id}, 'H-001', 'MARTILLO INDUSTRIAL') ON CONFLICT DO NOTHING")
    cur.execute(f"INSERT INTO activo (categoria_id, codigo, nombre) VALUES ({cat_id}, 'H-002', 'MUSICA CHAPACA CD') ON CONFLICT DO NOTHING")
    print("Dummy activos creados.")
except Exception as e:
    print(f"Error: {e}")
