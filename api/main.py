import bcrypt
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from neon_auth.client import NeonClient

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    email: str
    password: str
    canvas_token: str

@app.post("/auth/login")
def login(req: LoginRequest):
    client = NeonClient()

    # 1. Buscar si el usuario existe
    users = client.select("users", params={
        "email": f"eq.{req.email}",
        "select": "id,email,password,canvas_api_token,created_at"
    })
    print("SELECT RESPONSE:", users)

    if users and isinstance(users, list) and len(users) > 0:
        # Usuario existe — verificar password
        user = users[0]
        password_match = bcrypt.checkpw(
            req.password.encode("utf-8"),
            user["password"].encode("utf-8")
        )
        if not password_match:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    else:
        # Usuario no existe — crear
        password_hash = bcrypt.hashpw(
            req.password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        user = client.insert("users", {
            "email": req.email,
            "password": password_hash,
            "canvas_api_token": req.canvas_token,
        })
        print("INSERT RESPONSE:", user)
        if isinstance(user, list):
            user = user[0]

    # 2. Traer cursos del usuario
    courses = client.select("user_courses", params={"user_id": f"eq.{user['id']}"})

    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
        },
        "courses": courses,
    }