"""
Quick setup verification script for the RAG Agent.
Run this to verify all components are properly configured.
"""
import sys
import importlib.util

def check_python_version():
    """Check if Python version is 3.9 or higher."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print("✓ Python version OK:", f"{version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print("✗ Python version too old. Need 3.9+, have:", f"{version.major}.{version.minor}.{version.micro}")
        return False

def check_package(package_name, display_name=None):
    """Check if a Python package is installed."""
    if display_name is None:
        display_name = package_name
    
    spec = importlib.util.find_spec(package_name)
    if spec is not None:
        print(f"✓ {display_name} installed")
        return True
    else:
        print(f"✗ {display_name} NOT installed")
        return False

def check_env_file():
    """Check if .env file exists."""
    import os
    if os.path.exists('.env'):
        print("✓ .env file exists")
        # Check if API key is set
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key and api_key != 'your_google_api_key_here':
            print("✓ GOOGLE_API_KEY is configured")
            return True
        else:
            print("⚠ GOOGLE_API_KEY not set in .env file")
            print("  Get your free key from: https://aistudio.google.com/app/apikey")
            return False
    else:
        print("✗ .env file NOT found. Copy .env.example to .env and add your API key.")
        return False

def check_qdrant_connection():
    """Check if Qdrant is running."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333)
        collections = client.get_collections()
        print("✓ Qdrant is running and accessible")
        return True
    except Exception as e:
        print(f"✗ Cannot connect to Qdrant: {e}")
        print("  Start Qdrant with: docker run -p 6333:6333 qdrant/qdrant")
        return False

def check_data_directory():
    """Check if data directory exists."""
    import os
    from pathlib import Path
    
    upload_dir = Path("data/uploads")
    if upload_dir.exists():
        print(f"✓ Upload directory exists: {upload_dir}")
        return True
    else:
        print(f"⚠ Upload directory doesn't exist. Creating: {upload_dir}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        return True

def main():
    """Run all setup checks."""
    print("=" * 60)
    print("RAG Agent Setup Verification")
    print("=" * 60)
    print()
    
    checks = []
    
    print("1. Checking Python version...")
    checks.append(check_python_version())
    print()
    
    print("2. Checking Python packages...")
    packages = [
        ("langchain", "LangChain"),
        ("google.generativeai", "Google Generative AI"),
        ("qdrant_client", "Qdrant Client"),
        ("fastapi", "FastAPI"),
        ("sentence_transformers", "Sentence Transformers"),
        ("pypdf", "PyPDF"),
    ]
    
    for package, name in packages:
        checks.append(check_package(package, name))
    print()
    
    print("3. Checking environment configuration...")
    checks.append(check_env_file())
    print()
    
    print("4. Checking Qdrant connection...")
    checks.append(check_qdrant_connection())
    print()
    
    print("5. Checking data directories...")
    checks.append(check_data_directory())
    print()
    
    print("=" * 60)
    if all(checks):
        print("✓ All checks passed! Ready to run the RAG agent.")
        print()
        print("Next steps:")
        print("  1. Start backend: python main.py")
        print("  2. Start frontend: cd frontend && npm run dev")
        print("  3. Open browser: http://localhost:5173")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print()
        print("Common fixes:")
        print("  - Install packages: pip install -r requirements.txt")
        print("  - Create .env: copy .env.example .env")
        print("  - Start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
    print("=" * 60)

if __name__ == "__main__":
    main()
