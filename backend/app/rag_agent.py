"""RAG Agent orchestrating the retrieval and generation."""
import time
from typing import List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from .vector_store import VectorStoreManager
from .document_processor import DocumentProcessor
from .config import settings

MAX_RETRIES = 3


class RAGAgent:
    """RAG Agent with retrieval and generation capabilities."""
    
    def __init__(self):
        """Initialize the RAG agent."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=0.7,
            max_output_tokens=2048
        )
        
        self.vector_store_manager = VectorStoreManager()
        self.document_processor = DocumentProcessor()
        self.chat_history = []
    
    def _invoke_with_retry(self, chain, inputs, retries=MAX_RETRIES):
        """Invoke a chain with retry logic for transient API failures."""
        for attempt in range(retries):
            try:
                result = chain.invoke(inputs)
                if result and str(result).strip():
                    return str(result)
                # Empty response — retry after short delay
                time.sleep(1)
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # exponential backoff: 1s, 2s
                else:
                    raise e
        return None
    
    def ask(
        self, 
        question: str, 
        conversation_id: str = None, 
        selected_sources: List[str] = None
    ) -> Dict[str, any]:
        """Ask a question with optional per-conversation source filtering."""
        try:
            # Retrieve documents with filters
            docs = self.vector_store_manager.similarity_search(
                question,
                conversation_id=conversation_id,
                selected_sources=selected_sources
            )
            
            context = "\n\n".join(doc.page_content for doc in docs) if docs else "No relevant documents found."
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are a helpful AI assistant for the company. You can answer questions using the provided context from company documents, or use your general knowledge for other questions.

Context from company documents:
{context}

Instructions:
- If the context contains relevant information, use it to answer the question accurately.
- If the context doesn't contain relevant information, use your general knowledge to provide a helpful answer.
- Be clear about whether you're answering from company documents or general knowledge.
- If you're unsure, say so honestly."""),
            ] + [(msg.type, msg.content) for msg in self.chat_history] + [
                ("human", "{question}")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            answer = self._invoke_with_retry(chain, {"question": question})
            
            if not answer:
                # All retries returned empty — try direct LLM call
                response = self.llm.invoke(question)
                answer = response.content if hasattr(response, 'content') else str(response)
            
            if not answer or not answer.strip():
                answer = "I'm having trouble generating a response right now. Please try again."
            
            self.chat_history.append(HumanMessage(content=question))
            self.chat_history.append(AIMessage(content=answer))
            
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]
            
            return {
                "answer": answer,
                "sources": [
                    {
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in docs
                ],
                "mode": "rag" if docs else "general"
            }
        except Exception as e:
            # Fallback: direct LLM call with retries
            for attempt in range(MAX_RETRIES):
                try:
                    response = self.llm.invoke(question)
                    answer = response.content if hasattr(response, 'content') else str(response)
                    if answer and answer.strip():
                        return {
                            "answer": answer,
                            "sources": [],
                            "mode": "general"
                        }
                    time.sleep(1)
                except Exception:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(2 ** attempt)
            
            return {
                "answer": "I'm having trouble connecting to the AI service. Please try again in a moment.",
                "sources": [],
                "mode": "general"
            }
    
    def add_documents(self, file_path: str, conversation_id: str = None) -> Dict[str, any]:
        """Process and add documents to the vector store."""
        try:
            chunks = self.document_processor.process_document(file_path)
            ids = self.vector_store_manager.add_documents(chunks, conversation_id=conversation_id)
            
            return {
                "success": True,
                "chunks_created": len(chunks),
                "document_ids": ids,
                "file": file_path
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file": file_path
            }
    
    def add_text(self, text: str, source: str = "manual_input", conversation_id: str = None) -> Dict[str, any]:
        """Add raw text to the vector store."""
        try:
            chunks = self.document_processor.process_text(text, source)
            ids = self.vector_store_manager.add_documents(chunks, conversation_id=conversation_id)
            
            return {
                "success": True,
                "chunks_created": len(chunks),
                "document_ids": ids
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_collection_info(self) -> Dict:
        """Get information about the vector store collection."""
        return self.vector_store_manager.get_collection_info()
    
    def clear_memory(self):
        """Clear conversation memory."""
        self.chat_history = []
