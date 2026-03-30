from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("/", response_model=list[schemas.DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    return db.query(models.Document).all()

@router.get("/{document_id}", response_model=schemas.DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.get("/course/{course_id}", response_model=list[schemas.DocumentResponse])
def get_documents_by_course(course_id: int, db: Session = Depends(get_db)):
    return db.query(models.Document).filter(models.Document.course_id == course_id).all()

@router.post("/", response_model=schemas.DocumentResponse, status_code=201)
def create_document(document: schemas.DocumentCreate, db: Session = Depends(get_db)):
    db_document = db.query(models.Document).filter(models.Document.canvas_file_id == document.canvas_file_id).first()
    if db_document:
        raise HTTPException(status_code=400, detail="Document already exists")
    new_document = models.Document(**document.model_dump())
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    return new_document

@router.put("/{document_id}", response_model=schemas.DocumentResponse)
def update_document(document_id: int, document: schemas.DocumentCreate, db: Session = Depends(get_db)):
    db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found")
    for key, value in document.model_dump().items():
        setattr(db_document, key, value)
    db.commit()
    db.refresh(db_document)
    return db_document

@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(db_document)
    db.commit()