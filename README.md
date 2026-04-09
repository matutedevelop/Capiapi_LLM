# CapiAPI

A data engineering project that integrates Canvas LMS with a RAG pipeline to help ITESO students study smarter.

---

## Architecture

---

## Stack
- **Database**: Neon (PostgreSQL 17)
- **Auth**: Neon Auth (Better Auth) + JWT
- **Data API**: Neon Data API (PostgREST)
- **Language**: Python
- **Admin tool**: DBeaver

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/matutedevelop/DATA_ENGINEERING_PROJECT.git
cd DATA_ENGINEERING_PROJECT
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

---

## Project Structure

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

**Decision log:** Initially implemented FastAPI + SQLAlchemy REST API.
Migrated to Neon Data API as it is the canonical approach for Neon databases,
with built-in JWT auth and no additional server required.

---