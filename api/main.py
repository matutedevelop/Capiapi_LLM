import bcrypt
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
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

    # 1. Check if user exists
    users = client.select("users", params={
        "email": f"eq.{req.email}",
        "select": "id,email,password,canvas_api_token,created_at"
    })
    print("SELECT RESPONSE:", users)

    if users and isinstance(users, list) and len(users) > 0:
        # User exists — verify password
        user = users[0]
        password_match = bcrypt.checkpw(
            req.password.encode("utf-8"),
            user["password"].encode("utf-8")
        )
        if not password_match:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    else:
        # User does not exist — create new user
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

    # 2. Fetch user courses
    courses = client.select("user_courses", params={"user_id": f"eq.{user['id']}"})

    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
        },
        "courses": courses,
    }


# ── DEBEZIUM CDC ENDPOINT ─────────────────────────────────────────────────────

def process_document_event(payload: dict):
    """
    Background task that processes CDC events from Debezium.
    Currently logs the event — sync task will be implemented in a future KAN.
    """
    try:
        # Debezium HTTP sink sends payload nested under 'payload' key
        value = payload.get("payload", payload)
        
        op = value.get("op")
        source = value.get("source", {})
        table = source.get("table") if source else None
        after = value.get("after")
        before = value.get("before")

        print(f"CDC Event — table: {table}, operation: {op}")
        print(f"  before: {before}")
        print(f"  after: {after}")

        # Only process INSERT/UPDATE on documents table
        if table == "documents" and op in ("c", "u"):
            doc_id = after.get("id") if after else None
            loaded = after.get("loaded") if after else None
            print(f"  Document {doc_id} — loaded: {loaded}")
            # TODO: trigger sync task in future KAN

    except Exception as e:
        print(f"Error processing CDC event: {e}")


@app.post("/debezium/events")
async def debezium_events(request: Request, background_tasks: BackgroundTasks):
    """
    Receives CDC change events from Debezium Server.
    Processes them in the background to avoid blocking Debezium.
    """
    payload = await request.json()
    print(f"Debezium event received: {payload}")
    background_tasks.add_task(process_document_event, payload)
    return {"status": "received"}
