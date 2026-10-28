# Feedback Injection Proposal for AI Engine (Proposal ONLY - Do Not Apply)

**Status:** Proposed Architecture RFC  
**Target Subsystems:** `ai_engine/app/api/routes/generations.py`, `ai_engine/app/services/generation_service.py`, `ai_engine/app/sae/agents/`  
**Author:** Validator Engine v2 Integration Team  

---

## 1. Executive Summary

Validator Engine v2 produces rich, deterministic diagnostic feedback (Layer 0 schema defects, Layer 1 static analysis findings, Layer 3 rubric critiques with JSON pointers, and Layer 4 real-world benchmark alignment gaps). Currently, `ai_engine` applies rule-based heuristic patching in `generation_service.apply_correction_feedback_to_package` or runs unguided regeneration.

This RFC outlines a minimal, zero-breaking-change proposal allowing the AI Engine to accept an optional `feedback` payload when regenerating an individual artifact (HLD or any of the 5 LLDs). The feedback is injected directly into the target agent's system/user prompt so the generative model can fix flagged issues while preserving already accepted decisions.

---

## 2. API Surface: Endpoint in `routes/generations.py`

### Proposed Endpoint
Add a dedicated artifact regeneration endpoint in [`ai_engine/app/api/routes/generations.py`](file:///d:/Archova.ai/ai_engine/app/api/routes/generations.py):

```python
from pydantic import BaseModel, Field

class RegenerateArtifactRequest(BaseModel):
    artifact: str = Field(..., description="Target artifact: 'hld' | 'backend' | 'database' | 'frontend' | 'security' | 'cloud'")
    feedback: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured correction feedback from Validator Engine (findings, missing capabilities, real-world gaps)"
    )

@router.post(
    "/{generation_id}/regenerate-artifact",
    response_model=ArtifactResponse,
    status_code=status.HTTP_200_OK,
    summary="Regenerate an individual architecture artifact with optional correction feedback",
)
async def regenerate_artifact_endpoint(
    generation_id: str,
    payload: RegenerateArtifactRequest,
) -> ArtifactResponse:
    try:
        updated_artifact = await generation_service.regenerate_single_artifact(
            generation_id=generation_id,
            artifact=payload.artifact,
            feedback=payload.feedback,
        )
        return ArtifactResponse(
            generation_id=generation_id,
            artifact_type=payload.artifact,
            data=updated_artifact,
            status="READY",
        )
    except KeyError as k_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(k_err))
    except ValueError as v_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_err))
```

---

## 3. Orchestration: Service Method in `generation_service.py`

In [`ai_engine/app/services/generation_service.py`](file:///d:/Archova.ai/ai_engine/app/services/generation_service.py), add method `regenerate_single_artifact`:

```python
async def regenerate_single_artifact(
    self,
    generation_id: str,
    artifact: str,
    feedback: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    context = self.get_context(generation_id)
    if not context:
        raise KeyError(f"Generation '{generation_id}' not found.")

    artifact_lower = artifact.lower()
    arsrs = context.arsrs or {}
    hld = context.hld or {}
    cac = context.cac

    # Dispatch to the specific generation agent with feedback
    if artifact_lower == "backend":
        agent = BackendLLDGenerationAgent()
        result = await agent.generate(
            hld=hld,
            arsrs=arsrs,
            cac=cac,
            feedback=feedback,  # <-- Injected optional parameter
        )
        context.llds["backend"] = LLDState(status="READY", data=result)
    elif artifact_lower == "database":
        agent = DatabaseLLDGenerationAgent()
        result = await agent.generate(
            hld=hld,
            arsrs=arsrs,
            cac=cac,
            feedback=feedback,
        )
        context.llds["database"] = LLDState(status="READY", data=result)
    # ... other LLDs and HLD handled analogously ...

    # Persist updated package to disk
    self._save_package_to_disk(context)
    return result
```

---

## 4. Agent Prompt Injection Pattern

Each SAE agent class (e.g., [`BackendLLDGenerationAgent`](file:///d:/Archova.ai/ai_engine/app/sae/agents/backend_lld_generation_agent.py), [`DatabaseLLDGenerationAgent`](file:///d:/Archova.ai/ai_engine/app/sae/agents/database_lld_generation_agent.py)) defines a `generate(...)` method building an LLM prompt.

### Injection Logic
Inside `agent.generate(..., feedback: Optional[Dict[str, Any]] = None)`:

```python
feedback_section = ""
if feedback:
    findings = feedback.get("findings", [])
    rw_gaps = feedback.get("real_world_gaps", [])
    instructions = feedback.get("instructions", [])

    lines = ["\n### VALIDATION CRITIQUE & REQUIRED CORRECTIONS (FROM PRIOR ITERATION):"]
    if instructions:
        lines.append("General Instructions:")
        for inst in instructions:
            lines.append(f"- {inst}")
    if findings:
        lines.append("\nSpecific Defects Flagged:")
        for f in findings:
            lines.append(f"- [{f.get('severity', 'HIGH').upper()}] {f.get('rule_id')}: {f.get('message')}")
            if f.get('suggested_fix'):
                lines.append(f"  Recommended Fix: {f.get('suggested_fix')}")
    if rw_gaps:
        lines.append("\nReal-World Alignment Deficits:")
        for gap in rw_gaps:
            lines.append(f"- {gap.get('pattern_name')} (Reference: {gap.get('reference_system')}):")
            lines.append(f"  Gap: {gap.get('why_applicable')}")
            lines.append(f"  Requirement: {gap.get('what_to_add')}")
    lines.append("\nCRITICAL CONSTRAINT: Address every flagged deficit above without altering valid architectural decisions.")
    feedback_section = "\n".join(lines) + "\n\n"

# The prompt builder appends feedback_section before the artifact schema template
full_user_prompt = f"{base_context_prompt}\n{feedback_section}\n{schema_instructions}"
```

---

## 5. Backward Compatibility Guarantees

1. **Parameter Defaults**: `feedback: Optional[Dict[str, Any]] = None` defaults to `None`. All existing calls in `SAEPipeline` and batch generation continue functioning identically without modification.
2. **Deterministic Output Shape**: The endpoint returns standard `ArtifactResponse` identical to existing `GET /{generation_id}/lld/{lld_type}` responses.
3. **Additive Routes**: No existing route in `routes/generations.py` is removed or modified.
4. **Graceful Fallback**: If an unknown feedback format is passed, the stringifier handles missing keys without throwing exceptions.

---

## 6. Verification and Testing Strategy

1. **Unit Test (`ai_engine/tests/unit/test_feedback_prompt_builder.py`)**:
   - Call `agent.build_prompt(..., feedback=canned_feedback)`.
   - Assert `feedback_section` appears in the prompt string containing the expected rule IDs and messages.
   - Call without `feedback` and assert the prompt string is bit-for-bit identical to baseline.
2. **API Route Test (`ai_engine/tests/unit/test_regenerate_artifact_route.py`)**:
   - Mock `generation_service.regenerate_single_artifact` returning a canned dict.
   - Send `POST /api/v1/generations/{generation_id}/regenerate-artifact` with payload `{"artifact": "database", "feedback": {"findings": [...]}}`.
   - Assert HTTP 200 and schema validity.
3. **Integration Test (`Validator_Engine_v2` with `HttpRegenerationAdapter`)**:
   - Execute multi-round loop against running AI Engine.
   - Verify `regenerated_with_feedback` flag transitions to `True`.
