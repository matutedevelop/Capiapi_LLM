# CapiAPI
 
A data engineering project that integrates Canvas LMS with a RAG pipeline to help ITESO students study smarter.
 
---
 
## Architecture
Canvas API → PostgreSQL (Neon) → Debezium CDC → Kafka → ELT Pipeline → Vector DB → LLM
 
---
 
## Stack
- **Database**: Neon (PostgreSQL 17)
- **Auth**: Neon Auth (Better Auth) + JWT
- **Data API**: Neon Data API (PostgREST)
- **Data Lake**: Azure Blob Storage
- **Vector DB**: Qdrant
- **Language**: Python
- **Admin tool**: DBeaver

---
 
## Setup
 
### 1. Clone the repo
```bash
git clone https://github.com/matutedevelop/Capiapi_LLM.git
cd Capiapi_LLM
```
 
### 2. Create virtual environment
```bash
python -m venv venv
.\venv\Scripts\Activate  # Windows
source venv/bin/activate  # Mac/Linux
```
 
### 3. Install dependencies
```bash
pip install -r requirements.txt
```
 
### 4. Configure environment variables
```bash
cp .env.example .env
# Fill in your credentials in .env
```
 
### 5. Initialize database
```bash
python init_db.py
```

### 6. Start the backend API
```bash
uvicorn api.main:app --reload
```

### 7. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

### 8. Start Debezium CDC
```bash
# Create your config file from the example
cp debezium/config/application.properties.example debezium/config/application.properties
# Fill in your Neon credentials in application.properties

# Start Debezium (uvicorn must be running first)
docker compose up debezium
```


---
 
## Project Structure
Capiapi_LLM/
├── api/
│   ├── __init__.py
│   └── main.py                    ← FastAPI backend (auth + CDC endpoints)
├── database/
│   ├── schema.sql
│   └── fix_public_schema_kan_45.sql
├── debezium/
│   ├── config/
│   │   └── application.properties.example  ← CDC connector config template
│   └── data/                      ← Debezium offset storage (auto-generated)
├── datalake_example/
│   ├── prueba_collection.py
│   └── prueba_loadfile.py
├── ETL/
│   └── EXTRACT/
│       └── extract-tools/
│           ├── canvas-downloader/
│           ├── __init__.py
│           └── canvas_downloader.py
├── frontend/
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   └── src/
│       ├── components/
│       │   ├── CapiLogin.jsx      ← Login page
│       │   └── CapiAPI_chat.jsx   ← Chat interface
│       ├── App.jsx
│       ├── App.css
│       ├── main.jsx
│       └── index.css
├── neon_auth/
│   ├── __init__.py
│   ├── auth.py                    ← sign-up, sign-in, get_jwt_token
│   ├── client.py                  ← NeonClient with auto re-auth
│   └── config.py                  ← environment variables
├── qdrant/
│   ├── config.py                  ← Qdrant client & constants
│   └── create_collection.py       ← collection initialization script
├── tests/
│   ├── __init__.py
│   └── canvas_downloader_test.py
├── docker-compose.yml
├── .env.example
├── .gitignore
├── flake.nix
├── init_db.py
├── README.md
├── requirements.txt
└── test_neon.py
 
---
 
## Modules
 
### KAN-9 — Relational Database (Owen Loza)
Relational database built on Neon (PostgreSQL 17).
 
**Tables:**
- `users` — Canvas students with API token for authentication
- `courses` — Canvas course catalog
- `user_courses` — Many-to-many between users and courses
- `documents` — Course files (PDF, PPTX, DOCX, Excel, CSV)
- `sync_logs` — CDC tracking for the RAG pipeline

See [database/schema.sql](database/schema.sql) for full schema.
 
---
 
### KAN-13 — Data API + Authentication (Owen Loza / Juan Arroyo)
Neon Data API (PostgREST) with JWT authentication via Neon Auth.
 
**Authentication flow:**
1. Backend uses `NEON_API_KEY` to call Neon Auth (server-side only, never exposed to users)
2. Neon Auth returns a short-lived JWT
3. JWT is used to query the Data API with RLS applied per user
4. On token expiry (401), `NeonClient` re-authenticates automatically

**Decision log:** Initially implemented FastAPI + SQLAlchemy REST API.
Migrated to Neon Data API as it is the canonical approach for Neon databases,
with built-in JWT auth and no additional server required.
 
---

### KAN-10 — Frontend Demo + Backend Connection (Demien Becerra / Owen Loza)
React + Vite frontend with login page connected to the Python backend.

**Demien Becerra:**
- Built the full React frontend (CapiLogin.jsx, CapiAPI_chat.jsx)
- Implemented Canvas credential form, token persistence to localStorage
- Connected login redirect to chat interface
- Displayed enrolled courses from Canvas (mock data)

