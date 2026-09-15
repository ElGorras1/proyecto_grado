import psycopg2

conn = psycopg2.connect("postgresql://postgres:user@localhost:5432/activos_db")
conn.autocommit = True
cur = conn.cursor()
cur.execute("UPDATE usuario SET email='admin@simonpatino.com' WHERE email='admin@simonpatino.test'")
print("Actualizado admin a admin@simonpatino.com")
