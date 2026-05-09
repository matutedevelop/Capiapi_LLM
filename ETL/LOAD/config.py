from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
model = SentenceTransformer("google/embeddinggemma-300m")

#EMBED_MODEL = "gemini-embedding-001"
VECTOR_SIZE = 768



def get_collection_name(course_code: str) -> str:
    return f"capiapi_{course_code}"




def get_embedding(text: str, is_query: bool):
    if is_query:

        vector = model.encode_query(text)

    else:
        vector = model.encode_document(text)

    return vector
