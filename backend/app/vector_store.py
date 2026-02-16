"""Vector store manager for Qdrant."""
import time
from typing import List, Optional
from langchain_qdrant import QdrantVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, MatchValue, MatchAny, FilterSelector
from .config import settings


class VectorStoreManager:
    """Manages the Qdrant vector store."""
    
    def __init__(self):
        """Initialize the vector store manager."""
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.google_api_key
        )
        self.collection_name = settings.vector_collection
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            sample_embedding = self.embeddings.embed_query("test")
            vector_size = len(sample_embedding)
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
    
    def get_vectorstore(self) -> QdrantVectorStore:
        """Get the Qdrant vector store instance."""
        return QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings
        )
    
    def add_documents(self, documents: List[Document], conversation_id: str = None) -> List[str]:
        """Add documents in small batches with retry to avoid SSL errors."""
        if conversation_id:
            for doc in documents:
                doc.metadata["conversation_id"] = conversation_id
        
        vectorstore = self.get_vectorstore()
        all_ids = []
        batch_size = 5
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            for attempt in range(3):
                try:
                    ids = vectorstore.add_documents(batch)
                    all_ids.extend(ids)
                    break
                except Exception as e:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                    else:
                        raise e
            # Small delay between batches to avoid rate limits
            if i + batch_size < len(documents):
                time.sleep(1)
        
        return all_ids
    
    def similarity_search(
        self, 
        query: str, 
        k: int = None,
        conversation_id: str = None,
        selected_sources: List[str] = None
    ) -> List[Document]:
        """Search for similar documents with optional filtering."""
        if k is None:
            k = settings.top_k_results
        
        must_conditions = []
        if conversation_id:
            must_conditions.append(
                FieldCondition(key="metadata.conversation_id", match=MatchValue(value=conversation_id))
            )
        if selected_sources:
            must_conditions.append(
                FieldCondition(key="metadata.source", match=MatchAny(any=selected_sources))
            )
        
        qdrant_filter = Filter(must=must_conditions) if must_conditions else None
        
        vectorstore = self.get_vectorstore()
        if qdrant_filter:
            results = vectorstore.similarity_search(query, k=k, filter=qdrant_filter)
        else:
            results = vectorstore.similarity_search(query, k=k)
        return results
    
    def get_sources_for_conversation(self, conversation_id: str) -> List[dict]:
        """Get unique source names and chunk counts for a conversation."""
        qdrant_filter = Filter(
            must=[
                FieldCondition(key="metadata.conversation_id", match=MatchValue(value=conversation_id))
            ]
        )
        
        sources = {}
        offset = None
        while True:
            results, next_offset = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=qdrant_filter,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            for point in results:
                source_name = point.payload.get("metadata", {}).get("source", "unknown")
                if source_name not in sources:
                    sources[source_name] = {"name": source_name, "chunks": 0}
                sources[source_name]["chunks"] += 1
            
            if next_offset is None:
                break
            offset = next_offset
        
        return list(sources.values())
    
    def delete_source(self, conversation_id: str, source_name: str) -> int:
        """Delete all chunks for a specific source in a conversation."""
        qdrant_filter = Filter(
            must=[
                FieldCondition(key="metadata.conversation_id", match=MatchValue(value=conversation_id)),
                FieldCondition(key="metadata.source", match=MatchValue(value=source_name))
            ]
        )
        
        count = self.client.count(
            collection_name=self.collection_name,
            count_filter=qdrant_filter
        ).count
        
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(filter=qdrant_filter)
        )
        
        return count
    
    def delete_collection(self):
        """Delete the entire collection."""
        self.client.delete_collection(self.collection_name)
    
    def get_collection_info(self) -> dict:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": getattr(info, 'vectors_count', None) or info.points_count,
                "points_count": info.points_count
            }
        except Exception as e:
            return {"error": str(e)}
