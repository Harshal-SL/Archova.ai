"""
REE Agent Package

Agents:
  - InputUnderstandingAgent   : Parses, normalizes, and merges stakeholder input
  - EngineeringTeamAgent      : Parallel coordinator for the AI Engineering Team
  - RequirementEngineerAgent  : Functional/NFRs, actors, modules, APIs, constraints
  - BusinessAnalystAgent      : Business goals, rules, stakeholders, KPIs
  - DomainExpertAgent         : Industry, compliance, scale, architecture patterns
  - RequirementReviewAgent    : Assesses completeness + flags gaps
  - InterviewModerator        : Adaptive stakeholder interview conductor
  - FinalizationAgent         : Assembles the ARSRS

Support modules:
  - BaseAIAgent     : Shared LLM call infrastructure for AI specialist agents
  - TextNormalizer  : Deterministic text processing (used by InputUnderstandingAgent)

All agents share the SharedRequirementContext (SRC) as their primary
communication medium. Agents NEVER communicate directly.
"""

from .input_understanding import InputUnderstandingAgent
from .engineering_team import EngineeringTeamAgent
from .requirement_engineer import RequirementEngineerAgent
from .business_analyst import BusinessAnalystAgent
from .domain_expert import DomainExpertAgent
from .requirement_review import RequirementReviewAgent
from .interview_moderator import InterviewModerator
from .finalizer import FinalizationAgent
from .text_normalizer import TextNormalizer
from .base_agent import BaseAIAgent

__all__ = [
    "InputUnderstandingAgent",
    "EngineeringTeamAgent",
    "RequirementEngineerAgent",
    "BusinessAnalystAgent",
    "DomainExpertAgent",
    "RequirementReviewAgent",
    "InterviewModerator",
    "FinalizationAgent",
    "TextNormalizer",
    "BaseAIAgent",
]
