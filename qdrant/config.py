from qdrant_client import QdrantClient
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

#client = QdrantClient(url="http://localhost:6333")
client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
model = SentenceTransformer("google/embeddinggemma-300m")

EMBED_MODEL = "gemini-embedding-001"
VECTOR_SIZE = 3072

genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_collection_name(course_code: str) -> str:
    return f"capiapi_{course_code}"

# def get_embedding(text: str) -> list[float]:
#     result = genai_client.models.embed_content(
#         model=EMBED_MODEL,
#         contents=text,
#         config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
#     )
#     return result.embeddings[0].values

def get_embedding(text:str):
    vector = model.encode_document(text)
    return vector
