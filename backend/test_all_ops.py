import requests, json, sys
sys.path.insert(0, '.')
from app.core.security import create_access_token

BASE = 'http://localhost:8000/api/v1'

# Generar token directamente
token = create_access_token(subject=1)  # admin user id=1
headers = {'Authorization': f'Bearer {token}'}
print(f"Token generado OK")

# 1. GET /nodos
r = requests.get(f'{BASE}/kardex/nodos', headers=headers)
print(f"\nGET /nodos: {r.status_code}")
ops = [n for n in r.json() if n['grupo'] == 'Tipo de Operación']
print(f"Operaciones ({len(ops)}):")
for o in ops:
    print(f"  - {o['valor']}")

# 2. Check stock
r = requests.get(f'{BASE}/kardex/articulos', headers=headers)
for a in r.json():
    if 'PRUEBA' in a['nombre']:
        print(f"\nStock PRUEBA: {a['stock_actual']}")

# 3. Ingreso previo para tener stock
print("\n--- Ingreso de 20 unidades ---")
r = requests.post(f'{BASE}/kardex/movimiento-actual', headers=headers, json={
    "articulo_id": 1, "tipo": "ingreso", "cantidad": 20,
    "nodo_grafo": "Inventario / Compra", "tipo_operacion": "Inventario / Compra",
    "observaciones": "Stock para pruebas"
})
print(f"  {r.status_code} -> saldo={r.json().get('saldo_registrado', r.text[:200])}")

# 4. TEST: Ventas
print("\n--- Ventas ---")
r = requests.post(f'{BASE}/kardex/movimiento-actual', headers=headers, json={
    "articulo_id": 1, "tipo": "salida", "cantidad": 2,
    "nodo_grafo": "Ventas", "tipo_operacion": "Ventas",
    "canal_venta": "Venta Directa", "observaciones": "Test venta"
})
print(f"  {r.status_code} -> saldo={r.json().get('saldo_registrado', r.text[:200])}")

# 5. TEST: Transferencia Interna
print("\n--- Transferencia Interna ---")
r = requests.post(f'{BASE}/kardex/movimiento-actual', headers=headers, json={
    "articulo_id": 1, "tipo": "salida", "cantidad": 1,
    "nodo_grafo": "Área: Galería", "tipo_operacion": "Transferencia Interna",
    "receptor": "Juan Pérez", "observaciones": "Test transferencia"
})
print(f"  {r.status_code} -> saldo={r.json().get('saldo_registrado', r.text[:200])}")

# 6. TEST: Salida a Feria
print("\n--- Salida a Feria ---")
r = requests.post(f'{BASE}/kardex/movimiento-actual', headers=headers, json={
    "articulo_id": 1, "tipo": "salida", "cantidad": 3,
    "nodo_grafo": "Feria", "tipo_operacion": "Salida a Feria",
    "feria_id": 2, "ciudad_feria": "Cochabamba", "observaciones": "Test feria"
})
print(f"  {r.status_code} -> saldo={r.json().get('saldo_registrado', r.text[:200])}")

# 7. TEST: Obsequio
print("\n--- Obsequio ---")
r = requests.post(f'{BASE}/kardex/movimiento-actual', headers=headers, json={
    "articulo_id": 1, "tipo": "salida", "cantidad": 2,
    "nodo_grafo": "Obsequios y Donaciones", "tipo_operacion": "Obsequios y Donaciones",
    "receptor": "Colegio San Ignacio", "observaciones": "Test obsequio"
})
print(f"  {r.status_code} -> saldo={r.json().get('saldo_registrado', r.text[:200])}")

# 8. TEST: Baja
print("\n--- Baja ---")
r = requests.post(f'{BASE}/kardex/movimiento-actual', headers=headers, json={
    "articulo_id": 1, "tipo": "salida", "cantidad": 1,
    "nodo_grafo": "Baja / Pérdida", "tipo_operacion": "Baja / Pérdida",
    "motivo_baja": "Deterioro", "observaciones": "Test baja"
})
print(f"  {r.status_code} -> saldo={r.json().get('saldo_registrado', r.text[:200])}")

# 9. TEST: Consignación
print("\n--- Consignación ---")
r = requests.post(f'{BASE}/kardex/movimiento-actual', headers=headers, json={
    "articulo_id": 1, "tipo": "salida", "cantidad": 1,
    "nodo_grafo": "Consignación", "tipo_operacion": "Consignación",
    "receptor": "Librería Central", "observaciones": "Test consignación"
})
print(f"  {r.status_code} -> saldo={r.json().get('saldo_registrado', r.text[:200])}")

# 10. TEST: Stock insuficiente
print("\n--- Stock insuficiente ---")
r = requests.post(f'{BASE}/kardex/movimiento-actual', headers=headers, json={
    "articulo_id": 1, "tipo": "salida", "cantidad": 99999,
    "nodo_grafo": "Ventas", "tipo_operacion": "Ventas",
    "observaciones": "Debe fallar"
})
print(f"  {r.status_code} -> {r.text[:200]}")

# 11. Historial moderno final
print("\n--- HISTORIAL MODERNO ---")
r = requests.get(f'{BASE}/kardex/historial-actual/1', headers=headers)
for m in r.json():
    op = m.get('tipo_operacion') or '-'
    rec = m.get('receptor') or ''
    usr = m.get('usuario_operador') or '-'
    print(f"  {m['fecha_movimiento']} | {op:25s} | ing={str(m.get('ingresos','')):>5s} sal={str(m.get('salidas','')):>5s} | saldo={m['saldo_registrado']:>5} | op={usr} | rec={rec}")
