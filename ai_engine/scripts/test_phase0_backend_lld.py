"""Phase 0 Quick Win -- Isolated Backend LLD test.

Proves the hypothesis: flat model + example-driven prompt + json_object mode
+ 8192 max_tokens = reliable structured output.

Runs the backend LLD generation 10 times against real ARSRS input and reports
the success/failure rate.

Usage:
    cd ai_engine
    python scripts/test_phase0_backend_lld.py
"""

from __future__ import annotations

import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=True)

import httpx
from app.sae.models.response_models import BackendLLDResponse
from app.sae.utils.prompt_utils import repair_json_string

# ─── Configuration ───────────────────────────────────────────────────────────

API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
MODEL = os.getenv("LLM_MODEL", "nvidia/nemotron-3.5-lightning:free")
MAX_TOKENS = 8192
TIMEOUT = 90  # seconds
NUM_RUNS = 5

# ─── Prompts (example-driven, no schema injection) ───────────────────────────

SYSTEM_PROMPT = """You are a Principal Backend Architect generating a Backend Low Level Design (LLD).

Analyze the provided system requirements and HLD summary, then produce a complete backend design as a JSON object.

CRITICAL RULES:
1. Respond ONLY with a valid JSON object — no markdown, no explanation, no code blocks.
2. Keep lists to 3-5 items maximum — be concise but complete.
3. Cover all essential backend concerns: API endpoints, services, domain models, repositories, project structure.

Your response MUST follow this exact JSON structure:

{
  "api_endpoints": [
    {"route": "/api/v1/books", "method": "GET", "description": "List all books with pagination", "request": {"query_params": ["page", "limit", "search"]}, "response": {"status": 200, "body": "List of Book objects"}, "auth_required": true}
  ],
  "services": [
    {"name": "BookService", "responsibility": "Core book management logic", "methods": ["getBooks", "getBookById", "createBook", "updateBook", "deleteBook"], "dependencies": ["BookRepository", "CacheService"]}
  ],
  "domain_models": [
    {"name": "Book", "type": "entity", "fields": {"id": "UUID", "title": "String", "author": "String", "isbn": "String", "status": "BookStatus"}, "relationships": ["BorrowRecord"]}
  ],
  "repositories": [
    {"name": "BookRepository", "entity": "Book", "methods": ["findAll", "findById", "save", "delete", "findByIsbn"], "database": "PostgreSQL"}
  ],
  "project_structure": {
    "pattern": "Clean Architecture",
    "layers": {"presentation": "controllers/", "application": "services/", "domain": "models/", "infrastructure": "repositories/"}
  },
  "framework_config": {
    "framework": "FastAPI",
    "language": "Python",
    "key_dependencies": ["SQLAlchemy", "Pydantic", "Alembic"]
  },
  "security_config": {
    "auth_type": "JWT Bearer Token",
    "middleware": ["AuthMiddleware", "CORSMiddleware"],
    "rbac_roles": ["student", "librarian", "admin"]
  },
  "error_handling": {
    "strategy": "Global exception handler",
    "error_format": {"code": "string", "message": "string", "details": "object"}
  },
  "dependencies": ["fastapi", "sqlalchemy", "pydantic", "alembic", "python-jose", "passlib"],
  "architecture_patterns": ["Clean Architecture", "Repository Pattern", "Dependency Injection", "DTO Pattern"]
}"""

USER_PROMPT_TEMPLATE = """Generate a complete Backend Low Level Design for the following system:

=== SYSTEM OVERVIEW ===
System: {system_name}
Domain: {domain}
Modules: {modules}

=== KEY REQUIREMENTS ===
{requirements_summary}

=== KEY WORKFLOWS ===
{workflows_summary}

=== TECHNOLOGY DECISIONS ===
Backend Framework: Choose the best fit based on the requirements
Database: Choose based on data patterns
Authentication: JWT-based auth

Generate the complete Backend LLD JSON now."""


