import psycopg2
conn = psycopg2.connect('postgresql://postgres:user@localhost:5432/activos_db')
cur = conn.cursor()

# 1. Buscar el artículo
print("=== ARTÍCULO ===")
cur.execute("SELECT id, nombre, codigo FROM activo WHERE codigo ILIKE '%E91159%' OR nombre ILIKE '%PRUEBA%'")
arts = cur.fetchall()
for a in arts:
    print(a)

if arts:
    art_id = arts[0][0]
    # 2. Movimientos
    print(f"\n=== MOVIMIENTOS de artículo {art_id} ===")
    cur.execute("SELECT id, fecha_movimiento, detalle, ingresos, salidas, saldo_registrado, lote_id FROM movimientos_kardex WHERE articulo_id = %s ORDER BY id", (art_id,))
    for r in cur.fetchall():
        print(r)

# 3. Catálogo de áreas (lo que devuelve /nodos)
print("\n=== CATÁLOGO DE ÁREAS (activas) ===")
cur.execute("SELECT id, nombre_oficial, tipo, activa FROM catalogo_areas WHERE activa = TRUE ORDER BY tipo, nombre_oficial")
for r in cur.fetchall():
    print(r)

# 4. Ferias
print("\n=== FERIAS ===")
cur.execute("SELECT id, nombre, ciudad FROM catalogo_ferias WHERE activa = TRUE")
for r in cur.fetchall():
    print(r)

conn.close()
