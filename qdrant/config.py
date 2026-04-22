from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


client = QdrantClient(url="http://localhost:6333")

# Modelo de embeddings
EMBED_MODEL = "to-be-decided"  


COLLECTION_NAME = "capiapi_vdb"
VECTOR_SIZE = 768 # size of gemini vector