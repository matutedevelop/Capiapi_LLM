# CapiAPI

A data engineering project that integrates Canvas LMS with a RAG pipeline to help ITESO students study smarter.

---

## Architecture
Canvas API → PostgreSQL (Neon) → ETL Pipeline (Azure Blob → parse MD → chunking → embedding) → Qdrant (Vector DB) → Gemini (LLM) → Frontend

---

## Stack
- **Database**: Neon (PostgreSQL 17)
- **Auth**: Neon Auth (Better Auth) + JWT
- **Data API**: Neon Data API (PostgREST)
- **Data Lake**: Azure Blob Storage
- **Vector DB**: Qdrant
- **LLM**: Gemini (text-embedding-004 + gemini-1.5-flash)
- **Frontend**: React + Vite
- **Backend**: FastAPI
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

### 6. Start Qdrant
```bash
docker compose up -d
```

### 7. Start the backend API
```bash
uvicorn api.main:app --reload
```

### 8. Start the frontend
```bash
cd frontend
npm install
npm run dev
```

---
 
## Project Structure
```
Capiapi_LLM/
├── api/
│   ├── __init__.py
│   └── main.py                        ← FastAPI backend (auth + sync + chat endpoints)
├── database/
│   ├── schema.sql
│   └── fix_public_schema_kan_45.sql
├── ETL/
│   ├── EXTRACT/
│   │   └── extract-tools/
│   │       ├── canvas-downloader/
│   │       ├── __init__.py
│   │       └── canvas_downloader.py   ← CanvasClient wrapping the canvas-downloader binary
│   ├── LOAD/
│   │   ├── config.py
│   │   ├── qdrant_loader.py           ← chunking, embedding, and upload to Qdrant
│   │   ├── qdrant_query.py            ← RAG query against Qdrant + Gemini
│   │   ├── sync.py                    ← sync_user() — courses and documents sync
│   │   ├── upload.py                  ← upload files to Azure Blob Storage
│   │   └── user_pipeline.py           ← full pipeline orchestrator
│   └── TRANSFORM/
│       └── pdf_to_md.py               ← PDF/DOCX → Markdown via docling
├── frontend/
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   └── src/
│       ├── components/
│       │   ├── CapiLogin.jsx          ← Login page
│       │   └── CapiAPI_chat.jsx       ← Chat interface + Recargar button
│       ├── App.jsx
│       ├── App.css
│       ├── main.jsx
│       └── index.css
├── neon_auth/
│   ├── __init__.py
│   ├── auth.py                        ← sign-up, sign-in, get_jwt_token
│   ├── client.py                      ← NeonClient with auto re-auth on 401
│   └── config.py                      ← environment variables
├── qdrant/
│   ├── config.py                      ← Qdrant client & constants
│   └── create_collection.py           ← collection initialization script
├── tests/
│   ├── __init__.py
│   └── canvas_downloader_test.py
├── docker-compose.yml
├── .env.example
├── .gitignore
├── init_db.py
├── README.md
└── requirements.txt
```
 
---
 
## Modules

### KAN-9 — Relational Database (Owen Loza)
Relational database built on Neon (PostgreSQL 17).

**Tables:**
- `users` — Canvas students with API token for authentication
- `courses` — Canvas course catalog
- `user_courses` — Many-to-many between users and courses
- `documents` — Course files (PDF, PPTX, DOCX, Excel, CSV)
- `sync_logs` — pipeline sync tracking

See [database/schema.sql](database/schema.sql) for full schema.

---

### KAN-13 — Data API + Authentication (Owen Loza / Juan Arroyo)
Neon Data API (PostgREST) with JWT authentication via Neon Auth.

**Authentication flow:**
1. Backend uses `NEON_API_KEY` to call Neon Auth (server-side only, never exposed to users)
2. Neon Auth returns a short-lived JWT
3. JWT is used to query the Data API with RLS applied per user
4. On token expiry (401), `NeonClient` re-authenticates automatically

