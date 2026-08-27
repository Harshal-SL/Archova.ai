"""Response schemas for API v1 Generation endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class InterviewQuestionSchema(BaseModel):
    """Schema representing an interview question presented to the user."""

    question_id: str = Field(..., description="Unique question identifier.")
    question: str = Field(..., description="The clarification question text.")
    options: List[str] = Field(
        default_factory=list,
        description="Suggested choice options (empty if free-form).",
    )
    default_option: Optional[str] = Field(
        default=None,
        description="Recommended default option for the question.",
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Technical context/rationale behind this question.",
    )
    target_section: Optional[str] = Field(
        default=None,
        description="Target section in the requirement context.",
    )
    target_field: Optional[str] = Field(
        default=None,
        description="Target parameter field being clarified.",
    )
    priority: Optional[str] = Field(
        default=None,
        description="Priority level ('high', 'medium', 'low').",
    )


class StartGenerationResponse(BaseModel):
    """Response returned when initiating a generation workflow."""

    generation_id: str = Field(..., description="Unique ID for this generation lifecycle.")
    status: str = Field(..., description="Current status, e.g. INTERVIEW_IN_PROGRESS or INTERVIEW_COMPLETED.")
    current_question: Optional[InterviewQuestionSchema] = Field(
        default=None,
        description="The first interview question to answer (if questions were generated).",
    )


class SubmitAnswerResponse(BaseModel):
    """Response returned after submitting an interview answer."""

    generation_id: str = Field(..., description="Unique generation ID.")
    status: str = Field(..., description="INTERVIEW_IN_PROGRESS or INTERVIEW_COMPLETED.")
    next_question: Optional[InterviewQuestionSchema] = Field(
        default=None,
        description="The next interview question to answer, if more questions remain.",
    )


class GenerateArchitectureResponse(BaseModel):
    """Response returned when ARSRS and HLD have been generated."""

    generation_id: str = Field(..., description="Unique generation ID.")
    status: str = Field(..., description="Overall status, typically HLD_READY.")
    arsrs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Architecture-Ready Structured Requirement Specification (ARSRS).",
    )
    hld: Dict[str, Any] = Field(
        default_factory=dict,
        description="High Level Design (HLD) specification.",
    )


class GenerationStatusResponse(BaseModel):
    """Status polling response for the generation lifecycle and background tasks."""

    generation_id: str = Field(..., description="Unique generation ID.")
    status: str = Field(..., description="Overall generation status.")
    interview: str = Field(..., description="Interview status: IN_PROGRESS or COMPLETED.")
    arsrs: str = Field(..., description="ARSRS status: NOT_STARTED, GENERATING, READY, or FAILED.")
    hld: str = Field(..., description="HLD status: NOT_STARTED, GENERATING, READY, or FAILED.")
    llds: Dict[str, str] = Field(
        default_factory=dict,
        description="Per-LLD generation status (e.g. backend: READY, frontend: GENERATING).",
    )


class ArtifactResponse(BaseModel):
    """Generic artifact retrieval response (e.g. for ARSRS or HLD)."""

    generation_id: str = Field(..., description="Unique generation ID.")
    status: str = Field(..., description="Artifact status: NOT_STARTED, GENERATING, READY, or FAILED.")
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The artifact payload if ready.",
    )
    message: Optional[str] = Field(
        default=None,
        description="Optional status message or hint.",
    )


class LLDDetailResponse(BaseModel):
    """Response for a specific Low Level Design (LLD) section."""

    generation_id: str = Field(..., description="Unique generation ID.")
    lld_type: str = Field(..., description="Type of LLD requested (e.g. backend, frontend).")
    status: str = Field(..., description="LLD status: NOT_STARTED, GENERATING, READY, or FAILED.")
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The generated LLD payload if READY.",
    )
    message: Optional[str] = Field(
        default=None,
        description="Information message if not yet ready or not started.",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error details if the LLD generation failed.",
    )


class LogEntrySchema(BaseModel):
    """Single chronological execution log entry."""

    timestamp: str = Field(..., description="Log timestamp formatted as HH:MM:SS.")
    stage: str = Field(..., description="Pipeline stage, e.g. REE, SAE, INTERVIEW, LLD_BACKEND.")
    message: str = Field(..., description="Log message text.")
    level: str = Field(default="INFO", description="Log severity level (INFO, WARNING, ERROR).")


class GenerationLogsResponse(BaseModel):
    """Response model for retrieving generation logs."""

    generation_id: str = Field(..., description="Unique generation ID.")
    count: int = Field(..., description="Total count of log entries.")
    logs: List[LogEntrySchema] = Field(default_factory=list, description="Chronological log entries.")
