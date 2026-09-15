import requests

def test_login(email, password):
    r = requests.post("http://localhost:8000/api/v1/auth/login", json={"email": email, "password": password})
    print(f"{email}: {r.status_code} - {r.text}")

print("Testing admin@simonpatino.test")
test_login("admin@simonpatino.test", "CambiarPassword123!")

print("Testing operador@simonpatino.com")
test_login("operador@simonpatino.com", "DemoPassword123!")
