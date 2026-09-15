import psycopg2

conn = psycopg2.connect("postgresql://postgres:user@localhost:5432/activos_db")
conn.autocommit = True
cur = conn.cursor()

# Get hash from user 4
cur.execute("SELECT password_hash FROM usuario WHERE id=4")
hash_val = cur.fetchone()[0]

# Update user 1
cur.execute("UPDATE usuario SET password_hash=%s WHERE id=1", (hash_val,))

# Delete user 4
cur.execute("DELETE FROM usuario WHERE id=4")

print("Admin password for admin@simonpatino.com updated to CambiarPassword123!")