**Decision log:** Initially implemented FastAPI + SQLAlchemy REST API. Migrated to Neon Data API as it is the canonical approach for Neon databases, with built-in JWT auth and no additional server required.
 
---

### KAN-10 — Frontend Demo + Backend Connection (Demien Becerra / Owen Loza)
React + Vite frontend with login page connected to the Python backend.

**Demien Becerra:**
- Built the full React frontend (CapiLogin.jsx, CapiAPI_chat.jsx)
- Implemented Canvas credential form, token persistence to localStorage
- Connected login redirect to chat interface
- Displayed enrolled courses from Canvas

**Owen Loza:**
- Created FastAPI backend with `POST /auth/login` endpoint
- Implemented user exists/create logic:
  - If user exists → verifies bcrypt password
  - If user does not exist → creates user with hashed password in DB
- Connected frontend to real backend

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
### KAN-72 — Logout / Reload (Demien Becerra)
Frontend improvements adding logout functionality and the Recargar button to trigger the sync pipeline.

**What was implemented:**
- `frontend/src/components/CapiAPI_chat.jsx` — added "Recargar" button that calls `POST /sync/{user_id}` to trigger the full pipeline, and logout button that clears the session and redirects to the login page
- Token and user session cleanup on logout via localStorage clear

**Flow:**
1. User clicks "Recargar" → `POST /sync/{user_id}` is called → full pipeline runs in background
2. Courses are refreshed from `GET /users/{user_id}/courses` after sync
3. User clicks "Logout" → session is cleared → redirected to login

---

### KAN-67 — Sync & Full Pipeline (Owen Loza / Juan Arroyo)
Full pipeline connecting Canvas API to Neon, Azure Blob Storage, Qdrant, and Gemini.

**What was implemented:**
- `ETL/LOAD/sync.py` — `sync_user()` fetches the user's Canvas courses and documents and syncs them to Neon
- `ETL/EXTRACT/canvas_downloader.py` — `CanvasClient` class wrapping the `canvas-downloader` binary
- `ETL/TRANSFORM/pdf_to_md.py` — converts raw files to Markdown using `docling`, in parallel via `ThreadPoolExecutor`
- `ETL/LOAD/qdrant_loader.py` — chunks Markdown content, generates embeddings with Gemini `text-embedding-004`, and uploads to Qdrant
- `ETL/LOAD/qdrant_query.py` — RAG query: embeds the user's question, retrieves relevant chunks from Qdrant, and streams a response from `gemini-1.5-flash`
- `ETL/LOAD/user_pipeline.py` — orchestrates the full pipeline end-to-end
- `api/main.py` — exposes:
  - `POST /auth/login` — authentication
  - `POST /sync/{user_id}` — triggers the full pipeline as a background task
  - `GET /users/{user_id}/courses` — returns synced courses
  - `POST /chat` — streams RAG response to the frontend

**Pipeline flow:**
1. User clicks "Recargar" in the frontend → `POST /sync/{user_id}` is called
2. `sync_user()` fetches courses and documents from Canvas and syncs them to Neon
3. Raw files are downloaded and uploaded to `canvas-bruto` in Azure Blob Storage
4. Files are converted to Markdown and uploaded to `canvas-procesado`
5. Markdown content is chunked, embedded, and indexed in Qdrant
6. User asks a question → `POST /chat` retrieves relevant chunks and streams a Gemini response

---

### KAN-64 — Vector Database Query (Santiago Ayón)
RAG query pipeline connecting Qdrant and Gemini to generate contextualized responses.

**What was implemented:**
- `ETL/LOAD/qdrant_query.py` — embeds the user's question using Gemini `text-embedding-004`, retrieves the most relevant chunks from the corresponding Qdrant collection, builds a contextualized prompt, and streams the response from `gemini-1.5-flash`
- `api/main.py` — `POST /chat` endpoint that receives `{ course_code, course_name, question }` and returns a streaming plain-text response

