import psycopg2
conn = psycopg2.connect("postgresql://postgres:user@localhost:5432/activos_db")
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
for row in cur.fetchall():
    print(row[0])
