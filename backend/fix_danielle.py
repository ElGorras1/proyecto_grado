import psycopg2

conn = psycopg2.connect('postgresql://postgres:user@localhost:5432/activos_db')
cur = conn.cursor()

# Get DANIELLE CAILLET article ID
cur.execute("SELECT id FROM activo WHERE nombre ILIKE '%DANIELLE%'")
activo = cur.fetchone()

if activo:
    art_id = activo[0]
    # Fetch all its movements sorted
    cur.execute("SELECT id, fecha_movimiento, saldo_registrado, ingresos, salidas FROM movimientos_kardex WHERE articulo_id = %s ORDER BY numero_pagina ASC, orden_fila ASC", (art_id,))
    rows = cur.fetchall()
    
    saldo_acumulado = None
    ultima_fecha = None
    
    for row in rows:
        m_id, fecha, saldo_reg, ing, sal = row
        ing = ing or 0
        sal = sal or 0
        
        tiene_error = False
        obs_list = []
        
        if saldo_acumulado is None:
            saldo_esp = (ing - sal) if (ing > 0 or sal > 0) else saldo_reg
        else:
            saldo_esp = saldo_acumulado + ing - sal
            
        if saldo_esp != saldo_reg:
            tiene_error = True
            obs_list.append("Error de consistencia aritmética en saldo físico.")
            
        if ultima_fecha and fecha < ultima_fecha:
            tiene_error = True
            obs_list.append("Error cronológico: La fecha es anterior al registro previo.")
            
        obs_str = " | ".join(obs_list) if obs_list else None
        
        cur.execute("UPDATE movimientos_kardex SET tiene_error_saldo = %s, observaciones = %s, saldo_calculado = %s WHERE id = %s",
                    (tiene_error, obs_str, saldo_esp, m_id))
                    
        saldo_acumulado = saldo_reg
        ultima_fecha = fecha
        
    conn.commit()
    print("Correcciones actualizadas en DB para Danielle Caillet.")
else:
    print("Activo no encontrado.")
