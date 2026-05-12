-- Canvas RAG - Database Schema
-- KAN-9: Relational database initialization and schema setup

-- 1. Users
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    canvas_user_id  INTEGER UNIQUE NOT NULL,
    canvas_api_token TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 2. Courses
CREATE TABLE IF NOT EXISTS courses (
    id          SERIAL PRIMARY KEY,
    canvas_id   INTEGER UNIQUE NOT NULL,
    code        VARCHAR(50) NOT NULL,
    name        VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 3. User-Courses (many to many)
CREATE TABLE IF NOT EXISTS user_courses (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
    course_id   INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    UNIQUE(user_id, course_id)
);

-- 4. Documents
CREATE TABLE IF NOT EXISTS documents (
    id              SERIAL PRIMARY KEY,
    course_id       INTEGER REFERENCES courses(id) ON DELETE CASCADE,
    canvas_file_id  INTEGER UNIQUE NOT NULL,
    filename        VARCHAR(255) NOT NULL,
    file_type       VARCHAR(50),
    file_url        TEXT,
    loaded          BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 5. Sync logs (for Debezium CDC)
CREATE TABLE IF NOT EXISTS sync_logs (
    id              SERIAL PRIMARY KEY,
    document_id     INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    status          VARCHAR(50) DEFAULT 'pending',
    synced_at       TIMESTAMP DEFAULT NOW(),
    error_message   TEXT
);
