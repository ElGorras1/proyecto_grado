import psycopg2

conn = psycopg2.connect("postgresql://postgres:user@localhost:5432/activos_db")
cur = conn.cursor()
cur.execute("SELECT id, email, estado, password_hash FROM usuario")
for row in cur.fetchall():
    print(row)
