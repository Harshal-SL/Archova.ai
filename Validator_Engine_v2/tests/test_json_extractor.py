import pytest
from Validator_Engine_v2.review.llm_client import _extract_first_json


def test_preamble_before_json():
    text = """We need to evaluate the frontend artifact against the rubric dimensions and reference patterns. Provide a comprehensive analysis.
    {
      "dimensions": [
        {"id": "view_route_coverage", "score": 4, "evidence_path": "/pages", "rationale": "All pages covered"},
        {"id": "api_binding_and_state", "score": 4, "evidence_path": "/api", "rationale": "State is valid"}
      ],
      "findings": []
    }"""
    parsed = _extract_first_json(text)
    assert parsed is not None
    assert "dimensions" in parsed
    assert len(parsed["dimensions"]) == 2
    assert parsed["dimensions"][0]["score"] == 4


def test_unclosed_truncated_json():
    text = """We need to produce a JSON output with dimensions and findings.
    {
      "dimensions": [
        {"id": "view_route_coverage", "score": 4, "rationale": "Valid views"},
        {"id": "api_binding_and_state", "score": 5, "rationale": "Valid state"""
    parsed = _extract_first_json(text)
    assert parsed is not None
    assert "dimensions" in parsed
    assert len(parsed["dimensions"]) >= 1


def test_regex_salvage_fallback():
    text = """We reviewed the frontend artifact. Results:
    "id": "view_route_coverage", "score": 4
    "id": "api_binding_and_state", "score": 5
    """
    parsed = _extract_first_json(text)
    assert parsed is not None
    assert "dimensions" in parsed
    assert len(parsed["dimensions"]) == 2
    assert parsed["dimensions"][0]["id"] == "view_route_coverage"
    assert parsed["dimensions"][0]["score"] == 4

