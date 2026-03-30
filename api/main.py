from fastapi import FastAPI
from .routers import users, courses, documents
from .database import engine
from . import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Canvas RAG API",
    description="REST API for Canvas RAG project - ITESO",
    version="1.0.0"
)

app.include_router(users.router)
app.include_router(courses.router)
app.include_router(documents.router)

@app.get("/")
def root():
    return {"message": "Canvas RAG API is running"}