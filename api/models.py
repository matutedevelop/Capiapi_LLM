from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, UniqueConstraint, ForeignKey
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    canvas_user_id = Column(Integer, unique=True, nullable=False)
    canvas_api_token = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    canvas_id = Column(Integer, unique=True, nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class UserCourse(Base):
    __tablename__ = "user_courses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "course_id"),)

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    canvas_file_id = Column(Integer, unique=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50))
    file_url = Column(Text)
    loaded = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="pending")
    synced_at = Column(TIMESTAMP, server_default=func.now())
    error_message = Column(Text)