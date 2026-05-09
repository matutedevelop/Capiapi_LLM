import os
import hashlib
import uuid
import sys
import re
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from qdrant_client.models import PointStruct, VectorParams, Distance

from config import client, VECTOR_SIZE, get_collection_name, get_embedding

load_dotenv()


# AZURE

def get_azure_client() -> BlobServiceClient:
    account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    return BlobServiceClient(
        account_url=f"https://{account}.blob.core.windows.net",
        credential=key
    )


# QDRANT

def ensure_collection(course_code: str) -> str:
    """Create the collection in Qdrant if it does not exist. Return the name."""
    
    collection_name = get_collection_name(course_code)
    existing = [c.name for c in client.get_collections().collections]

    if collection_name not in existing:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
        print(f"[CREATED] Collection '{collection_name}' created")
    else:
        print(f"[EXISTS] Collection '{collection_name}' already exists")

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
    Receives the Markdown content from a pre-processed file
    and uploads it to the course's Qdrant collection.
    Parameters:
        course_code: course code, e.g., 'O2024_DEL34E6'
        filename: file name, e.g., 'syllabus.md'
        content: Markdown content of the file
    """
    collection_name = ensure_collection(course_code)

    # Check for duplicates using a hash
    file_hash = hashlib.sha256(content.encode()).hexdigest()
    if file_already_loaded(collection_name, file_hash):
        print(f"[SKIP] '{filename}' it's already on Qdrant (hash: {file_hash[:8]}...)")
        return

    # Chunking and embedding
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
    print(f"[OK] {len(points)} vectors uploaded → '{collection_name}'")




def on_new_document(course_code: str, filename: str) -> None:
    """
    Triggered when Debezium detects a new document in Neon.
    Downloads the .md file from canvas-procesado and uploads it to Qdrant.

    Parameters:
        course_code: course code, e.g., 'O2024_DEL34E6'
        filename: file name, e.g., 'syllabus.md'
    """

    filename_md = re.sub(r'\.[^.]+$', '.md', filename)

    container = os.getenv("AZURE_CONTAINER_PROCESSED")
    blob_path = f"{course_code}/.md/{filename_md}"

    print(f"[EVENT] New document detected: {blob_path}")

    # download from Azure
    try:
        azure = get_azure_client()
        blob_client = azure.get_container_client(container).get_blob_client(blob_path)
        content = blob_client.download_blob().readall().decode("utf-8")
    except Exception as e:
        print(f"[ERROR] '{blob_path}' could not be downloaded from Azure: {e}")
        return

    # load to Qdrant
    load_file_to_qdrant(course_code, filename_md, content)


if __name__ == "__main__":
    
    on_new_document(
        course_code="P2025_MAF1121H2",
        filename="pip + nix template.md"
    )