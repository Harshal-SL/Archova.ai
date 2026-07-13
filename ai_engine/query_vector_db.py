"""
Interactive script to query the vector database and see retrieval results
Usage: python query_vector_db.py
"""

import sys
from pathlib import Path
from app.services.rag_design.indexer import ChromaDocumentIndex
from app.services.rag_design.retriever import build_retrieval_query, rank_retrieval_hits, build_context_block
from app.config import settings


def print_separator(char="=", length=80):
    print(char * length)


def print_section(title):
    print(f"\n{title}")
    print_separator("-")


def main():
    print_separator()
    print("VECTOR DATABASE QUERY TOOL")
    print_separator()
    
    # Initialize the vector database
    print("\nInitializing vector database...")
    try:
        index = ChromaDocumentIndex(
            persist_dir=Path(settings.rag_persist_dir),
            collection_name=settings.rag_collection_name,
            ollama_base_url=settings.ollama_base_url,
            embedding_model=settings.rag_embedding_model,
            timeout_seconds=settings.ollama_timeout_seconds,
        )
        doc_count = index.count()
        print(f"✓ Connected to vector DB")
        print(f"✓ Collection: {settings.rag_collection_name}")
        print(f"✓ Total indexed chunks: {doc_count}")
        print(f"✓ Embedding model: {settings.rag_embedding_model}")
        
        if doc_count == 0:
            print("\n⚠ WARNING: Vector database is empty!")
            print("Please run the indexing process first.")
            return
            
    except Exception as e:
        print(f"\n✗ Error connecting to vector DB: {e}")
        return
    
    # Get user input
    print_section("ENTER YOUR PROMPT")
    print("Example: Create an E-commerce application for 10k users interacting everyday")
    print("\nYour prompt (or 'quit' to exit):")
    
    user_prompt = input("> ").strip()
    
    if not user_prompt or user_prompt.lower() in ['quit', 'exit', 'q']:
        print("Exiting...")
        return
    
    # Build parameters from prompt
    parameters = {
        "goal": user_prompt,
        "system_type": "distributed system",
        "actors": [],
        "functional_requirements": [],
        "non_functional_requirements": []
    }
    
    # Build retrieval query
    print_section("STEP 1: BUILDING RETRIEVAL QUERY")
    retrieval_query = build_retrieval_query(parameters)
    print(f"Query text sent to vector DB:\n{retrieval_query}")
    
    # Query the vector database
    print_section("STEP 2: QUERYING VECTOR DATABASE")
    print(f"Retrieving top {settings.rag_retrieval_k} results...")
    
    try:
        raw_hits = index.query(retrieval_query, n_results=settings.rag_retrieval_k)
        print(f"✓ Retrieved {len(raw_hits)} results")
    except Exception as e:
        print(f"✗ Error querying vector DB: {e}")
        return
    
    # Display raw results
    print_section("STEP 3: RAW RETRIEVAL RESULTS")
    
    if not raw_hits:
        print("No results found!")
        return
    
    for i, hit in enumerate(raw_hits, 1):
        print(f"\n{'─' * 80}")
        print(f"RESULT #{i}")
        print(f"{'─' * 80}")
        print(f"Source File    : {hit['metadata'].get('source_path', 'unknown')}")
        print(f"Chunk Index    : {hit['metadata'].get('chunk_index', 'N/A')}")
        print(f"Distance       : {hit['distance']:.6f}")
        print(f"Similarity     : {hit['similarity']:.6f}")
        print(f"Existing Design: {hit['metadata'].get('is_existing_design', False)}")
        print(f"\nContent Preview (first 300 chars):")
        print(f"{'-' * 80}")
        content = hit['text'][:300]
        print(content)
        if len(hit['text']) > 300:
            print("...")
        print(f"\nFull Content Length: {len(hit['text'])} characters")
    
    # Rank results
    print_section("STEP 4: RANKED & SCORED RESULTS")
    ranked_hits = rank_retrieval_hits(
        raw_hits,
        max_items=settings.rag_context_docs,
        existing_design_boost=settings.rag_existing_design_boost,
    )
    
    print(f"Top {len(ranked_hits)} results after ranking:")
    
    for i, hit in enumerate(ranked_hits, 1):
        boost = hit.score - hit.similarity
        print(f"\n{'─' * 80}")
        print(f"RANKED #{i}")
        print(f"{'─' * 80}")
        print(f"Source         : {hit.metadata.get('source_path', 'unknown')}")
        print(f"Base Similarity: {hit.similarity:.6f}")
        print(f"Boost Applied  : {boost:.6f}")
        print(f"Final Score    : {hit.score:.6f}")
        print(f"\nContent Preview:")
        print(f"{'-' * 80}")
        print(hit.text[:400])
        if len(hit.text) > 400:
            print("...")
    
    # Build context block
    print_section("STEP 5: FINAL CONTEXT BLOCK FOR LLM")
    context_block, references = build_context_block(
        ranked_hits,
        max_chars=settings.rag_context_char_budget,
    )
    
    print(f"Context character budget: {settings.rag_context_char_budget}")
    print(f"Actual context length: {len(context_block)} characters")
    print(f"\nContext block that will be sent to LLM:")
    print(f"{'=' * 80}")
    print(context_block)
    print(f"{'=' * 80}")
    
    print_section("STEP 6: REFERENCES")
    for i, ref in enumerate(references, 1):
        print(f"{i}. {ref['source']} - {ref['why_relevant']}")
    
    print_section("SUMMARY")
    print(f"✓ Query: {user_prompt}")
    print(f"✓ Retrieved: {len(raw_hits)} initial results")
    print(f"✓ Selected: {len(ranked_hits)} for context")
    print(f"✓ Context size: {len(context_block)} chars (budget: {settings.rag_context_char_budget})")
    print(f"✓ Retrieval type: Semantic vector search (cosine similarity)")
    print(f"✓ Embedding model: {settings.rag_embedding_model}")
    
    print_separator()
    print("Done!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
