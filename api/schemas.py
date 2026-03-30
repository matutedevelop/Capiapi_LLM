from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: str
    canvas_user_id: int
    canvas_api_token: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Course schemas
class CourseBase(BaseModel):
    canvas_id: int
    code: str
    name: str

class CourseCreate(CourseBase):
    pass

class CourseResponse(CourseBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# UserCourse schemas
class UserCourseBase(BaseModel):
    user_id: int
    course_id: int

class UserCourseCreate(UserCourseBase):
    pass

class UserCourseResponse(UserCourseBase):
    id: int

    class Config:
        from_attributes = True

# Document schemas
class DocumentBase(BaseModel):
    course_id: int
    canvas_file_id: int
    filename: str
    file_type: Optional[str] = None
    file_url: Optional[str] = None
    loaded: Optional[bool] = False

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# SyncLog schemas
class SyncLogBase(BaseModel):
    document_id: int
    status: Optional[str] = "pending"
    error_message: Optional[str] = None

class SyncLogCreate(SyncLogBase):
    pass

class SyncLogResponse(SyncLogBase):
    id: int
    synced_at: datetime

    class Config:
        from_attributes = True