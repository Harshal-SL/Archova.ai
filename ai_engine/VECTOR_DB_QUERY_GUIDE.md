# Vector Database Query Tools

Tools to inspect what gets retrieved from the vector database during design generation.

## Files Created

1. **query_vector_db.py** - Interactive single query tool
2. **batch_query_vector_db.py** - Batch processing for multiple prompts
3. **test_retrieval_demo.py** - Demo with hardcoded e-commerce example

## Usage

### Option 1: Interactive Query (Recommended)

Run the interactive tool and enter your prompt:

```bash
python query_vector_db.py
```

**Example session:**
```
> Create an E-commerce application for 10k users interacting everyday
```

**Output shows:**
- Step 1: Retrieval query built from your prompt
- Step 2: Query execution details
- Step 3: Raw results with similarity scores
- Step 4: Ranked results with boost applied
- Step 5: Final context block sent to LLM
- Step 6: References used

### Option 2: Batch Query

Test multiple prompts at once and save results to JSON:

```bash
python batch_query_vector_db.py
```

Edit the `TEST_PROMPTS` list in the file to add your own prompts.

**Output:**
- Console summary for each prompt
- Detailed JSON file: `vector_db_results_YYYYMMDD_HHMMSS.json`

### Option 3: Demo Script

Run the pre-configured demo with e-commerce example:

```bash
python test_retrieval_demo.py
```

## What You'll See

### 1. Retrieval Query
The structured query sent to the vector database:
```
Goal: E-commerce application for 10k users interacting everyday
System type: E-commerce platform
Actors: Customer, Admin, Seller
...
```

### 2. Raw Results
Each retrieved document chunk with:
- **Source File**: Which markdown file it came from
- **Distance**: Cosine distance (lower = more similar)
- **Similarity**: Converted score (higher = more similar)
- **Content**: The actual text retrieved

### 3. Ranked Results
After re-ranking with boosts:
- **Base Similarity**: Original similarity score
- **Boost Applied**: Extra score for existing designs (+0.2)
- **Final Score**: Used for final selection

### 4. Context Block
The final text sent to the LLM for generation (limited by character budget)

## Configuration

Current settings (from `app/config.py`):

```python
rag_retrieval_k = 3              # Retrieve top 3 candidates
rag_context_docs = 1             # Use top 1 for context
rag_context_char_budget = 1000   # Max 1000 chars in context
rag_embedding_model = "nomic-embed-text"
rag_existing_design_boost = 0.2  # +0.2 score for existing designs
```

## Retrieval Type

**Semantic Vector Search with Cosine Similarity**

- Embedding model: nomic-embed-text (via Ollama)
- Vector DB: ChromaDB with HNSW index
- Similarity metric: Cosine similarity
- Two-stage: Retrieve K candidates → Re-rank → Select top N

## Example Output Structure

```json
{
  "prompt": "Create an E-commerce application...",
  "raw_results": [
    {
      "rank": 1,
      "source": "data/RAG/category_10_real_world_systems/10.3_amazon_E-commerce_system.md",
      "similarity": 0.8234,
      "content_preview": "Amazon E-commerce System..."
    }
  ],
  "ranked_results": [
    {
      "rank": 1,
      "final_score": 0.8234,
      "boost_applied": 0.0
    }
  ],
  "context_block": "[source: 10.3_amazon_E-commerce_system.md | score: 0.823]\n..."
}
```

## Troubleshooting

### "Vector database is empty"
Run the indexing process first:
```bash
# Start your FastAPI server which will auto-index on first request
# OR manually trigger reindexing via the API
```

### "Python not found"
Make sure Python is installed and in your PATH:
```bash
python --version
# or
python3 --version
```

### "Module not found"
Install dependencies:
```bash
pip install -r requirements.txt
```

## Understanding the Results

**High Similarity (>0.8)**: Very relevant, likely contains similar system design
**Medium Similarity (0.5-0.8)**: Somewhat relevant, may have useful patterns
**Low Similarity (<0.5)**: Less relevant, but might have specific components

The system uses the top-ranked results to provide context to the LLM, which then generates the final design document.
