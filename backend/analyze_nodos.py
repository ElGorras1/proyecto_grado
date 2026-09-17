import psycopg2
conn = psycopg2.connect('postgresql://postgres:user@localhost:5432/activos_db')
cur = conn.cursor()

print("=== TODOS LOS NODOS DISTINTOS ===")
cur.execute("SELECT DISTINCT nodo_grafo, COUNT(*) FROM movimientos_kardex WHERE nodo_grafo IS NOT NULL GROUP BY nodo_grafo ORDER BY nodo_grafo")
for r in cur.fetchall():
    print(f"  [{r[1]:>4} usos] {r[0]}")

print(f"\n=== TOTAL NODOS DISTINTOS: ===")
cur.execute("SELECT COUNT(DISTINCT nodo_grafo) FROM movimientos_kardex WHERE nodo_grafo IS NOT NULL")
print(cur.fetchone()[0])

print("\n=== COLUMNAS del movimiento actual (qué guardamos) ===")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'movimientos_kardex' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  - {r[0]}")