**Query flow:**
1. User sends a question from the frontend with the selected course
2. The question is embedded using Gemini `text-embedding-004`
3. The top relevant chunks are retrieved from the course's Qdrant collection
4. A prompt is built with the retrieved context and sent to `gemini-1.5-flash`
5. The response is streamed back to the frontend

---

### KAN-77 — Dockerize Everything (Juan Arroyo)
Full containerization of the CapiAPI stack using Docker and docker-compose.

**What was implemented:**
- `Dockerfile` — builds the Python backend image including all dependencies and the `canvas-downloader` binary
- `docker-compose.yml` — orchestrates all services: FastAPI backend, Qdrant, and any auxiliary containers
- `.dockerignore` — excludes unnecessary files from the build context

**Key decisions:**
- The `canvas-downloader` binary is bundled directly into the Docker image to ensure consistent behavior across environments
- Qdrant runs as a separate service with persistent volume storage
- Environment variables are injected via `.env` file at runtime

**How to run:**
```bash
docker compose up --build
```

---

### KAN-65 — PDF → MD Docling Pipeline (Juan Arroyo)
Transformation pipeline that converts raw course files from Azure Blob Storage into Markdown using `docling`.

**What was implemented:**
- `ETL/TRANSFORM/pdf_to_md.py` — full pipeline that downloads raw files from `canvas-bruto`, converts them to Markdown, and uploads the result to `canvas-procesado`
- `process_pdf_blob()` — single file processing: download → convert → upload
- `process_pdf_blobs_parallel()` — parallel processing of multiple files using `ThreadPoolExecutor`
- Confidence score calculation per document to assess conversion quality

**Transformation flow:**
1. Raw file is downloaded from `canvas-bruto` in Azure Blob Storage
2. File is converted to Markdown using `docling`'s `DocumentConverter`
3. A confidence score is calculated based on element-level OCR confidence
4. The resulting `.md` file is uploaded to `canvas-procesado` under the same course folder structure

---

### KAN-43 — Datalake Actualization Pipeline (Juan Arroyo)
Pipeline that keeps Azure Blob Storage in sync with the latest course files from Canvas.

**What was implemented:**
- `ETL/LOAD/upload.py` — downloads files from Canvas using the file's download URL and uploads them to `canvas-bruto` in Azure Blob Storage, organized by course code and file type
- `ETL/LOAD/user_pipeline.py` — orchestrates the full actualization flow: sync Neon → download from Canvas → upload to Azure → transform to Markdown → index in Qdrant
- Deduplication logic using SHA-256 hashes to avoid re-processing files that haven't changed

**Pipeline flow:**
1. Documents are synced from Canvas to Neon via `sync_documents()`
2. New or updated files are downloaded from Canvas using their download URL
3. Files are uploaded to `canvas-bruto` organized as `{course_code}/{file_type}/{filename}`
4. Pipeline hands off to the transformation stage (`pdf_to_md.py`)

---

### KAN-55 — Local LLM Request Endpoint (Juan Arroyo)
FastAPI endpoint that handles RAG queries from the frontend and streams Gemini responses.

**What was implemented:**
- `api/main.py` — `POST /chat` endpoint that receives `{ course_code, course_name, question }` from the frontend and returns a streaming plain-text response
- `ETL/LOAD/qdrant_query.py` — `ask()` function that orchestrates the full RAG query: embed → retrieve → prompt → stream
- Streaming response via FastAPI's `StreamingResponse` with `media_type="text/plain"` for real-time output in the frontend

**Request flow:**
1. Frontend sends `{ course_code, course_name, question }` to `POST /chat`
2. `ask()` embeds the question using Gemini `text-embedding-004`
3. Top relevant chunks are retrieved from the course's Qdrant collection
4. A contextualized prompt is built and sent to `gemini-1.5-flash`
5. The response is streamed chunk by chunk back to the frontend

---




