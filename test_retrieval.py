"""Test which chunks are retrieved for different queries."""
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

queries = [
    "info on github access?",
    "github access",
    "how to get github access at nexora",
    "clone repositories",
    "source code repository",
]

for q in queries:
    vec = emb.embed_query(q)
    results = client.query_points(
        collection_name="company_docs", query=vec, limit=5, with_payload=True
    )
    print(f"\n=== QUERY: {q} ===")
    for i, pt in enumerate(results.points):
        content = pt.payload["page_content"][:100].replace("\n", " ")
        print(f"  #{i+1} (score={pt.score:.4f}): {content}...")
