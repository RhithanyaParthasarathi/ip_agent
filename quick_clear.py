from qdrant_client import QdrantClient

def clear_vstore():
    client = QdrantClient(host="localhost", port=6333)
    collection_name = "company_docs"
    print(f"Deleting collection {collection_name}...")
    try:
        client.delete_collection(collection_name)
        print("Deleted.")
        print("Recreating...")
        from qdrant_client.models import Distance, VectorParams
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE) # Default for HuggingFace
        )
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clear_vstore()
