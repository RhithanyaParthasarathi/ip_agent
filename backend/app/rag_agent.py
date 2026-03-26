"""RAG Agent orchestrating the retrieval and generation."""
import time
from typing import List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_ollama import ChatOllama  # For local/offline LLM via Ollama
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
        # --- Gemini API (active) ---
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.google_api_key,
            temperature=0.7
        )
        
        # --- Ollama / Local LLM (commented out) ---
        # self.llm = ChatOllama(
        #     model=settings.ollama_model,
        #     base_url=settings.ollama_host,
        #     temperature=0.7
        # )
        
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
            # ── Greeting / Identity detection (BEFORE vector search) ──
            import re
            cleaned = re.sub(r'[^\w\s]', '', question.lower()).strip()
            greetings = {"hi", "hello", "hey", "good morning", "good afternoon",
                        "good evening", "sup", "howdy", "what's up", "whats up",
                        "who are you", "what are you", "what can you do", "help",
                        "how are you", "hows it going", "how's it going",
                        "hows work", "how was your day", "hi there", "hello there",
                        "greet", "morning", "evening", "who is this", "what is red ai"}
            
            # Bulletproof check for identity or simple greeting
            words = cleaned.split()
            is_identity_request = "who are you" in cleaned or "what are you" in cleaned or "who is this" in cleaned or "who is red ai" in cleaned
            is_greeting = (
                cleaned in greetings 
                or (words and words[0] in greetings)
                or is_identity_request
            )

            if is_greeting:
                system_msg = """You are Red AI, a friendly onboarding assistant for new company employees.
Your job is to help employees understand company policies, benefits, and procedures.
When someone greets you, respond warmly and briefly (1-2 sentences max).
For 'who are you' or similar, explain you are Red AI: an agent who can help you understand company policies while you onboard.
Keep responses short, warm, and professional."""
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_msg),
                    ("human", "{question}")
                ])
                chain = prompt | self.llm | StrOutputParser()
                answer = self._invoke_with_retry(chain, {"question": question})
                
                # Fallback to prevent "I don't have information" for greetings
                if not answer or not answer.strip() or "information about" in answer.lower():
                    if is_identity_request:
                        answer = "I'm Red AI, your onboarding assistant. I can help you understand company policies while you onboard."
                    else:
                        answer = "Hi! I'm Red AI, your onboarding companion. How can I help you today?"
                
                self.chat_history.append(HumanMessage(content=question))
                self.chat_history.append(AIMessage(content=answer))
                return {"answer": answer, "sources": [], "mode": "general"}

            # ── RAG: Retrieve documents ──
            docs = self.vector_store_manager.similarity_search(
                question,
                conversation_id=conversation_id,
                selected_sources=selected_sources
            )
            
            context = "\n\n".join(doc.page_content for doc in docs) if docs else ""
            
            if context:
                system_msg = f"""You are Red AI, a company onboarding assistant. Answer questions using ONLY the context provided below.
For questions that are clearly unrelated to company policies or work (e.g. geography, cooking, sports), say "I don't have information about that."

CONTEXT:
{context}

EXAMPLES:
Q: What are the working hours?
A: Working hours are 9:30 AM to 6:30 PM.

Q: How many sick leaves do I get?
A: You get 12 sick leaves per year.

Q: What is the capital of France?
A: I don't have information about that.

ANSWER THE QUESTION BELOW. If the answer is not in the context, say "I don't have information about that.\""""
            else:
                # No documents found — refuse politely
                return {
                    "answer": "I don't have information about that in the company documents.",
                    "sources": [],
                    "mode": "rag"
                }
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_msg),
                ("human", "{question}")
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            answer = self._invoke_with_retry(chain, {"question": question})
            
            if not answer or not answer.strip():
                answer = "I don't have information about that."
            
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
            # If the API fails (like 429 Rate Limit) or network disconnects
            return {
                "answer": "I'm having trouble connecting to the AI service. Please try again in a moment.",
                "sources": [],
                "mode": "rag"
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
