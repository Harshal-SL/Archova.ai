"""
Design output validation and normalization.

Provides functions to validate and normalize HLD/LLD structures
from Ollama generation, handling legacy formats and missing fields.
"""

from __future__ import annotations

from copy import deepcopy


def _as_str(value, default: str = "") -> str:
    """Convert value to string with fallback."""
    if value is None:
        return default
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else default
    return str(value)


def _as_list(value) -> list:
    """Convert value to list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _as_dict(value) -> dict:
    """Convert value to dict."""
    if isinstance(value, dict):
        return value
    return {}


def _as_bool(value, default: bool = False) -> bool:
    """Convert value to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
    return default


def _as_int(value, default: int = 0) -> int:
    """Convert value to int."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return default
    return default


_DEFAULT_CORE_COMPONENTS = [
    {
        "name": "Frontend",
        "type": "Client Layer",
        "description": "UI for users",
        "interacts_with": ["API Gateway"],
        "technology_options": ["React", "Angular"],
    },
    {
        "name": "API Gateway",
        "type": "Entry Layer",
        "description": "Handles routing, auth, rate limiting",
        "interacts_with": ["Auth Service", "Backend Services"],
        "technology_options": ["Kong", "NGINX"],
    },
    {
        "name": "Auth Service",
        "type": "Service",
        "description": "Authentication and authorization",
        "interacts_with": ["Database", "API Gateway"],
        "technology_options": ["Keycloak", "OAuth2 Server"],
    },
    {
        "name": "Core Backend Service",
        "type": "Service",
        "description": "Business logic handling",
        "interacts_with": ["Database", "Cache"],
        "technology_options": ["FastAPI", "Spring Boot"],
    },
    {
        "name": "Database",
        "type": "Storage",
        "description": "Persistent data storage",
        "interacts_with": ["Core Backend Service"],
        "technology_options": ["PostgreSQL", "MySQL"],
    },
    {
        "name": "Cache",
        "type": "Performance Layer",
        "description": "Stores frequently accessed data",
        "interacts_with": ["Core Backend Service"],
        "technology_options": ["Redis", "Memcached"],
    },
    {
        "name": "External Services",
        "type": "Third-party",
        "description": "Payments, APIs, AI models",
        "interacts_with": ["Core Backend Service"],
        "technology_options": ["REST", "Webhooks"],
    },
]


_LLD_COMPONENT_TEMPLATES = [
    {
        "name": "Frontend",
        "type": "Client",
        "pages": [{"name": "Home Page", "components": ["Navbar", "Search Bar", "Cards"]}],
        "state_management": {
            "tool": "Redux / Context API",
            "states": ["user", "data", "loading", "error"],
        },
        "api_integration": [{"endpoint": "/api/resource", "method": "GET"}],
    },
    {
        "name": "API Gateway",
        "type": "Routing Layer",
        "routes": [{"path": "/api/*", "destination": "Backend Services"}],
        "middleware": ["Authentication", "Rate Limiting", "Logging"],
    },
    {
        "name": "Backend Service",
        "type": "Business Logic",
        "modules": [{"name": "Core Module", "responsibility": "Main business logic"}],
        "classes": [
            {
                "name": "ServiceClass",
                "methods": [
                    {
                        "name": "processRequest",
                        "steps": ["Validate input", "Process logic", "Return response"],
                    }
                ],
            }
        ],
    },
    {
        "name": "Authentication Service",
        "type": "Security",
        "flows": ["User login", "Validate credentials", "Generate JWT", "Return token"],
    },
    {
        "name": "Database",
        "type": "Storage",
        "schema": {
            "tables": [
                {
                    "name": "entities",
                    "columns": [
                        {"name": "id", "type": "UUID"},
                        {"name": "field", "type": "String"},
                    ],
                }
            ]
        },
        "queries": [{"name": "findById", "query": "SELECT * FROM entities WHERE id = ?"}],
    },
    {
        "name": "Cache",
        "type": "Performance",
        "strategy": "Read-through / Write-through",
        "ttl": "300 seconds",
    },
    {
        "name": "External Integration",
        "type": "Third-party",
        "services": [{"name": "Payment API", "interaction": "REST", "data_format": "JSON"}],
    },
    {
        "name": "Error Handling",
        "type": "Cross-cutting",
        "exceptions": [{"name": "GenericException", "status": 500}],
    },
    {
        "name": "Logging",
        "type": "Monitoring",
        "levels": ["INFO", "ERROR"],
        "tools": ["ELK", "CloudWatch"],
    },
]


def _template_by_name() -> dict[str, dict]:
    """Index templates by lowercase component name."""
    return {item["name"].lower(): item for item in _LLD_COMPONENT_TEMPLATES}


def _fill_template(raw_value, template):
    """Fill template with raw values, coercing types."""
    if isinstance(template, dict):
        raw_dict = _as_dict(raw_value)
        return {key: _fill_template(raw_dict.get(key), default) for key, default in template.items()}

    if isinstance(template, list):
        if not isinstance(raw_value, list):
            return deepcopy(template)

        if not template:
            return [_as_str(item) for item in raw_value if _as_str(item)]

        item_template = template[0]
        if isinstance(item_template, dict):
            normalized = [_fill_template(item, item_template) for item in raw_value]
            return normalized or deepcopy(template)

        if isinstance(item_template, bool):
            normalized = [_as_bool(item, item_template) for item in raw_value]
            return normalized or deepcopy(template)

        if isinstance(item_template, int):
            normalized = [_as_int(item, item_template) for item in raw_value]
            return normalized or deepcopy(template)

        normalized = [_as_str(item) for item in raw_value if _as_str(item)]
        return normalized or deepcopy(template)

    if isinstance(template, bool):
        return _as_bool(raw_value, template)

    if isinstance(template, int):
        return _as_int(raw_value, template)

    return _as_str(raw_value, template)


def _normalize_references(model_refs, retrieval_refs: list[dict]) -> list[dict]:
    """Merge references from model and retrieval, deduplicate."""
    merged = []
    seen = set()

    for item in _as_list(model_refs):
        if isinstance(item, dict):
            source = _as_str(item.get("source"), "")
            why = _as_str(item.get("why_relevant"), "")
        else:
            source = _as_str(item, "")
            why = ""

        if not source or source in seen:
            continue

        merged.append({"source": source, "why_relevant": why})
        seen.add(source)

    for item in retrieval_refs:
        source = _as_str(item.get("source"), "")
        if not source or source in seen:
            continue

        merged.append(
            {
                "source": source,
                "why_relevant": _as_str(item.get("why_relevant"), "semantic retrieval match"),
            }
        )
        seen.add(source)

    return merged


def _normalize_hld(design_output: dict) -> dict:
    """Normalize HLD with defaults for missing fields."""
    hld_raw = _as_dict(design_output.get("high_level_design"))

    system_context = _as_str(hld_raw.get("system_context"), "")
    system_name = _as_str(hld_raw.get("system_name"), "Your Project Name")
    if system_name == "Your Project Name" and system_context:
        system_name = "Generated System"

    architecture_raw = _as_dict(hld_raw.get("architecture"))
    architecture_pattern = [_as_str(v) for v in _as_list(architecture_raw.get("pattern")) if _as_str(v)]
    if not architecture_pattern:
        architecture_pattern = ["Client-Server", "Layered", "Event-Driven"]

    actors = []
    for item in _as_list(hld_raw.get("actors")):
        raw_actor = _as_dict(item)
        if raw_actor:
            actor_name = _as_str(raw_actor.get("actor"), _as_str(raw_actor.get("name"), "User"))
            actor_description = _as_str(raw_actor.get("description"), "Not specified.")
        else:
            actor_name = _as_str(item, "User")
            actor_description = "Not specified."

        if actor_name:
            actors.append({"actor": actor_name, "description": actor_description})

    if not actors:
        actors = [
            {"actor": "User", "description": "End user interacting with system"},
            {"actor": "Admin", "description": "Manages system operations"},
        ]

    raw_components = _as_list(hld_raw.get("core_components"))
    if not raw_components:
        raw_components = _as_list(hld_raw.get("major_components"))

    core_components = []
    for item in raw_components:
        raw_component = _as_dict(item)
        if raw_component:
            component = {
                "name": _as_str(raw_component.get("name"), "Component"),
                "type": _as_str(raw_component.get("type"), "Service"),
                "description": _as_str(raw_component.get("description"), "Not specified."),
                "interacts_with": [_as_str(v) for v in _as_list(raw_component.get("interacts_with")) if _as_str(v)],
                "technology_options": [
                    _as_str(v) for v in _as_list(raw_component.get("technology_options")) if _as_str(v)
                ],
            }
        else:
            component = {
                "name": _as_str(item, "Component"),
                "type": "Service",
                "description": "Not specified.",
                "interacts_with": [],
                "technology_options": [],
            }

        if component["name"]:
            core_components.append(component)

    if not core_components:
        core_components = deepcopy(_DEFAULT_CORE_COMPONENTS)

    data_flow = []
    legacy_steps = []
    for item in _as_list(hld_raw.get("data_flow")):
        raw_flow = _as_dict(item)
        if raw_flow:
            use_case = _as_str(raw_flow.get("use_case"), "User Request Flow")
            steps = [_as_str(step) for step in _as_list(raw_flow.get("steps")) if _as_str(step)]
            if not steps:
                maybe_step = _as_str(raw_flow.get("description"), "")
                if maybe_step:
                    steps = [maybe_step]
            if steps:
                data_flow.append({"use_case": use_case, "steps": steps})
        else:
            step = _as_str(item)
            if step:
                legacy_steps.append(step)

    if legacy_steps:
        data_flow = [{"use_case": "User Request Flow", "steps": legacy_steps}]

    if not data_flow:
        data_flow = [
            {
                "use_case": "User Request Flow",
                "steps": [
                    "User interacts with Frontend",
                    "Frontend calls API Gateway",
                    "API Gateway authenticates request",
                    "Request forwarded to Backend Service",
                    "Backend interacts with Database/Cache",
                    "Response returned to Frontend",
                ],
            }
        ]

    scalability_raw = _as_dict(hld_raw.get("scalability"))
    legacy_scaling = [_as_str(v) for v in _as_list(hld_raw.get("scalability_strategy")) if _as_str(v)]

    security_raw = _as_dict(hld_raw.get("security"))
    legacy_security = [_as_str(v) for v in _as_list(hld_raw.get("security_strategy")) if _as_str(v)]
    data_security = [_as_str(v) for v in _as_list(security_raw.get("data_security")) if _as_str(v)]
    if not data_security:
        data_security = legacy_security or ["HTTPS", "Encryption"]

    nfr_raw = _as_dict(hld_raw.get("non_functional_requirements"))

    return {
        "system_name": system_name,
        "version": _as_str(hld_raw.get("version"), "1.0"),
        "description": _as_str(hld_raw.get("description"), system_context or "Brief description of the system"),
        "architecture": {
            "type": _as_str(
                architecture_raw.get("type"),
                _as_str(hld_raw.get("architecture_style"), "Microservices / Monolith / Hybrid"),
            ),
            "pattern": architecture_pattern,
            "deployment": _as_str(
                architecture_raw.get("deployment"),
                _as_str(hld_raw.get("deployment_topology"), "Cloud / On-Premise"),
            ),
        },
        "actors": actors,
        "core_components": core_components,
        "data_flow": data_flow,
        "scalability": {
            "approach": _as_str(
                scalability_raw.get("approach"),
                legacy_scaling[0] if legacy_scaling else "Horizontal scaling",
            ),
            "load_balancer": _as_str(scalability_raw.get("load_balancer"), "Yes"),
            "auto_scaling": _as_bool(scalability_raw.get("auto_scaling"), True),
        },
        "security": {
            "authentication": _as_str(security_raw.get("authentication"), "JWT / OAuth"),
            "authorization": _as_str(security_raw.get("authorization"), "RBAC"),
            "data_security": data_security,
        },
        "non_functional_requirements": {
            "availability": _as_str(nfr_raw.get("availability"), "99.9%"),
            "latency": _as_str(nfr_raw.get("latency"), "<200ms"),
            "throughput": _as_str(nfr_raw.get("throughput"), "High"),
            "fault_tolerance": _as_str(nfr_raw.get("fault_tolerance"), "Retry + Circuit Breaker"),
        },
    }


def _normalize_components_from_raw_lld(raw_lld: dict) -> list[dict]:
    """Extract and normalize components from LLD."""
    templates = _template_by_name()
    normalized_by_name: dict[str, dict] = {}
    extras: list[dict] = []

    for item in _as_list(raw_lld.get("components")):
        raw_component = _as_dict(item)
        name = _as_str(raw_component.get("name"), "")
        if not name:
            continue

        key = name.lower()
        if key in templates:
            normalized_by_name[key] = _fill_template(raw_component, templates[key])
        else:
            extras.append({"name": name, "type": _as_str(raw_component.get("type"), "Custom")})

    ordered = []
    for template in _LLD_COMPONENT_TEMPLATES:
        key = template["name"].lower()
        ordered.append(normalized_by_name.get(key, deepcopy(template)))
    ordered.extend(extras)
    return ordered


def _normalize_low_level_design(design_output: dict, hld: dict) -> dict:
    """Normalize LLD with defaults for missing fields."""
    raw_lld = _as_dict(design_output.get("low_level_design"))
    
    if _as_list(raw_lld.get("components")):
        components = _normalize_components_from_raw_lld(raw_lld)
    else:
        # Fallback to defaults
        components = deepcopy(_LLD_COMPONENT_TEMPLATES)

    return {
        "system_name": _as_str(raw_lld.get("system_name"), _as_str(hld.get("system_name"), "Your Project Name")),
        "version": _as_str(raw_lld.get("version"), _as_str(hld.get("version"), "1.0")),
        "components": components,
    }


def normalize_design_output(raw: dict, retrieval_refs: list[dict] | None = None) -> dict:
    """Normalize design output with validation and defaults.
    
    Args:
        raw: Raw design output from LLM or API
        retrieval_refs: References from RAG retrieval (sources to include)
    
    Returns:
        Normalized design dictionary with HLD, LLD, references, assumptions
    """
    if retrieval_refs is None:
        retrieval_refs = []
    
    root = _as_dict(raw)
    design_output = _as_dict(root.get("design_output")) if "design_output" in root else root

    high_level_design = _normalize_hld(design_output)
    low_level_design = _normalize_low_level_design(design_output, high_level_design)

    references = _normalize_references(design_output.get("references"), retrieval_refs)

    assumptions = [
        _as_str(item)
        for item in _as_list(design_output.get("assumptions"))
        if _as_str(item)
    ]
    if not assumptions and not references:
        assumptions = ["Limited corpus evidence was available for some design decisions."]

    return {
        "high_level_design": high_level_design,
        "low_level_design": low_level_design,
        "references": references,
        "assumptions": assumptions,
    }
