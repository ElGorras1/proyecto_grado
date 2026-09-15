import psycopg2
conn = psycopg2.connect('postgresql://postgres:user@localhost:5432/activos_db')
cur = conn.cursor()
cur.execute("SELECT id FROM activo WHERE nombre ILIKE '%DANIELLE%'")
activo = cur.fetchone()
if activo:
    print(f"ID: {activo[0]}")
    cur.execute("SELECT id, fecha_movimiento, detalle, ingresos, salidas, saldo_registrado, saldo_calculado, tiene_error_saldo, numero_pagina, orden_fila FROM movimientos_kardex WHERE articulo_id = %s ORDER BY numero_pagina ASC, orden_fila ASC LIMIT 10", (activo[0],))
    for row in cur.fetchall():
        print(row)
else:
    print("No encontrado")