def load_arsrs() -> dict:
    """Load ARSRS from the output directory."""
    arsrs_path = PROJECT_ROOT / "output" / "arsrs.json"
    if not arsrs_path.exists():
        print(f"[ERROR] ARSRS file not found at {arsrs_path}")
        sys.exit(1)
    with open(arsrs_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_user_prompt(arsrs: dict) -> str:
    """Build the user prompt from ARSRS data."""
    system_name = (
        arsrs.get("project_profile", {}).get("goal", "")
        or arsrs.get("system_name", "Enterprise System")
    )
    domain = (
        arsrs.get("domain_context", {}).get("industry", "")
        or arsrs.get("project_profile", {}).get("domain", "General")
    )
    modules = ", ".join(arsrs.get("modules", []))

    # Compact requirements summary
    func_reqs = arsrs.get("functional_requirements", [])
    req_lines = []
    for r in func_reqs[:5]:
        if isinstance(r, dict):
            req_lines.append(f"- {r.get('title', r.get('description', 'Requirement'))}")
        else:
            req_lines.append(f"- {r}")
    requirements_summary = "\n".join(req_lines) if req_lines else "- Standard CRUD operations for all modules"

    # Compact workflows summary
    workflows = arsrs.get("workflows", [])
    wf_lines = []
    for wf in workflows[:5]:
        if isinstance(wf, dict):
            name = wf.get("name", "Workflow")
            steps = " → ".join(wf.get("steps", [])[:4])
            wf_lines.append(f"- {name}: {steps}")
    workflows_summary = "\n".join(wf_lines) if wf_lines else "- Standard application workflows"

    return USER_PROMPT_TEMPLATE.format(
        system_name=system_name,
        domain=domain,
        modules=modules,
        requirements_summary=requirements_summary,
        workflows_summary=workflows_summary,
    )


def call_llm(user_prompt: str) -> tuple[str, float]:
    """Make a single LLM call with json_object response format. Returns (raw_text, latency)."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ai-architecture-platform.local",
        "X-Title": "SAE Phase 0 Test",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": MAX_TOKENS,
        "response_format": {"type": "json_object"},
    }

    t0 = time.perf_counter()
    with httpx.Client(timeout=float(TIMEOUT)) as client:
        resp = client.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers)
        latency = time.perf_counter() - t0

    if resp.status_code == 429:
        raise RuntimeError(f"Rate limited (HTTP 429). Latency: {latency:.1f}s")

    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError(f"Empty choices in response: {data}")

    content = choices[0].get("message", {}).get("content", "")
    usage = data.get("usage", {})
    
    print(f"    Tokens: prompt={usage.get('prompt_tokens', '?')}, "
          f"completion={usage.get('completion_tokens', '?')}, "
          f"latency={latency:.1f}s")
    
    return content, latency


def validate_response(raw_text: str) -> tuple[bool, BackendLLDResponse | None, str]:
    """Validate raw LLM text against the flat BackendLLDResponse model.
    
    Returns (success, parsed_model_or_None, error_message).
    """
    dict_data = None

    # Step 1: Try clean JSON parse first (do NOT run repair regex unless needed!)
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        first_nl = cleaned.find("\n")
        if first_nl != -1:
            cleaned = cleaned[first_nl + 1:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

    try:
        dict_data = json.loads(cleaned, strict=False)
    except Exception:
        # Step 2: Fallback to repair_json_string only when direct parse fails
        try:
            json_str = repair_json_string(cleaned)
            dict_data = json.loads(json_str, strict=False)
        except Exception as e:
            return False, None, f"JSON parse & repair failed: {e}"

    if not isinstance(dict_data, dict):
        return False, None, f"Expected dict, got {type(dict_data).__name__}"

    # Auto-unwrap if wrapped under a root container key (e.g. {"backend_lld": {...}} or {"backend_design": {...}})
    for unwrap_key in ["backend_lld", "backend_design", "backend", "lld", "data", "result"]:
        if unwrap_key in dict_data and isinstance(dict_data[unwrap_key], dict):
            dict_data = dict_data[unwrap_key]
            break

    # Normalize common key variations
    key_aliases = {
        "endpoints": "api_endpoints",
        "apis": "api_endpoints",
        "domain_entities": "domain_models",
        "entities": "domain_models",
        "daos": "repositories",
        "data_access": "repositories",
        "application_services": "services",
    }
    for alias, target in key_aliases.items():
        if alias in dict_data and target not in dict_data:
            dict_data[target] = dict_data.pop(alias)

    # Step 3: Validate against flat Pydantic model
    try:
        model = BackendLLDResponse.model_validate(dict_data)
        return True, model, ""
    except Exception as e:
        return False, None, f"Pydantic validation failed: {e}"


def check_quality(model: BackendLLDResponse) -> dict:
    """Check content richness of the validated response."""
    return {
        "api_endpoints": len(model.api_endpoints),
        "services": len(model.services),
        "domain_models": len(model.domain_models),
        "repositories": len(model.repositories),
        "has_project_structure": bool(model.project_structure),
        "has_framework_config": bool(model.framework_config),
        "has_security_config": bool(model.security_config),
        "has_error_handling": bool(model.error_handling),
        "dependencies_count": len(model.dependencies),
        "patterns_count": len(model.architecture_patterns),
    }


def main():
    print("=" * 60)
    print(" PHASE 0 — Backend LLD Quick Win Test")
    print("=" * 60)
    print(f" Model      : {MODEL}")
    print(f" Max Tokens : {MAX_TOKENS}")
    print(f" Mode       : response_format=json_object (NO schema injection)")
    print(f" Runs       : {NUM_RUNS}")
    print("=" * 60)

    if not API_KEY:
        print("\n[ERROR] OPENROUTER_API_KEY not set in .env")
        sys.exit(1)

    arsrs = load_arsrs()
    user_prompt = build_user_prompt(arsrs)

    print(f"\nUser prompt length: {len(user_prompt)} chars")
    print(f"System prompt length: {len(SYSTEM_PROMPT)} chars")
    print(f"Total prompt: ~{len(user_prompt) + len(SYSTEM_PROMPT)} chars\n")

    results = []
    for i in range(1, NUM_RUNS + 1):
        print(f"--- Run {i}/{NUM_RUNS} ---", flush=True)
        print(f"    Sending request to {MODEL}...", flush=True)
        try:
            raw_text, latency = call_llm(user_prompt)
            success, model, error = validate_response(raw_text)

            if success and model:
                quality = check_quality(model)
                # Check for substantial content (not just empty lists)
                non_empty_fields = sum(1 for v in quality.values() if v and v != 0)
                total_fields = len(quality)
                fill_rate = non_empty_fields / total_fields * 100

                results.append({
                    "run": i,
                    "success": True,  
                    "latency": round(latency, 1),
                    "quality": quality,
                    "fill_rate": fill_rate,
                })
                print(f"    [PASS] Fill rate: {fill_rate:.0f}% "
                      f"({non_empty_fields}/{total_fields} fields populated)", flush=True)
                print(f"       APIs: {quality['api_endpoints']}, "
                      f"Services: {quality['services']}, "
                      f"Models: {quality['domain_models']}, "
                      f"Repos: {quality['repositories']}", flush=True)
            else:
                results.append({
                    "run": i,
                    "success": False,
                    "latency": round(latency, 1),
                    "error": error,
                })
                print(f"    [FAIL] {error[:120]}", flush=True)

                # Save failed response for debugging
                fail_path = PROJECT_ROOT / "outputs" / f"phase0_fail_run{i}.txt"
                fail_path.parent.mkdir(parents=True, exist_ok=True)
                with open(fail_path, "w", encoding="utf-8") as f:
                    f.write(raw_text)
                print(f"       Raw response saved to: {fail_path}")

        except KeyboardInterrupt:
            print("\n[STOP] Interrupted by user.")
            break
        except Exception as e:
            results.append({"run": i, "success": False, "latency": 0, "error": str(e)})
            print(f"    [ERROR] {str(e)[:120]}")

        # Small delay between runs to avoid rate limiting
        if i < NUM_RUNS:
            time.sleep(2)

    # ─── Summary ─────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(" RESULTS SUMMARY")
    print("=" * 60)

    successes = [r for r in results if r.get("success")]
    failures = [r for r in results if not r.get("success")]

    total_runs = len(results)
    success_rate = len(successes) / total_runs * 100 if total_runs else 0
    avg_latency = sum(r["latency"] for r in results) / total_runs if total_runs else 0

    print(f" Total Runs    : {total_runs}")
    print(f" Successes     : {len(successes)}")
    print(f" Failures      : {len(failures)}")
    print(f" Success Rate  : {success_rate:.0f}%")
    print(f" Avg Latency   : {avg_latency:.1f}s")

    if successes:
        avg_fill = sum(r["fill_rate"] for r in successes) / len(successes)
        print(f" Avg Fill Rate : {avg_fill:.0f}%")

        # Average quality metrics
        avg_q = {}
        for key in successes[0]["quality"]:
            vals = [r["quality"][key] for r in successes]
            if isinstance(vals[0], bool):
                avg_q[key] = f"{sum(vals)}/{len(vals)}"
            else:
                avg_q[key] = f"{sum(vals)/len(vals):.1f}"
        print(f" Avg Quality   : {json.dumps(avg_q, indent=2)}")

    if failures:
        print(f"\n Failed runs:")
        for f in failures:
            print(f"   Run {f['run']}: {f.get('error', 'Unknown')[:100]}")

    target_met = success_rate >= 90
    print(f"\n {'[TARGET MET]' if target_met else '[TARGET NOT MET]'}: "
          f"≥90% valid-output rate → {success_rate:.0f}%")
    print("=" * 60)

    # Save full results
    results_path = PROJECT_ROOT / "outputs" / "phase0_results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({"model": MODEL, "max_tokens": MAX_TOKENS, "results": results}, f, indent=2)
    print(f"\nFull results saved to: {results_path}")


if __name__ == "__main__":
    main()
