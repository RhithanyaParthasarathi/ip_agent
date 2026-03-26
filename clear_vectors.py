import sys
import os

# Add the current directory to sys.path to import from .app
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.vector_store import VectorStoreManager

def clear_vector_store():
    print("Connecting to Qdrant...")
    vsm = VectorStoreManager()
    print(f"Current collection info: {vsm.get_collection_info()}")
    print(f"Deleting collection: {vsm.collection_name}...")
    try:
        vsm.delete_collection()
        print("Collection deleted successfully.")
        print("Re-ensuring collection exists (empty)...")
        vsm._ensure_collection_exists()
        print(f"New collection info: {vsm.get_collection_info()}")
        print("Vector store cleared and reset to 0 chunks.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    clear_vector_store()
