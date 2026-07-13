# Graph Report - app  (2026-04-22)

## Corpus Check
- Corpus is ~6,848 words - fits in a single context window. You may not need a graph.

## Summary
- 132 nodes · 240 edges · 10 communities detected
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 29 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]

## God Nodes (most connected - your core abstractions)
1. `_normalize_low_level_design()` - 14 edges
2. `_as_str()` - 13 edges
3. `run_design_pipeline()` - 12 edges
4. `ChromaDocumentIndex` - 11 edges
5. `_as_list()` - 11 edges
6. `_build_index()` - 10 edges
7. `normalize_design_output()` - 8 edges
8. `_fill_template()` - 7 edges
9. `_normalize_components_from_raw_lld()` - 7 edges
10. `_ensure_index_ready()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `generate_system_design()` --calls--> `run_design_pipeline()`  [INFERRED]
  E:\Major\Major_code\ai_engine\app\routers\design_router.py → E:\Major\Major_code\ai_engine\app\services\rag_design\pipeline.py
- `extract_requirements()` --calls--> `run_extraction_pipeline()`  [INFERRED]
  E:\Major\Major_code\ai_engine\app\routers\extraction_router.py → E:\Major\Major_code\ai_engine\app\services\requirement_extractor\pipeline.py
- `run_design_pipeline()` --calls--> `build_context_block()`  [INFERRED]
  E:\Major\Major_code\ai_engine\app\services\rag_design\pipeline.py → E:\Major\Major_code\ai_engine\app\services\rag_design\retriever.py
- `rebuild_design_index()` --calls--> `reindex_corpus()`  [INFERRED]
  E:\Major\Major_code\ai_engine\app\routers\design_router.py → E:\Major\Major_code\ai_engine\app\services\rag_design\pipeline.py
- `run_design_pipeline()` --calls--> `build_design_prompt()`  [INFERRED]
  E:\Major\Major_code\ai_engine\app\services\rag_design\pipeline.py → E:\Major\Major_code\ai_engine\app\services\rag_design\generator.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.0
Nodes (16): build_design_prompt(), _extract_json(), generate_design_from_ollama(), _as_list(), _build_expected_state(), _build_index(), _compute_corpus_signature(), _ensure_index_ready() (+8 more)

### Community 1 - "Community 1"
Cohesion: 0.0
Nodes (18): _as_bool(), _as_dict(), _as_int(), _as_list(), _as_str(), _fill_template(), _legacy_auth_component(), _legacy_backend_component() (+10 more)

### Community 2 - "Community 2"
Cohesion: 0.0
Nodes (13): merge_answers(), Fill missing parameter values using user-provided answers.      Each answer it, BaseModel, DesignRequest, generate_system_design(), rebuild_design_index(), AnswerItem, AnswerRequest (+5 more)

### Community 3 - "Community 3"
Cohesion: 0.0
Nodes (13): chunk_text(), Split text into overlapping chunks.      chunk_size and overlap are in tokens., _empty_result(), extract_from_chunk(), _parse_json(), Parse model output. Returns None if parsing fails (triggers retry)., Send one chunk to Mistral via HTTP and return a partial requirements dict., merge_results() (+5 more)

### Community 4 - "Community 4"
Cohesion: 0.0
Nodes (10): create_recursive_splitter(), FallbackDocument, build_context_block(), build_retrieval_query(), _fallback_split(), _parameter_value(), rank_retrieval_hits(), RetrievalHit (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.0
Nodes (7): detect_missing_parameters(), Return a list of parameter keys whose value is None., elicit_requirements(), Step 3 — Detect missing parameters and generate clarification questions., run_elicitation_pipeline(), generate_questions(), _parse_json()

### Community 6 - "Community 6"
Cohesion: 0.0
Nodes (2): ChromaDocumentIndex, _normalize_metadata()

### Community 7 - "Community 7"
Cohesion: 0.0
Nodes (8): discover_corpus_files(), is_existing_design_document(), load_corpus_documents(), load_file_text(), _normalize_segment(), _read_docx(), _read_markdown(), _read_pdf()

### Community 8 - "Community 8"
Cohesion: 0.0
Nodes (5): _build_settings(), _default_rag_data_root(), _float_env(), _int_env(), Settings

### Community 9 - "Community 9"
Cohesion: 0.0
Nodes (3): parse_file(), process_input(), build_prompt()

## Knowledge Gaps
- **11 isolated node(s):** `Step 3 — Detect missing parameters and generate clarification questions.`, `Step 4 — Merge user answers into the parameter set.      Accepts the parameter`, `Fill missing parameter values using user-provided answers.      Each answer it`, `Return a list of parameter keys whose value is None.`, `FallbackDocument` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 6`** (10 nodes): `ChromaDocumentIndex`, `._embed_one_by_one()`, `._embed_texts()`, `.index_documents()`, `.__init__()`, `.query()`, `.reset_collection()`, `._try_embed_batch()`, `._upsert_batch()`, `_normalize_metadata()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.