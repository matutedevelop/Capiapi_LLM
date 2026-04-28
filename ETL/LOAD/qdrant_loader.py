import os
import hashlib
import uuid
import sys
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from qdrant_client.models import PointStruct, VectorParams, Distance

sys.path.append(os.path.join(os.path.dirname(__file__), '../../qdrant'))
from config import client, VECTOR_SIZE, get_collection_name, get_embedding

load_dotenv()


# === AZURE ===

def get_azure_client() -> BlobServiceClient:
    account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    return BlobServiceClient(
        account_url=f"https://{account}.blob.core.windows.net",
        credential=key
    )


# === QDRANT ===

def ensure_collection(course_code: str) -> str:
    """Crea la colección en Qdrant si no existe. Retorna el nombre."""
    collection_name = get_collection_name(course_code)
    existing = [c.name for c in client.get_collections().collections]

    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
        print(f"[CREATED] Colección '{collection_name}' creada")
    else:
        print(f"[EXISTS] Colección '{collection_name}' ya existe")

    return collection_name


def chunk_markdown(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def file_already_loaded(collection_name: str, file_hash: str) -> bool:
    results = client.scroll(
        collection_name=collection_name,
        scroll_filter={
            "must": [{"key": "file_hash", "match": {"value": file_hash}}]
        },
        limit=1
    )
    return len(results[0]) > 0


def load_file_to_qdrant(course_code: str, filename: str, content: str) -> None:
    """
    Recibe el contenido markdown de un archivo ya procesado
    y lo carga a la colección de Qdrant del curso.

    Parámetros:
        course_code: código del curso ej. 'O2024_DEL34E6'
        filename: nombre del archivo ej. 'syllabus.md'
        content: contenido markdown del archivo
    """
    collection_name = ensure_collection(course_code)

    # Verificar duplicado por hash
    file_hash = hashlib.sha256(content.encode()).hexdigest()
    if file_already_loaded(collection_name, file_hash):
        print(f"[SKIP] '{filename}' ya está en Qdrant (hash: {file_hash[:8]}...)")
        return

    # Chunkear y embeddear
    chunks = chunk_markdown(content)
    print(f"[INFO] '{filename}' → {len(chunks)} chunks")

    points = []
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "course_code": course_code,
                "filename": filename,
                "file_hash": file_hash,
                "chunk_index": i,
                "text": chunk,
            }
        ))

    client.upsert(collection_name=collection_name, points=points)
    print(f"[OK] {len(points)} vectores cargados → '{collection_name}'")




def on_new_document(course_code: str, filename: str) -> None:
    """
    Trigger cuando Debezium detecta un nuevo documento en Neon.
    Descarga el .md de canvas-procesado y lo carga a Qdrant.

    Parámetros:
        course_code: código del curso ej. 'O2024_DEL34E6'
        filename: nombre del archivo ej. 'syllabus.md'
    """
    container = os.getenv("AZURE_CONTAINER_PROCESSED")
    blob_path = f"{course_code}/{filename}"

    print(f"[EVENT] Nuevo documento detectado: {blob_path}")

    # Descargar de Azure
    try:
        azure = get_azure_client()
        blob_client = azure.get_container_client(container).get_blob_client(blob_path)
        content = blob_client.download_blob().readall().decode("utf-8")
    except Exception as e:
        print(f"[ERROR] No se pudo descargar '{blob_path}' de Azure: {e}")
        return

    # Cargar a Qdrant
    load_file_to_qdrant(course_code, filename, content)


if __name__ == "__main__":
    # Prueba con un curso
    on_new_document(
        course_code="P2025_MAF1121H2",
        filename="Procedimientos textuales tabla.md"
    )