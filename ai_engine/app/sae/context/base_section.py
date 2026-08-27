"""BaseSection model for dynamic SDC section registry with lifecycle status."""

from datetime import datetime, timezone
from typing import Any, Dict, Union
from pydantic import BaseModel, Field

from app.sae.utils.enums import AgentRole, SectionStatus, SectionType


class BaseSection(BaseModel):
    """Dynamic section container stored inside the Shared Design Context registry.

    Allows future domain agents (AI, Mobile, Analytics, etc.) to register custom
    sections without modifying the core SDC model.
    """

    section_id: str = Field(..., description="Unique section identifier e.g. hld, database_lld, mobile_lld")
    section_type: Union[SectionType, str] = Field(..., description="Section category identifier")
    owner: AgentRole = Field(..., description="Authorized owner role of this section")
    status: SectionStatus = Field(
        default=SectionStatus.PENDING,
        description="Lifecycle status of section (PENDING, GENERATING, GENERATED, VALIDATED, FAILED)"
    )
    version: int = Field(default=1, description="Version number of this individual section")
    last_modified: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of last modification"
    )
    content: Any = Field(default_factory=dict, description="Strongly typed content model or payload dictionary")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional section-level metadata")

    def increment_version(self) -> None:
        """Increment section version and update last_modified timestamp."""
        self.version += 1
        self.last_modified = datetime.now(timezone.utc)

    def set_status(self, status: SectionStatus) -> None:
        """Update section lifecycle status and last_modified timestamp."""
        self.status = status
        self.last_modified = datetime.now(timezone.utc)
