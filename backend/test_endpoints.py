import requests, json

r = requests.get('http://localhost:8000/api/v1/kardex/nodos')
print(f"Status: {r.status_code}")
data = r.json()
print(f"Total nodos: {len(data)}")
for d in data:
    print(f"  grupo={d['grupo']}, valor={d['valor']}")

print("\n--- Ferias ---")
r2 = requests.get('http://localhost:8000/api/v1/kardex/ferias')
print(f"Status: {r2.status_code}")
print(json.dumps(r2.json(), indent=2, ensure_ascii=False))

# Simular una transacción para ver si el POST funciona
print("\n--- Test POST /movimiento-actual (sin auth) ---")
r3 = requests.post('http://localhost:8000/api/v1/kardex/movimiento-actual', json={
    "articulo_id": 1,
    "tipo": "salida",
    "cantidad": 1,
    "nodo_grafo": "Ventas",
    "tipo_operacion": "Ventas",
    "canal_venta": "Venta Directa",
    "observaciones": "test"
})
print(f"Status: {r3.status_code}")
print(r3.text[:500])
