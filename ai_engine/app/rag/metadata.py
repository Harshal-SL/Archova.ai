"""
Metadata extraction for RAG documents.

Automatically generates structured metadata from file paths and content,
supporting rich filtering and categorization during retrieval.
"""

import re
from pathlib import Path
from typing import Dict, Any


def extract_metadata_from_path(file_path: Path, root: Path) -> Dict[str, Any]:
    """
    Extract metadata from the file path and folder structure.
    
    Args:
        file_path: Full path to the document.
        root: Root directory of the RAG corpus.
    
    Returns:
        Dictionary with extracted metadata fields.
    """
    rel_path = file_path.relative_to(root)
    parts = rel_path.parts
    
    # Example: technology_guides/redis.md
    if len(parts) >= 2:
        category = parts[0]
        filename = parts[-1]
    else:
        category = "uncategorized"
        filename = file_path.name
    
    # Extract title from filename
    title = filename.replace("_", " ").replace(".md", "").strip()
    title = re.sub(r'(\d+\.)+', '', title).strip()  # Remove leading numbers
    
    # Determine subcategory from filename patterns
    subcategory = _infer_subcategory(category, filename)
    
    # Extract keywords from title
    keywords = _extract_keywords(title)
    
    # Determine difficulty level
    difficulty = _infer_difficulty(category)
    
    # Determine domain
    domain = _infer_domain(category)
    
    return {
        "title": title,
        "category": category,
        "subcategory": subcategory,
        "source_file": filename,
        "relative_path": rel_path.as_posix(),
        "keywords": keywords,
        "document_type": "markdown",
        "difficulty": difficulty,
        "domain": domain,
    }


def _infer_subcategory(category: str, filename: str) -> str:
    """Infer subcategory from category and filename."""
    subcategory_map = {
        "cloud_architecture": _infer_cloud_subcategory,
        "technology_guides": _infer_tech_subcategory,
        "system_components": _infer_component_subcategory,
    }
    
    mapper = subcategory_map.get(category)
    if mapper:
        return mapper(filename)
    
    return category


def _infer_cloud_subcategory(filename: str) -> str:
    """Infer cloud architecture subcategory."""
    if "aws" in filename.lower():
        return "aws"
    if "azure" in filename.lower():
        return "azure"
    if "gcp" in filename.lower():
        return "gcp"
    if "multi" in filename.lower() or "region" in filename.lower():
        return "multi_cloud"
    if "disaster" in filename.lower():
        return "disaster_recovery"
    return "cloud_architecture"


def _infer_tech_subcategory(filename: str) -> str:
    """Infer technology subcategory."""
    if "database" in filename.lower() or any(db in filename.lower() for db in ["postgres", "mysql", "mongodb", "cassandra"]):
        return "database"
    if "cache" in filename.lower() or "redis" in filename.lower():
        return "caching"
    if "message" in filename.lower() or any(mq in filename.lower() for mq in ["kafka", "rabbitmq"]):
        return "messaging"
    if any(proxy in filename.lower() for proxy in ["nginx", "envoy"]):
        return "networking"
    if "kubernetes" in filename.lower() or "docker" in filename.lower():
        return "orchestration"
    return "technology"


def _infer_component_subcategory(filename: str) -> str:
    """Infer system component subcategory."""
    if any(word in filename.lower() for word in ["auth", "security", "encryption"]):
        return "security"
    if any(word in filename.lower() for word in ["notification", "email", "sms"]):
        return "communication"
    if any(word in filename.lower() for word in ["payment", "order", "inventory"]):
        return "commerce"
    if any(word in filename.lower() for word in ["search", "analytics", "logging"]):
        return "observability"
    return "service"


def _extract_keywords(title: str) -> list[str]:
    """Extract keywords from title."""
    # Split on common delimiters and filter small words
    stop_words = {"a", "an", "and", "or", "the", "is", "for", "with", "to", "from", "in", "on", "at", "by"}
    words = re.split(r'[\s\-_]+', title.lower())
    keywords = [w for w in words if w and len(w) > 2 and w not in stop_words]
    return keywords


def _infer_difficulty(category: str) -> str:
    """Infer difficulty level based on category."""
    easy_categories = {"hld_templates", "lld_templates", "domain_architectures"}
    medium_categories = {"architecture_decision_matrix", "system_components"}
    hard_categories = {"architecture_patterns", "scaling_techniques", "failure_modes"}
    
    if category in easy_categories:
        return "beginner"
    if category in medium_categories:
        return "intermediate"
    if category in hard_categories:
        return "advanced"
    return "intermediate"


def _infer_domain(category: str) -> str:
    """Infer domain based on category."""
    domain_map = {
        "cloud_architecture": "infrastructure",
        "technology_guides": "infrastructure",
        "system_components": "backend",
        "hld_templates": "architecture",
        "lld_templates": "architecture",
        "nfr_mapping": "architecture",
        "domain_architectures": "domain",
        "architecture_decision_matrix": "architecture",
        "production_readiness": "operations",
        "ai_systems": "ai",
    }
    return domain_map.get(category, "general")
