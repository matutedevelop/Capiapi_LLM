import bcrypt
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from neon_auth.client import NeonClient
from ETL.LOAD.upload import upload_file
from ETL.TRANSFORM.pdf_to_md import process_pdf_blob

import os
import dotenv
from ETL.LOAD.sync import sync_user
from ETL.LOAD.qdrant_query import ask

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
    canvas_token: str = ""


@app.post("/auth/login")
def login(req: LoginRequest):
    client = NeonClient()

    # 1. Check if user exists
    users = client.select(
        "users",
        params={
            "email": f"eq.{req.email}",
            "select": "id,email,password,canvas_api_token,created_at",
        },
    )
    print("SELECT RESPONSE:", users)

    if users and isinstance(users, list) and len(users) > 0:
        # User exists — verify password
        user = users[0]
        password_match = bcrypt.checkpw(
            req.password.encode("utf-8"), user["password"].encode("utf-8")
        )
        if not password_match:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    else:
        # User does not exist — canvas token required
        if not req.canvas_token or not req.canvas_token.strip():
            raise HTTPException(
                status_code=428,
                detail={"needs_canvas_token": True, "message": "Canvas token required for new users"}
            )

        # Create new user
        password_hash = bcrypt.hashpw(
            req.password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        user = client.insert(
            "users",
            {
                "email": req.email,
                "password": password_hash,
                "canvas_api_token": req.canvas_token,
            },
        )
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
    Triggers sync_user() when a new user INSERT is detected.
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

        # New user detected — trigger sync
        if table == "users" and op == "c":
            user_id = after.get("id") if after else None
            if user_id:
                print(f"  New user detected (id={user_id}), triggering sync...")
                sync_user(user_id)

        # Document inserted or updated
        if table == "documents" and op in ("c", "u"):
            doc_id = after.get("id") if after else None
            loaded = after.get("loaded") if after else None
            filename = after.get("filename") if after else None
            course_code = after.get("course_code") if after else None
            print(f"  Document {doc_id} — loaded: {loaded}")
            # TODO: trigger document processing pipeline in future KAN

            # if filename and course_code and not loaded:
                # on_new_document(course_code, filename) this is after parsing - load a file to the vdb

            # =<><><><><><><><><<><><><><><><><><><

            dotenv.load_dotenv()
            ac = NeonClient()
            raw_container = os.getenv("AZURE_CONTAINER_RAW")
            canvas_api = os.getenv("CANVAS_API_TOKEN")
            course_code = ac.select(
                "courses", params={"id": f"eq.{after.get('course_id')}"}
            )[0]["code"]

            blob_name = f"{raw_container}/{course_code}/{after.get('filename')}"

            upload_file(
                ac=ac,
                container_name=raw_container,
                file_name=after.get("filename"),
                file_url=after.get("file_url"),
                course_code=course_code,
                file_type=after.get("file_type"),
                canvas_api=canvas_api,
            )

            process_pdf_blob(blob_name)


            ac.update("documents", data={"loaded": True}, params={"id": f"eq.{doc_id}"})

            # =<><><><><><><><><<><><><><><><><><><

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

# ── SYNC + COURSES ENDPOINTS ──────────────────────────────────────────────────

@app.post("/sync/{user_id}")
async def trigger_sync(user_id: int, background_tasks: BackgroundTasks):
    """
    Triggers a full sync for a given user.
    Called by the frontend Recargar button.
    """
    background_tasks.add_task(sync_user, user_id)
    return {"status": "sync started", "user_id": user_id}


@app.get("/users/{user_id}/courses")
def get_user_courses(user_id: int):
    """
    Returns the courses for a given user from Neon DB.
    Uses PostgREST join to fetch course details in a single query.
    """
    client = NeonClient()
    result = client.select("user_courses", params={
        "user_id": f"eq.{user_id}",
        "select": "course_id,courses(id,code,name)"
    })
    courses = [item["courses"] for item in result if item.get("courses")]
    return {"courses": courses}


# ── QDRANT QUERY ──────────────────────────────────────────────────

class ChatRequest(BaseModel):
    course_code: str
    course_name: str
    question: str

@app.post("/chat")
def chat(req: ChatRequest):
    def generate():
        for chunk in ask(req.course_code, req.course_name, req.question):
            yield chunk
    return StreamingResponse(generate(), media_type="text/plain")