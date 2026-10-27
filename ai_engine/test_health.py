#!/usr/bin/env python3
"""
Archova AI Architecture Engine — Health & Diagnostics Suite
Verifies:
  1. All 4 OpenRouter API keys (Authentication, Credits, and Live Inference).
  2. All agent-configured AI models from .env (Slug validity, free tier access, response latency).
  3. The Agent-to-Key mapping matrix used by REE & SAE parallel agents.

Usage:
  py test_health.py
  (or from root: py ai_engine/test_health.py)
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── 1. Locate and Load .env ────────────────────────────────────────────────────

def find_and_load_env():
    possible_paths = [
        Path(__file__).resolve().parent / "app" / ".env",
        Path.cwd() / "app" / ".env",
        Path.cwd() / ".env",
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent.parent / "ai_engine" / ".env",
    ]
    env_file = None
    for p in possible_paths:
        if p.is_file():
            env_file = p
            break

    env_vars = {}
    if env_file:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    env_vars[k] = v
                    os.environ[k] = v
    return env_file, env_vars

ENV_FILE, ENV_VARS = find_and_load_env()

# ── ANSI Terminal Colors ───────────────────────────────────────────────────────

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

# Windows color support
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

def mask_key(k: str) -> str:
    if not k:
        return "<NOT_SET>"
    if len(k) <= 16:
        return k[:4] + "..." + k[-4:]
    return k[:13] + "..." + k[-4:]

# ── HTTP Helper ────────────────────────────────────────────────────────────────

def request_json(url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, data: Optional[Dict[str, Any]] = None, timeout: int = 15) -> Tuple[int, Any, Optional[str]]:
    hdr = {
        "User-Agent": "Archova-HealthCheck/2.0",
        "Accept": "application/json",
    }
    if headers:
        hdr.update(headers)

    payload = None
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        hdr["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=payload, headers=hdr, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body
            return resp.status, parsed, None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body
        return e.code, parsed, str(e)
    except Exception as e:
        return 0, None, str(e)

# ── API Key Tests ──────────────────────────────────────────────────────────────

def test_single_key(key_name: str, key_val: str, test_model: str) -> Dict[str, Any]:
    result = {
        "name": key_name,
        "key_masked": mask_key(key_val),
        "auth_ok": False,
        "credits": None,
        "free_limit": None,
        "inference_ok": False,
        "latency_ms": 0,
        "status": "UNKNOWN",
        "detail": "",
    }

    if not key_val:
        result["status"] = "MISSING"
        result["detail"] = "Key not configured in .env"
        return result

    headers = {"Authorization": f"Bearer {key_val}"}

    # 1. Auth & Account check
    status, auth_data, err = request_json("https://openrouter.ai/api/v1/auth/key", headers=headers)
    if status == 200 and isinstance(auth_data, dict):
        result["auth_ok"] = True
        info = auth_data.get("data", {})
        free_reqs = info.get("free_model_daily_requests", {})
        result["free_limit"] = f"{free_reqs.get('used', 0)}/{free_reqs.get('limit', 0)} used"
    else:
        result["status"] = "AUTH_FAILED"
        result["detail"] = f"HTTP {status}: {err or auth_data}"
        return result

    # 2. Credits check
    c_status, c_data, _ = request_json("https://openrouter.ai/api/v1/credits", headers=headers)
    if c_status == 200 and isinstance(c_data, dict):
        creds = c_data.get("data", {}).get("total_credits", 0)
        result["credits"] = f"${creds:.2f}"

    # 3. Live Inference test
    t0 = time.perf_counter()
    chat_payload = {
        "model": test_model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5,
    }
    chat_status, chat_data, chat_err = request_json(
        "https://openrouter.ai/api/v1/chat/completions",
        method="POST",
        headers=headers,
        data=chat_payload,
        timeout=20,
    )
    result["latency_ms"] = int((time.perf_counter() - t0) * 1000)

    if chat_status == 200:
        result["inference_ok"] = True
        result["status"] = "ACTIVE"
        result["detail"] = "Authentication & Inference functioning normally"
    elif chat_status == 403:
        err_msg = ""
        if isinstance(chat_data, dict):
            err_msg = chat_data.get("error", {}).get("message", "")
        result["status"] = "BLOCKED"
        result["detail"] = err_msg or "Inference blocked by OpenRouter"
    elif chat_status == 429:
        result["status"] = "RATE_LIMITED"
        result["detail"] = "Rate limit reached on this key"
    else:
        result["status"] = f"HTTP_{chat_status}"
        result["detail"] = str(chat_data or chat_err)[:100]

    return result

# ── Model Tests ────────────────────────────────────────────────────────────────

def test_model_availability(model_id: str, active_key: Optional[str], catalog: Dict[str, Any]) -> Dict[str, Any]:
    result = {
        "model": model_id,
        "in_catalog": False,
        "is_free": False,
        "inference_ok": False,
        "latency_ms": 0,
        "detail": "",
    }

    entry = catalog.get(model_id)
    if entry:
        result["in_catalog"] = True
        pricing = entry.get("pricing", {})
        prompt_cost = float(pricing.get("prompt", 0) or 0)
        compl_cost = float(pricing.get("completion", 0) or 0)
        result["is_free"] = (prompt_cost == 0.0 and compl_cost == 0.0)
    else:
        result["detail"] = "Model slug not found in OpenRouter catalog"
        return result

    if not active_key:
        result["detail"] = "No working key available to test generation"
        return result

    # Test inference
    t0 = time.perf_counter()
    headers = {"Authorization": f"Bearer {active_key}"}
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "respond 'ok'"}],
        "max_tokens": 5,
    }
    status, data, err = request_json(
        "https://openrouter.ai/api/v1/chat/completions",
        method="POST",
        headers=headers,
        data=payload,
        timeout=20,
    )
    result["latency_ms"] = int((time.perf_counter() - t0) * 1000)

    if status == 200:
        result["inference_ok"] = True
        result["detail"] = "Ready"
    else:
        err_msg = ""
        if isinstance(data, dict):
            err_msg = data.get("error", {}).get("message", "")
        result["detail"] = f"HTTP {status}: {err_msg or err}"[:80]

    return result

# ── Main Runner ────────────────────────────────────────────────────────────────

def main():
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 75}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  Archova AI Engine — Multi-Key & Model Diagnostics Tool{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 75}{Colors.RESET}")

    if ENV_FILE:
        print(f" Loaded .env: {Colors.BOLD}{ENV_FILE}{Colors.RESET}\n")
    else:
        print(f" {Colors.YELLOW}Warning: No .env file found. Using existing environment variables.{Colors.RESET}\n")

    # 1. Collect Keys
    keys_to_test = [
        ("OPENROUTER_API_KEY_1", os.getenv("OPENROUTER_API_KEY_1", "")),
        ("OPENROUTER_API_KEY_2", os.getenv("OPENROUTER_API_KEY_2", "")),
        ("OPENROUTER_API_KEY_3", os.getenv("OPENROUTER_API_KEY_3", "")),
        ("OPENROUTER_API_KEY_4", os.getenv("OPENROUTER_API_KEY_4", "")),
    ]
    if os.getenv("OPENROUTER_API_KEY") and os.getenv("OPENROUTER_API_KEY") not in [v for _, v in keys_to_test]:
        keys_to_test.append(("OPENROUTER_API_KEY (Default)", os.getenv("OPENROUTER_API_KEY", "")))

    # Fetch live OpenRouter catalog
    print(f"{Colors.DIM}Fetching live OpenRouter models catalog...{Colors.RESET}", end="", flush=True)
    status, catalog_data, _ = request_json("https://openrouter.ai/api/v1/models")
    catalog: Dict[str, Any] = {}
    if status == 200 and isinstance(catalog_data, dict):
        for m in catalog_data.get("data", []):
            if "id" in m:
                catalog[m["id"]] = m
        print(f" {Colors.GREEN}Done ({len(catalog)} models){Colors.RESET}\n")
    else:
        print(f" {Colors.RED}Failed to fetch catalog (HTTP {status}){Colors.RESET}\n")

    # Determine probe model for key tests
    test_probe_model = os.getenv("LLM_MODEL", "nvidia/nemotron-3.5-lightning:free")
    if test_probe_model not in catalog:
        # fallback to any free model
        free_candidates = [m_id for m_id, m in catalog.items() if m.get("pricing", {}).get("prompt") == "0"]
        if free_candidates:
            test_probe_model = free_candidates[0]

    # ════════════════════════════════════════════════════════════════════════════
    # PART 1: TEST ALL API KEYS
    # ════════════════════════════════════════════════════════════════════════════
    print(f"{Colors.BOLD}── 1. API Keys Health & Quota ──────────────────────────────────────────{Colors.RESET}")
    key_results = []
    first_working_key = None

    for name, val in keys_to_test:
        print(f" Testing {Colors.BOLD}{name:<25}{Colors.RESET} [{mask_key(val)}] ... ", end="", flush=True)
        res = test_single_key(name, val, test_probe_model)
        key_results.append(res)

        if res["status"] == "ACTIVE":
            print(f"{Colors.GREEN}[ACTIVE] (HTTP 200, {res['latency_ms']}ms){Colors.RESET}")
            if not first_working_key:
                first_working_key = val
        elif res["status"] == "BLOCKED":
            print(f"{Colors.RED}[BLOCKED] (HTTP 403 Forbidden){Colors.RESET}")
        elif res["status"] == "AUTH_FAILED":
            print(f"{Colors.RED}[INVALID] (Auth Failed){Colors.RESET}")
        elif res["status"] == "MISSING":
            print(f"{Colors.YELLOW}[MISSING]{Colors.RESET}")
        else:
            print(f"{Colors.RED}[{res['status']}]{Colors.RESET}")

    # Print Key Detail Table
    print("\n Key Details:")
    print(f" {'Key Name':<28} {'Masked Token':<20} {'Credits':<10} {'Inference':<15} {'Diagnosis'}")
    print(f" {'-'*28} {'-'*20} {'-'*10} {'-'*15} {'-'*25}")
    for r in key_results:
        color = Colors.GREEN if r["status"] == "ACTIVE" else (Colors.YELLOW if r["status"] == "MISSING" else Colors.RED)
        creds = r["credits"] or "$0.00"
        inf_badge = f"{color}{r['status']}{Colors.RESET}"
        print(f" {r['name']:<28} {r['key_masked']:<20} {creds:<10} {inf_badge:<24} {r['detail'][:40]}")

    # ════════════════════════════════════════════════════════════════════════════
    # PART 2: TEST CONFIGURED MODELS
    # ════════════════════════════════════════════════════════════════════════════
    print(f"\n{Colors.BOLD}── 2. Configured Models Health ─────────────────────────────────────────{Colors.RESET}")

    model_vars = [
        ("LLM_MODEL (Global Default)", os.getenv("LLM_MODEL", "")),
        ("FALLBACK_MODEL", os.getenv("FALLBACK_MODEL", "")),
        ("MODEL_INPUT_UNDERSTANDING", os.getenv("MODEL_INPUT_UNDERSTANDING", "")),
        ("MODEL_REQUIREMENT_ENGINEER", os.getenv("MODEL_REQUIREMENT_ENGINEER", "")),
        ("MODEL_BUSINESS_ANALYST", os.getenv("MODEL_BUSINESS_ANALYST", "")),
        ("MODEL_DOMAIN_EXPERT", os.getenv("MODEL_DOMAIN_EXPERT", "")),
        ("MODEL_REQUIREMENT_REVIEW", os.getenv("MODEL_REQUIREMENT_REVIEW", "")),
        ("MODEL_INTERVIEW", os.getenv("MODEL_INTERVIEW", "")),
        ("MODEL_BACKEND", os.getenv("MODEL_BACKEND", "")),
        ("MODEL_DATABASE", os.getenv("MODEL_DATABASE", "")),
        ("MODEL_FRONTEND", os.getenv("MODEL_FRONTEND", "")),
        ("MODEL_SECURITY", os.getenv("MODEL_SECURITY", "")),
        ("MODEL_CLOUD", os.getenv("MODEL_CLOUD", "")),
    ]

    # Deduplicate unique models
    unique_models = {}
    for var_name, m_id in model_vars:
        if m_id:
            if m_id not in unique_models:
                unique_models[m_id] = []
            unique_models[m_id].append(var_name)

    # Use first working key or key 1 for probing
    probe_key = first_working_key or (keys_to_test[0][1] if keys_to_test else None)

    model_results = []
    for m_id, used_by in unique_models.items():
        res = test_model_availability(m_id, probe_key, catalog)
        model_results.append((m_id, used_by, res))

    print(f" {'Model Slug':<48} {'Catalog':<10} {'Free?':<8} {'Inference':<14} {'Status'}")
    print(f" {'-'*48} {'-'*10} {'-'*8} {'-'*14} {'-'*20}")

    for m_id, used_by, r in model_results:
        cat_str = f"{Colors.GREEN}Found{Colors.RESET}" if r["in_catalog"] else f"{Colors.RED}Not Found{Colors.RESET}"
        free_str = f"{Colors.GREEN}Yes{Colors.RESET}" if r["is_free"] else f"{Colors.YELLOW}Paid{Colors.RESET}"

        if r["inference_ok"]:
            inf_str = f"{Colors.GREEN}PASS ({r['latency_ms']}ms){Colors.RESET}"
        elif not first_working_key:
            inf_str = f"{Colors.YELLOW}Untested (Keys 403){Colors.RESET}"
        else:
            inf_str = f"{Colors.RED}FAIL{Colors.RESET}"

        status_text = r["detail"]
        print(f" {m_id:<48} {cat_str:<19} {free_str:<17} {inf_str:<23} {status_text[:30]}")

    # ════════════════════════════════════════════════════════════════════════════
    # PART 3: AGENT-TO-KEY MAPPING MATRIX
    # ════════════════════════════════════════════════════════════════════════════
    print(f"\n{Colors.BOLD}── 3. Agent Key Distribution Matrix ────────────────────────────────────{Colors.RESET}")
    print(" Verifies the dedicated API Key assigned to each parallel AI agent:\n")

    matrix = [
        ("InputUnderstanding", "MODEL_INPUT_UNDERSTANDING", os.getenv("MODEL_INPUT_UNDERSTANDING", ""), "OPENROUTER_API_KEY_1 (Key #1)"),
        ("RequirementEngineer", "MODEL_REQUIREMENT_ENGINEER", os.getenv("MODEL_REQUIREMENT_ENGINEER", ""), "OPENROUTER_API_KEY_1 (Key #1)"),
        ("BusinessAnalyst", "MODEL_BUSINESS_ANALYST", os.getenv("MODEL_BUSINESS_ANALYST", ""), "OPENROUTER_API_KEY_2 (Key #2)"),
        ("DomainExpert", "MODEL_DOMAIN_EXPERT", os.getenv("MODEL_DOMAIN_EXPERT", ""), "OPENROUTER_API_KEY_3 (Key #3)"),
        ("RequirementReview", "MODEL_REQUIREMENT_REVIEW", os.getenv("MODEL_REQUIREMENT_REVIEW", ""), "OPENROUTER_API_KEY_4 (Key #4)"),
        ("ClarificationInterview", "MODEL_INTERVIEW", os.getenv("MODEL_INTERVIEW", ""), "OPENROUTER_API_KEY_4 (Key #4)"),
    ]

    print(f" {'Agent Specialist':<25} {'Assigned Key':<28} {'Model':<40} {'Health'}")
    print(f" {'-'*25} {'-'*28} {'-'*40} {'-'*15}")

    for agent_name, var_name, model_name, key_assigned in matrix:
        # Check key status
        k_num = 1
        if "Key #2" in key_assigned: k_num = 2
        elif "Key #3" in key_assigned: k_num = 3
        elif "Key #4" in key_assigned: k_num = 4

        key_stat = key_results[k_num - 1]["status"] if (k_num - 1) < len(key_results) else "UNKNOWN"
        if key_stat == "ACTIVE":
            health = f"{Colors.GREEN}READY{Colors.RESET}"
        elif key_stat == "BLOCKED":
            health = f"{Colors.RED}BLOCKED (Key #{k_num} 403){Colors.RESET}"
        else:
            health = f"{Colors.YELLOW}{key_stat}{Colors.RESET}"

        print(f" {agent_name:<25} {key_assigned:<28} {model_name:<40} {health}")

    # ════════════════════════════════════════════════════════════════════════════
    # PART 4: SUMMARY & ACTIONABLE RECOMMENDATIONS
    # ════════════════════════════════════════════════════════════════════════════
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 75}{Colors.RESET}")
    print(f"{Colors.BOLD}  Diagnostic Summary & Recommendations{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 75}{Colors.RESET}")

    active_count = sum(1 for r in key_results if r["status"] == "ACTIVE")
    blocked_count = sum(1 for r in key_results if r["status"] == "BLOCKED")

    if active_count == len(key_results):
        print(f"\n {Colors.GREEN}✓ All {active_count} API keys are healthy and active! Full parallel agent generation ready.{Colors.RESET}")
    elif blocked_count > 0:
        print(f"\n {Colors.RED}✗ {blocked_count} of {len(key_results)} API keys are BLOCKED (HTTP 403) by OpenRouter.{Colors.RESET}")
        print(f"\n {Colors.BOLD}Recommended Actions:{Colors.RESET}")
        print(f"  1. Log into your OpenRouter account at {Colors.CYAN}https://openrouter.ai{Colors.RESET} to check for required email/phone verification.")
        print(f"  2. If using newly registered free accounts, OpenRouter may flag rapid multi-accounting from the same IP.")
        print(f"  3. Alternatively, deposit $5 on a single OpenRouter account to unlock unrestricted access, then set:")
        print(f"     {Colors.BOLD}OPENROUTER_API_KEY_1=your_new_key{Colors.RESET}")
        print(f"     {Colors.BOLD}OPENROUTER_API_KEY_2=your_new_key{Colors.RESET}")
        print(f"     {Colors.BOLD}OPENROUTER_API_KEY_3=your_new_key{Colors.RESET}")
        print(f"     {Colors.BOLD}OPENROUTER_API_KEY_4=your_new_key{Colors.RESET}")
    print()

if __name__ == "__main__":
    main()