**Owen Loza:**
- Created FastAPI backend with `POST /auth/login` endpoint
- Implemented user exists/create logic:
  - If user exists → verifies bcrypt password
  - If user does not exist → creates user with hashed password in DB
- Connected frontend to real backend (`USE_MOCK = false`)

**Login flow:**
1. User submits `{ email, password, canvas_token }` from the frontend
2. Backend checks if user exists in `users` table via Neon Data API
3. If exists → verifies password with bcrypt
4. If not → creates new user with hashed password
5. Returns `{ user, courses }` to frontend
6. Frontend redirects to chat interface

---
 
### KAN-8 — Data Lake Initialization & Setup (Santiago Ayón)
Azure Blob Storage configured as the central data lake for the RAG pipeline.
 
**Two-container architecture:**
- `canvas-bruto` — raw files downloaded from Canvas, organized by subject code and file type
- `canvas-procesado` — all files converted to Markdown, same folder structure as raw

**Key decisions:**
- Files grouped by subject code extracted from the Canvas course name. Multiple groups of the same subject share one folder.

**Environment variables required:**
```env
AZURE_STORAGE_ACCOUNT_NAME=
AZURE_STORAGE_ACCOUNT_KEY=
AZURE_CONTAINER_RAW=canvas-bruto
AZURE_CONTAINER_PROCESSED=canvas-procesado
```

---

### KAN-11 — Vector Database Initialization (Santiago Ayón)
Qdrant set up as the vector database for the RAG pipeline.

**Files:**
- `docker-compose.yml` — runs Qdrant locally with persistent storage
- `qdrant/config.py` — client connection and constants
- `qdrant/create_collection.py` — idempotent collection initialization script

**Collection design:**
- Vector size: `768` — matches Gemini `text-embedding-004` output dimensions
- Distance metric: `COSINE` — standard for text embeddings
- Collections are created dynamically per subject code during ingestion (`MAT101`, `ING202`, etc.)

**How to run:**
```bash
# Start Qdrant
docker compose up -d

# Create collection
python qdrant/create_collection.py

# Verify at
http://localhost:6333/dashboard
```

---

### KAN-53 — Debezium CDC Initialization and Setup (Owen Loza)
Change Data Capture layer using Debezium Server to monitor real-time changes in the Neon PostgreSQL database and forward events to the FastAPI backend.

**Architecture:**
Neon PostgreSQL (WAL) → Debezium Server (Docker) → HTTP POST → FastAPI /debezium/events

**What was configured:**
- Logical replication enabled on Neon (wal_level = logical)
- Publication `debezium_publication` monitoring tables: documents, courses, users
- Replication slot `debezium` using pgoutput plugin
- Dedicated `debezium_role` with replication and SELECT permissions

**Files:**
- `docker-compose.yml` — includes Debezium Server 3.0 container (quay.io/debezium/server:3.0)
- `debezium/config/application.properties.example` — connector configuration template (real config excluded via .gitignore)
- `api/main.py` — includes `POST /debezium/events` endpoint that receives and processes CDC events in the background

**Event format received:**
- `op: c` — INSERT
- `op: u` — UPDATE  
- `op: d` — DELETE
- `after` — new row state
- `before` — previous row state (only PK columns by default)

**Note:** The sync task trigger (download Canvas files → process → upload to Vector DB) is planned for a future KAN. The endpoint currently logs events and includes a TODO hook for that integration.

---
### KAN-67 — Sync Database (Owen Loza)
Canvas course sync pipeline connecting the Canvas API to the Neon PostgreSQL database via the ELT layer.

**What was implemented:**
- `ETL/LOAD/sync.py` — `sync_user(user_id)` reusable function that fetches the user's Canvas courses and syncs them to the `courses` and `user_courses` tables
- `ETL/EXTRACT/canvas_downloader.py` — `CanvasClient` class wrapping the `canvas-downloader` binary with cross-platform support (Linux/Windows via `platform.system()`)
- `api/main.py` — two new endpoints:
  - `POST /sync/{user_id}` — manually triggers `sync_user()` as a background task (called by the Recargar button in the frontend)
  - `GET /users/{user_id}/courses` — returns the user's synced courses via a PostgREST join on `user_courses + courses`
- `frontend/src/components/CapiAPI_chat.jsx` — Recargar button connected to `POST /sync/{user_id}`, courses rendered from `GET /users/{user_id}/courses`

**Sync flow:**
1. User logs in → `sync_user(user_id)` is triggered automatically via the CDC endpoint (Debezium INSERT on users)
2. `CanvasClient` calls the `canvas-downloader` binary with the user's Canvas token
3. Courses are fetched and upserted into `courses` and `user_courses` tables
4. Frontend displays the synced courses via `GET /users/{user_id}/courses`

**Note:** The `canvas-downloader` binary is platform-aware and runs natively on Linux (Docker) and Windows. Document sync (`sync_documents`) is functional on Linux; full end-to-end tested in the Docker environment.

---



