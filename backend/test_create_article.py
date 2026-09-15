from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

print("Creando artículo...")
r = client.post("/api/v1/kardex/articulos", json={"nombre": "PRUEBA " + str(uuid.uuid4())[:6]})
print(r.status_code, r.text)

print("Listando artículos...")
r = client.get("/api/v1/kardex/articulos")
print(r.status_code, r.text)
