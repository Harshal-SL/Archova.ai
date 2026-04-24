"""
Batch query script - test multiple prompts and save results to file
Usage: python batch_query_vector_db.py
"""

import json
from pathlib import Path
from datetime import datetime
from app.services.rag_design.indexer import ChromaDocumentIndex
from app.services.rag_design.retriever import build_retrieval_query, rank_retrieval_hits, build_context_block
from app.config import settings


# Add your test prompts here
TEST_PROMPTS = [
    "Create an E-commerce application for 10k users interacting everyday",
    "Design a real-time chat messaging system like WhatsApp",
    "Build a video streaming platform similar to Netflix",
    "Design a ride-sharing application like Uber",
    "Create a social media platform for photo sharing",
]


def query_vector_db(prompt: str, index: ChromaDocumentIndex) -> dict:
    """Query vector DB and return structured results"""
    
    # Build parameters
    parameters = {
        "goal": prompt,
        "system_type": "distributed system",
    }
    
    # Build retrieval query
    retrieval_query = build_retrieval_query(parameters)
    
    # Query vector DB
    raw_hits = index.query(retrieval_query, n_results=settings.rag_retrieval_k)
    
    # Rank results
    ranked_hits = rank_retrieval_hits(
        raw_hits,
        max_items=settings.rag_context_docs,
        existing_design_boost=settings.rag_existing_design_boost,
    )
    
    # Build context
    context_block, references = build_context_block(
        ranked_hits,
        max_chars=settings.rag_context_char_budget,
    )
    
    # Structure results
    results = {
        "prompt": prompt,
        "retrieval_query": retrieval_query,
        "config": {
            "retrieval_k": settings.rag_retrieval_k,
            "context_docs": settings.rag_context_docs,
            "context_char_budget": settings.rag_context_char_budget,
            "embedding_model": settings.rag_embedding_model,
            "existing_design_boost": settings.rag_existing_design_boost,
        },
        "raw_results": [
            {
                "rank": i + 1,
                "source": hit['metadata'].get('source_path', 'unknown'),
                "chunk_index": hit['metadata'].get('chunk_index', 'N/A'),
                "distance": round(hit['distance'], 6),
                "similarity": round(hit['similarity'], 6),
                "is_existing_design": hit['metadata'].get('is_existing_design', False),
                "content_preview": hit['text'][:200] + "..." if len(hit['text']) > 200 else hit['text'],
                "content_length": len(hit['text']),
            }
            for i, hit in enumerate(raw_hits)
        ],
        "ranked_results": [
            {
                "rank": i + 1,
                "source": hit.metadata.get('source_path', 'unknown'),
                "base_similarity": round(hit.similarity, 6),
                "boost_applied": round(hit.score - hit.similarity, 6),
                "final_score": round(hit.score, 6),
                "content_preview": hit.text[:200] + "..." if len(hit.text) > 200 else hit.text,
                "content_length": len(hit.text),
            }
            for i, hit in enumerate(ranked_hits)
        ],
        "context_block": context_block,
        "context_length": len(context_block),
        "references": references,
    }
    
    return results


def main():
    print("=" * 80)
    print("BATCH VECTOR DATABASE QUERY TOOL")
    print("=" * 80)
    
    # Initialize vector DB
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
        print(f"✓ Total indexed chunks: {doc_count}")
        
        if doc_count == 0:
            print("\n⚠ WARNING: Vector database is empty!")
            return
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return
    
    # Process all prompts
    print(f"\nProcessing {len(TEST_PROMPTS)} prompts...")
    print("-" * 80)
    
    all_results = []
    
    for i, prompt in enumerate(TEST_PROMPTS, 1):
        print(f"\n[{i}/{len(TEST_PROMPTS)}] Processing: {prompt[:60]}...")
        
        try:
            result = query_vector_db(prompt, index)
            all_results.append(result)
            
            # Print summary
            print(f"  ✓ Retrieved: {len(result['raw_results'])} results")
            print(f"  ✓ Top source: {result['ranked_results'][0]['source'] if result['ranked_results'] else 'None'}")
            print(f"  ✓ Top score: {result['ranked_results'][0]['final_score'] if result['ranked_results'] else 0:.4f}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            all_results.append({
                "prompt": prompt,
                "error": str(e)
            })
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"vector_db_results_{timestamp}.json"
    
    output_data = {
        "timestamp": timestamp,
        "total_prompts": len(TEST_PROMPTS),
        "vector_db_config": {
            "collection": settings.rag_collection_name,
            "embedding_model": settings.rag_embedding_model,
            "total_chunks": doc_count,
        },
        "results": all_results,
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print(f"✓ Results saved to: {output_file}")
    print("=" * 80)
    
    # Print summary table
    print("\nSUMMARY TABLE")
    print("-" * 80)
    print(f"{'#':<4} {'Prompt':<45} {'Top Source':<30}")
    print("-" * 80)
    
    for i, result in enumerate(all_results, 1):
        if 'error' in result:
            print(f"{i:<4} {result['prompt'][:45]:<45} ERROR")
        else:
            top_source = result['ranked_results'][0]['source'].split('/')[-1] if result['ranked_results'] else 'None'
            print(f"{i:<4} {result['prompt'][:45]:<45} {top_source:<30}")
    
    print("-" * 80)
    print(f"\nDetailed results available in: {output_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
