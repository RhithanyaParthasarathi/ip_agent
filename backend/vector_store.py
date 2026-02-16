"""Vector store manager for Qdrant."""
from typing import List, Optional
from langchain_community.vectorstores import Qdrant
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from config import settings


class VectorStoreManager:
    """Manages the Qdrant vector store."""
    
    def __init__(self):
        """Initialize the vector store manager."""
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.google_api_key
        )
        self.collection_name = settings.vector_collection
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            # Get embedding dimension
            sample_embedding = self.embeddings.embed_query("test")
            vector_size = len(sample_embedding)
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
    
    def get_vectorstore(self) -> Qdrant:
        """Get the Qdrant vector store instance."""
        return Qdrant(
            client=self.client,
            collection_name=self.collection_name,
            embeddings=self.embeddings
        )
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store."""
        vectorstore = self.get_vectorstore()
        ids = vectorstore.add_documents(documents)
        return ids
    
    def similarity_search(
        self, 
        query: str, 
        k: int = None
    ) -> List[Document]:
        """Search for similar documents."""
        if k is None:
            k = settings.top_k_results
        
        vectorstore = self.get_vectorstore()
        results = vectorstore.similarity_search(query, k=k)
        return results
    
    def delete_collection(self):
        """Delete the entire collection."""
        self.client.delete_collection(self.collection_name)
    
    def get_collection_info(self) -> dict:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count
            }
        except Exception as e:
            return {"error": str(e)}
