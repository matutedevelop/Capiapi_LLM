from neon_auth.auth import sign_up, get_jwt_token
from neon_auth.client import NeonClient

# Paso 1: Crear usuario (solo la primera vez)
# print("=== SIGN UP ===")
# sign_up()

# Paso 2: Obtener JWT token
print("=== SIGN IN ===")
token = get_jwt_token()
print(f"Token: {token[:50]}..." if token else "No token")

# Paso 3: Hacer query a la DB
print("\n=== SELECT USERS ===")
client = NeonClient()
users = client.select("users")
print(users)
