"""Request schemas for API v1 Generation endpoints."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class StartGenerationRequest(BaseModel):
    """Request payload to initiate a new generation session with a problem statement."""

    prompt: str = Field(
        ...,
        min_length=1,
        description="Raw problem statement or stakeholder requirements text.",
        examples=["Build an online event management system for university hackathons."],
    )
    generation_id: Optional[str] = Field(
        default=None,
        description="Optional client-generated generation ID to enable immediate telemetry polling.",
    )


class SubmitAnswerRequest(BaseModel):
    """Request payload to submit an answer for an interview question."""

    question_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier of the question being answered.",
        examples=["Q1", "c7b1a2f0"],
    )
    answer: str = Field(
        ...,
        min_length=1,
        description="Stakeholder's response to the interview question.",
        examples=["Target audience is university students and organizers with up to 5,000 attendees."],
    )
