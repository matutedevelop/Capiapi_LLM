from qdrant_client.models import Distance, VectorParams, HnswConfigDiff
from config import client, VECTOR_SIZE, get_collection_name

COLLECTION_NAME = 'capiapi_vdb'

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

def list_collections():
    collections = client.get_collections().collections
    
    if not collections:
        print("No collections in Qdrant")
        return []
    
    print(f"Collections ({len(collections)}):")
    for c in collections:
        info = client.get_collection(c.name)
        count = info.points_count if info.points_count is not None else 0
        print(f"  - {c.name} | vectors: {count} | dimesion: {info.config.params.vectors.size}")
    return [c.name for c in collections]


if __name__ == "__main__":
    create_collection()
    list_collections()