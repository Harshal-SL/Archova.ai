"""Input Data Models representing AI Engine Architecture JSON payloads."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterator, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ArchitecturePackageInput(BaseModel):
    """Input payload model representing the AI Engine's complete architecture JSON."""

    model_config = ConfigDict(extra="allow")

    package_id: str = Field(default="", description="Package ID or generation ID")
    generation_id: str = Field(default="", description="Unique generation run ID")
    prompt: str = Field(default="", description="Original user requirement prompt")
    status: Optional[str] = Field(default="COMPLETED")
    arsrs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Architecture-Ready Structured Requirement Specification",
    )
    hld: Dict[str, Any] = Field(
        default_factory=dict,
        description="High-Level Design architecture payload",
    )
    cac: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Canonical Architecture Contract (if present)",
    )
    llds: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of 5 LLD sections (backend, frontend, database, security, cloud)",
    )
    raw_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Full raw dictionary payload",
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_input_payload(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # If data is passed as {package_id: ..., data: ...}
        if "data" in data and isinstance(data["data"], dict) and ("hld" in data["data"] or "arsrs" in data["data"] or "llds" in data["data"]):
            inner = data["data"]
            merged = dict(inner)
            merged["package_id"] = data.get("package_id") or inner.get("generation_id") or inner.get("package_id") or "arch_pkg"
            merged["raw_data"] = inner
            return merged

        # If payload is wrapped inside an 'architecture' envelope
        if "architecture" in data and isinstance(data["architecture"], dict):
            inner = data["architecture"]
            merged = dict(inner)
            for k, v in data.items():
                if k != "architecture" and k not in merged:
                    merged[k] = v
            merged["package_id"] = merged.get("package_id") or merged.get("generation_id") or "arch_pkg"
            merged["raw_data"] = data
            return merged

        merged = dict(data)
        if not merged.get("package_id"):
            merged["package_id"] = merged.get("generation_id") or "arch_pkg"
        merged["raw_data"] = data
        return merged

    # ── Dict-like compatibility interface ──
    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get method."""
        if hasattr(self, key):
            val = getattr(self, key)
            if val is not None and val != "" and val != {} and val != []:
                return val
        if self.raw_data and key in self.raw_data:
            return self.raw_data[key]
        return default

    def __getitem__(self, key: str) -> Any:
        """Dict-like indexing."""
        if hasattr(self, key):
            val = getattr(self, key)
            if val is not None and val != "" and val != {} and val != []:
                return val
        if self.raw_data and key in self.raw_data:
            return self.raw_data[key]
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Dict-like key check."""
        if hasattr(self, key) and getattr(self, key) is not None:
            return True
        return bool(self.raw_data and key in self.raw_data)

    def keys(self) -> List[str]:
        if self.raw_data:
            return list(self.raw_data.keys())
        return list(self.model_dump(mode="json").keys())

    def items(self) -> Iterator[tuple[str, Any]]:
        if self.raw_data:
            return iter(self.raw_data.items())
        return iter(self.model_dump(mode="json").items())

    @property
    def data(self) -> Dict[str, Any]:
        """Return the dictionary representation of the architecture package."""
        if self.raw_data:
            return self.raw_data
        return self.model_dump(mode="json")

    def get_system_name(self) -> str:
        """Extract the system name from prompt, arsrs, hld, or metadata."""
        prompt = self.prompt or self.data.get("prompt", "")
        # Extract title from prompt if starting with "Build an ... System"
        m = re.search(r"^(?:Build|Design|Create|Develop)\s+(?:an?\s+)?([^.]+?)(?:\.|$)", prompt, re.IGNORECASE)
        if m and len(m.group(1).strip()) > 3:
            return m.group(1).strip().title()

        name = (
            self.arsrs.get("system_name")
            or self.hld.get("system_name")
            or self.data.get("system_name")
            or self.data.get("requirement_analysis", {}).get("system_name")
        )
        if name and name.lower() not in ["software architecture", "general distributed system"]:
            return name

        return "Smart System Architecture"

    def get_domain(self) -> str:
        """Extract the domain intelligently from prompt, domain concepts, or arsrs."""
        prompt = (self.prompt or self.data.get("prompt", "")).lower()

        # Domain recognition rules from prompt keywords
        if any(k in prompt for k in ["parking", "vehicle", "traffic", "transit", "toll", "fleet"]):
            return "IoT & Smart Transportation / Parking"
        if any(k in prompt for k in ["payment", "fintech", "banking", "wallet", "ledger"]):
            return "Financial Technology & Payment Processing"
        if any(k in prompt for k in ["food", "restaurant", "delivery", "kitchen"]):
            return "Food Services & Delivery Logistics"
        if any(k in prompt for k in ["streaming", "video", "audio", "media", "music"]):
            return "Digital Media & Content Streaming"
        if any(k in prompt for k in ["chat", "messaging", "collaboration", "social"]):
            return "Real-Time Messaging & Collaboration"
        if any(k in prompt for k in ["ecommerce", "shopping", "store", "order", "inventory"]):
            return "E-Commerce & Retail Supply Chain"
        if any(k in prompt for k in ["healthcare", "hospital", "clinic", "patient", "medical"]):
            return "Healthcare & Medical Informatics"

        domain = (
            self.arsrs.get("domain")
            or self.arsrs.get("domain_context", {}).get("industry")
            or self.hld.get("domain")
            or self.data.get("domain")
            or self.data.get("requirement_analysis", {}).get("domain")
        )
        if domain and domain.lower() not in ["software engineering & enterprise saas", "general distributed system"]:
            return domain

        return "Enterprise SaaS & Distributed Systems"

    def get_hld(self) -> Dict[str, Any]:
        """Extract HLD section."""
        return self.hld or self.data.get("hld") or {}

    def get_arsrs(self) -> Dict[str, Any]:
        """Extract ARSRS section."""
        return self.arsrs or self.data.get("arsrs") or self.data.get("requirement_analysis") or {}

    def get_functional_requirements(self) -> List[Dict[str, Any]]:
        """Extract functional requirements from arsrs or root."""
        arsrs_data = self.get_arsrs()
        reqs = arsrs_data.get("functional_requirements", []) or arsrs_data.get("requirements", [])
        if not reqs:
            reqs = self.data.get("functional_requirements", [])
        return reqs if isinstance(reqs, list) else []

    def get_nfrs(self) -> List[Dict[str, Any]]:
        """Extract non-functional requirements from arsrs or root."""
        arsrs_data = self.get_arsrs()
        nfrs = (
            arsrs_data.get("non_functional_requirements", [])
            or arsrs_data.get("nfrs", [])
            or arsrs_data.get("quality_attributes", [])
        )
        if not nfrs:
            nfrs = self.data.get("non_functional_requirements", [])
        return nfrs if isinstance(nfrs, list) else []

    def get_llds(self) -> Dict[str, Any]:
        """Extract LLDs dictionary."""
        return self.llds or self.data.get("llds") or {}

    def _unwrap_lld(self, raw_lld: Any) -> Dict[str, Any]:
        """Unwrap LLD data if nested inside a status/data/error wrapper."""
        if not isinstance(raw_lld, dict):
            return {}
        if "data" in raw_lld and isinstance(raw_lld["data"], dict):
            return raw_lld["data"]
        return raw_lld

    def get_backend_lld(self) -> Dict[str, Any]:
        """Extract Backend LLD unwrapping inner data payload."""
        llds = self.get_llds()
        raw = llds.get("backend") or llds.get("backend_lld") or self.data.get("backend_lld") or {}
        return self._unwrap_lld(raw)

    def get_database_lld(self) -> Dict[str, Any]:
        """Extract Database LLD unwrapping inner data payload."""
        llds = self.get_llds()
        raw = llds.get("database") or llds.get("database_lld") or self.data.get("database_lld") or {}
        return self._unwrap_lld(raw)

    def get_frontend_lld(self) -> Dict[str, Any]:
        """Extract Frontend LLD unwrapping inner data payload."""
        llds = self.get_llds()
        raw = llds.get("frontend") or llds.get("frontend_lld") or self.data.get("frontend_lld") or {}
        return self._unwrap_lld(raw)

    def get_security_lld(self) -> Dict[str, Any]:
        """Extract Security LLD unwrapping inner data payload."""
        llds = self.get_llds()
        raw = llds.get("security") or llds.get("security_lld") or self.data.get("security_lld") or {}
        return self._unwrap_lld(raw)

    def get_cloud_lld(self) -> Dict[str, Any]:
        """Extract Cloud LLD unwrapping inner data payload."""
        llds = self.get_llds()
        raw = llds.get("cloud") or llds.get("cloud_lld") or self.data.get("cloud_lld") or {}
        return self._unwrap_lld(raw)
