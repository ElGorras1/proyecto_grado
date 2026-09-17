import psycopg2
conn = psycopg2.connect('postgresql://postgres:user@localhost:5432/activos_db')
cur = conn.cursor()

# Eliminar el movimiento erróneo de prueba
cur.execute("DELETE FROM movimientos_kardex WHERE id = 1151")
print(f"Eliminados: {cur.rowcount} registros erróneos")

conn.commit()
conn.close()
print("Limpieza completada.")
