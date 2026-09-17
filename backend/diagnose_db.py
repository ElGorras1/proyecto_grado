import psycopg2
conn = psycopg2.connect('postgresql://postgres:user@localhost:5432/activos_db')
cur = conn.cursor()

print("=== COLUMNAS DE movimientos_kardex ===")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'movimientos_kardex' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(r)

print("\n=== David Crespo - Buscar artículo ===")
cur.execute("SELECT id, nombre FROM activo WHERE nombre ILIKE '%crespo%' OR nombre ILIKE '%david%'")
arts = cur.fetchall()
for a in arts:
    print(a)

if arts:
    art_id = arts[0][0]
    print(f"\n=== Últimos 10 movimientos de artículo {art_id} ===")
    cur.execute("""SELECT id, fecha_movimiento, detalle, ingresos, salidas, saldo_registrado, 
                   lote_id, observaciones, ruta_imagen_respaldo
                   FROM movimientos_kardex 
                   WHERE articulo_id = %s 
                   ORDER BY id DESC LIMIT 10""", (art_id,))
    for r in cur.fetchall():
        print(r)

print("\n=== Contar movimientos con/sin lote_id ===")
cur.execute("SELECT COUNT(*) FROM movimientos_kardex WHERE lote_id IS NOT NULL")
print(f"Con lote (legacy): {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM movimientos_kardex WHERE lote_id IS NULL")
print(f"Sin lote (modernos/otros): {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM movimientos_kardex WHERE detalle LIKE 'Movimiento Actual%'")
print(f"Con 'Movimiento Actual' en detalle: {cur.fetchone()[0]}")
