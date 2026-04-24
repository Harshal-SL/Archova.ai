"""
Demo script to show RAG retrieval process for design generation
"""

from app.services.rag_design.retriever import build_retrieval_query, rank_retrieval_hits
from app.services.rag_design.indexer import ChromaDocumentIndex
from app.config import settings
from pathlib import Path

# Example parameters for "E-commerce application for 10k users interacting everyday"
example_parameters = {
    "goal": "E-commerce application for 10k users interacting everyday",
    "system_type": "E-commerce platform",
    "actors": ["Customer", "Admin", "Seller"],
    "functional_requirements": [
        "Product browsing and search",
        "Shopping cart management",
        "Order processing and payment",
        "User authentication and profiles"
    ],
    "non_functional_requirements": [
        "Support 10,000 daily active users",
        "High availability (99.9%)",
        "Fast response times (<200ms)",
        "Secure payment processing"
    ]
}

print("=" * 80)
print("RAG DESIGN GENERATION - RETRIEVAL DEMO")
print("=" * 80)

# Step 1: Build retrieval query
print("\n1. BUILDING RETRIEVAL QUERY")
print("-" * 80)
retrieval_query = build_retrieval_query(example_parameters)
print("Query sent to vector database:")
print(retrieval_query)

# Step 2: Show retrieval configuration
print("\n2. RETRIEVAL CONFIGURATION")
print("-" * 80)
print(f"Embedding Model: {settings.rag_embedding_model}")
print(f"Collection Name: {settings.rag_collection_name}")
print(f"Initial Retrieval K: {settings.rag_retrieval_k} documents")
print(f"Final Context Docs: {settings.rag_context_docs} documents")
print(f"Context Char Budget: {settings.rag_context_char_budget} characters")
print(f"Existing Design Boost: {settings.rag_existing_design_boost}")
print(f"Similarity Metric: Cosine similarity")

# Step 3: Initialize index and query
print("\n3. QUERYING VECTOR DATABASE")
print("-" * 80)
index = ChromaDocumentIndex(
    persist_dir=Path(settings.rag_persist_dir),
    collection_name=settings.rag_collection_name,
    ollama_base_url=settings.ollama_base_url,
    embedding_model=settings.rag_embedding_model,
    timeout_seconds=settings.ollama_timeout_seconds,
)

doc_count = index.count()
print(f"Total documents in vector DB: {doc_count}")

if doc_count > 0:
    # Query the index
    raw_hits = index.query(retrieval_query, n_results=settings.rag_retrieval_k)
    
    print(f"\nRetrieved {len(raw_hits)} initial results")
    
    # Step 4: Show raw results
    print("\n4. RAW RETRIEVAL RESULTS")
    print("-" * 80)
    for i, hit in enumerate(raw_hits, 1):
        print(f"\nResult #{i}:")
        print(f"  Source: {hit['metadata'].get('source_path', 'unknown')}")
        print(f"  Distance: {hit['distance']:.4f}")
        print(f"  Similarity: {hit['similarity']:.4f}")
        print(f"  Is Existing Design: {hit['metadata'].get('is_existing_design', False)}")
        print(f"  Text Preview: {hit['text'][:150]}...")
    
    # Step 5: Rank results
    print("\n5. RANKED RESULTS (after scoring)")
    print("-" * 80)
    ranked_hits = rank_retrieval_hits(
        raw_hits,
        max_items=settings.rag_context_docs,
        existing_design_boost=settings.rag_existing_design_boost,
    )
    
    for i, hit in enumerate(ranked_hits, 1):
        print(f"\nRanked #{i}:")
        print(f"  Source: {hit.metadata.get('source_path', 'unknown')}")
        print(f"  Base Similarity: {hit.similarity:.4f}")
        print(f"  Final Score: {hit.score:.4f}")
        print(f"  Boost Applied: {hit.score - hit.similarity:.4f}")
        print(f"  Text Preview: {hit.text[:150]}...")
    
    print("\n6. RETRIEVAL TYPE")
    print("-" * 80)
    print("Type: SEMANTIC VECTOR SEARCH with COSINE SIMILARITY")
    print("\nHow it works:")
    print("1. User query is converted to embedding vector using nomic-embed-text")
    print("2. Vector DB (ChromaDB) performs cosine similarity search")
    print("3. Returns top-K most similar document chunks")
    print("4. Results are re-ranked with boost for existing designs")
    print("5. Top documents are used as context for LLM generation")
    
else:
    print("Vector database is empty. Run indexing first!")

print("\n" + "=" * 80)
