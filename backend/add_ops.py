import psycopg2
conn = psycopg2.connect('postgresql://postgres:user@localhost:5432/activos_db')
cur = conn.cursor()

ops = [
    ("Transferencia Interna", "operacion", True),
    ("Salida a Feria", "operacion", True)
]

for nombre, tipo, activa in ops:
    cur.execute("""
        INSERT INTO catalogo_areas (nombre_oficial, tipo, activa) 
        VALUES (%s, %s, %s)
        ON CONFLICT (nombre_oficial) DO NOTHING
    """, (nombre, tipo, activa))

conn.commit()
conn.close()
print("Agregadas Transferencia Interna y Salida a Feria.")
