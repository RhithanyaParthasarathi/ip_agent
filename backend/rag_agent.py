"""RAG Agent orchestrating the retrieval and generation."""
from typing import List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from vector_store import VectorStoreManager
from document_processor import DocumentProcessor
from config import settings


class RAGAgent:
    """RAG Agent with retrieval and generation capabilities."""
    
    def __init__(self):
        """Initialize the RAG agent."""
        # Initialize Gemini
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=0.7,
            max_output_tokens=2048
        )
        
        # Initialize vector store and document processor
        self.vector_store_manager = VectorStoreManager()
        self.document_processor = DocumentProcessor()
        
        # Chat history for conversation context
        self.chat_history = []
        
        # Custom prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant for the company. You can answer questions using the provided context from company documents, or use your general knowledge for other questions.

Context from company documents:
{context}

Instructions:
- If the context contains relevant information, use it to answer the question accurately.
- If the context doesn't contain relevant information, use your general knowledge to provide a helpful answer.
- Be clear about whether you're answering from company documents or general knowledge.
- If you're unsure, say so honestly."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        self._build_chain()
    
    def _build_chain(self):
        """Build the RAG chain."""
        vectorstore = self.vector_store_manager.get_vectorstore()
        self.retriever = vectorstore.as_retriever(
            search_kwargs={"k": settings.top_k_results}
        )
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        self.chain = (
            {
                "context": self.retriever | format_docs,
                "question": RunnablePassthrough(),
                "chat_history": lambda x: self.chat_history
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
    
    def ask(self, question: str) -> Dict[str, any]:
        """
        Ask a question to the agent.
        
        Args:
            question: The user's question
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            # Get relevant documents
            docs = self.retriever.invoke(question)
            
            # Get answer from the chain
            answer = self.chain.invoke(question)
            
            # Update chat history
            self.chat_history.append(HumanMessage(content=question))
            self.chat_history.append(AIMessage(content=answer))
            
            # Keep history manageable (last 10 messages)
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
            # Fallback to general knowledge
            response = self.llm.invoke(question)
            answer = response.content if hasattr(response, 'content') else str(response)
            return {
                "answer": answer,
                "sources": [],
                "mode": "general"
            }
    
    def _should_use_rag(self, question: str) -> bool:
        """
        Determine if the question should use RAG or general knowledge.
        Simple heuristic - always try RAG and let the prompt handle it.
        """
        # Always use RAG - the prompt will handle whether to use context or not
        return True
    
    def add_documents(self, file_path: str) -> Dict[str, any]:
        """
        Process and add documents to the vector store.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Information about the processing
        """
        try:
            chunks = self.document_processor.process_document(file_path)
            ids = self.vector_store_manager.add_documents(chunks)
            
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
    
    def add_text(self, text: str, source: str = "manual_input") -> Dict[str, any]:
        """
        Add raw text to the vector store.
        
        Args:
            text: The text content to add
            source: Source identifier
            
        Returns:
            Information about the processing
        """
        try:
            chunks = self.document_processor.process_text(text, source)
            ids = self.vector_store_manager.add_documents(chunks)
            
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
