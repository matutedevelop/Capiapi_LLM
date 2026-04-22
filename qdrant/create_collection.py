from qdrant_client.models import Distance, VectorParams, HnswConfigDiff
from config import client, COLLECTION_NAME, VECTOR_SIZE

def create_collection(collection_name: str = COLLECTION_NAME):
    # Check if it already exists
    collections = [c.name for c in client.get_collections().collections]
    if collection_name in collections:
        print(f"Collection '{collection_name}' already exists")
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,   # best for text embeddings
        )
    )
    print(f"Collection '{collection_name}' created")
    print(f"  - Vector dimension: {VECTOR_SIZE}")
    print(f"  - Distance: COSINE")



if __name__ == "__main__":
    create_collection()