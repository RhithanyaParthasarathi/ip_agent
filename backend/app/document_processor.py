"""Document processing utilities."""
from pathlib import Path
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredHTMLLoader
)
from .config import settings


class DocumentProcessor:
    """Handles document loading and processing."""
    
    def __init__(self):
        """Initialize the document processor."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_document(self, file_path: str) -> List[Document]:
        """Load a document based on its file type."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Select appropriate loader based on file extension
        extension = file_path.suffix.lower()
        
        if extension == ".pdf":
            loader = PyPDFLoader(str(file_path))
        elif extension in [".docx", ".doc"]:
            loader = Docx2txtLoader(str(file_path))
        elif extension == ".txt":
            loader = TextLoader(str(file_path))
        elif extension in [".html", ".htm"]:
            loader = UnstructuredHTMLLoader(str(file_path))
        else:
            raise ValueError(f"Unsupported file type: {extension}")
        
        documents = loader.load()
        
        # Add metadata
        for doc in documents:
            doc.metadata["source"] = file_path.name
            doc.metadata["file_type"] = extension
        
        return documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        chunks = self.text_splitter.split_documents(documents)
        return chunks
    
    def process_document(self, file_path: str) -> List[Document]:
        """Load and split a document in one step."""
        documents = self.load_document(file_path)
        chunks = self.split_documents(documents)
        return chunks
    
    def process_text(self, text: str, source: str = "text") -> List[Document]:
        """Process raw text into document chunks."""
        document = Document(
            page_content=text,
            metadata={"source": source}
        )
        chunks = self.text_splitter.split_documents([document])
        return chunks
