"""Simple demo script to test the RAG agent."""
import sys
from pathlib import Path
from rag_agent import RAGAgent


def print_section(title: str):
    """Print a section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")


def main():
    """Run a simple demo of the RAG agent."""
    print_section("RAG Agent Demo - Initializing")
    
    try:
        # Initialize the agent
        print("Initializing RAG agent with Claude and Qdrant...")
        agent = RAGAgent()
        print("✓ Agent initialized successfully!\n")
        
        # Check collection info
        info = agent.get_collection_info()
        print(f"Vector Store Status:")
        print(f"  - Collection: {info.get('name', 'N/A')}")
        print(f"  - Documents: {info.get('points_count', 0)}")
        
        # Demo 1: Add sample text
        print_section("Demo 1: Adding Sample Company Information")
        sample_text = """
        Company Name: TechCorp Solutions
        Founded: 2020
        Location: San Francisco, CA
        
        About Us:
        TechCorp Solutions is a leading software development company specializing in 
        AI and machine learning solutions. We have over 100 employees and serve clients 
        globally. Our main products include CloudAI Platform and DataSync Pro.
        
        Working Hours: Monday to Friday, 9 AM to 6 PM PST
        Support Email: support@techcorp.com
        Sales Contact: sales@techcorp.com
        
        Benefits:
        - Health insurance
        - 401(k) matching
        - Remote work options
        - Professional development budget
        """
        
        print("Adding sample company information to knowledge base...")
        result = agent.add_text(sample_text, source="company_info")
        
        if result["success"]:
            print(f"✓ Successfully added! Created {result['chunks_created']} chunks")
        else:
            print(f"✗ Error: {result['error']}")
        
        # Demo 2: RAG-based questions
        print_section("Demo 2: Testing RAG-Based Questions")
        
        rag_questions = [
            "What are the working hours?",
            "What is TechCorp Solutions?",
            "What benefits does the company offer?",
        ]
        
        for i, question in enumerate(rag_questions, 1):
            print(f"\nQuestion {i}: {question}")
            print("-" * 60)
            
            response = agent.ask(question)
            print(f"Answer: {response['answer']}\n")
            
            if response['sources']:
                print(f"Sources used: {len(response['sources'])} documents")
                print(f"Mode: {response['mode']}")
        
        # Demo 3: General knowledge questions
        print_section("Demo 3: Testing General Knowledge Questions")
        
        general_questions = [
            "What is the capital of France?",
            "Explain what artificial intelligence is",
        ]
        
        for i, question in enumerate(general_questions, 1):
            print(f"\nQuestion {i}: {question}")
            print("-" * 60)
            
            response = agent.ask(question)
            print(f"Answer: {response['answer']}\n")
            print(f"Mode: {response['mode']}")
        
        # Demo 4: Document upload (if provided)
        print_section("Demo 4: Document Upload (Optional)")
        print("To test document upload, place PDF/DOCX/TXT files in the 'data/uploads' folder")
        print("Then uncomment the document upload code in this script.\n")
        
        # Uncomment to test with your own documents:
        # doc_path = "data/uploads/your_document.pdf"
        # if Path(doc_path).exists():
        #     print(f"Processing document: {doc_path}")
        #     result = agent.add_documents(doc_path)
        #     if result["success"]:
        #         print(f"✓ Successfully processed! Created {result['chunks_created']} chunks")
        
        print_section("Demo Complete!")
        print("The RAG agent is working correctly!")
        print("\nNext steps:")
        print("1. Add your own documents using agent.add_documents(file_path)")
        print("2. Start the FastAPI server: python main.py")
        print("3. Test the API endpoints at http://localhost:8000/docs")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nMake sure:")
        print("1. Qdrant is running (docker or locally)")
        print("2. .env file is configured with ANTHROPIC_API_KEY")
        print("3. All dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()
