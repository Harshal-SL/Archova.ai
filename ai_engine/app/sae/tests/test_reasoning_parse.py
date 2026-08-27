"""Unit test to verify that parse_and_validate handles reasoning tags (<think>...</think>) and code blocks correctly."""

import pathlib
import sys
import unittest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.sae.providers.llm_provider import OpenRouterProvider
from app.sae.models.response_models import (
    TechAdvisorResponse,
    BackendLLDResponse,
    SecurityLLDResponse,
    RequirementAnalysisResponse,
)


class TestReasoningParse(unittest.TestCase):
    def setUp(self):
        self.provider = OpenRouterProvider()

    def test_parses_reasoning_and_code_blocks(self):
        raw_output = """<think>
Here is my chain of thought.
I am considering { "temporary": "structure", "options": [1, 2, 3] }.
Let's choose FastAPI.
</think>

```json
{
  "backend": {
    "selected_option": "FastAPI (Python)",
    "alternatives_considered": ["Express", "Spring Boot"],
    "reasoning": "Asynchronous high throughput",
    "satisfies": ["FR-001"]
  }
}
```"""
        parsed: TechAdvisorResponse = self.provider.parse_and_validate(
            raw_output, TechAdvisorResponse, agent_name="test_tech"
        )
        self.assertEqual(parsed.backend.get("selected_option"), "FastAPI (Python)")
        self.assertEqual(parsed.backend.get("satisfies"), ["FR-001"])

    def test_parses_direct_json_with_think_tags(self):
        raw_output = """<thought>
Step 1: Check requirements.
Step 2: Generate backend design.
</thought>
{
  "backend_lld": {
    "api_endpoints": [
      {
        "endpoint": "/api/v1/auth/login",
        "method": "POST",
        "handler_name": "login_handler",
        "description": "User login"
      }
    ],
    "services": [
      {
        "name": "AuthService",
        "methods": ["login", "logout"]
      }
    ]
  }
}"""
        parsed: BackendLLDResponse = self.provider.parse_and_validate(
            raw_output, BackendLLDResponse, agent_name="test_backend"
        )
        self.assertEqual(len(parsed.api_endpoints), 1)
        self.assertEqual(parsed.api_endpoints[0].get("endpoint"), "/api/v1/auth/login")
        self.assertEqual(len(parsed.services), 1)
        self.assertEqual(parsed.services[0].get("name"), "AuthService")

    def test_parses_reasoning_prose_before_json(self):
        # Simulates 30KB+ reasoning where JSON is at the very end and prose has invalid { characters
        raw_output = """Thinking Process:
1. First let's analyze threats. The user said { "need": "encryption" }.
2. We must protect against SQLi and XSS. Let's make sure auth uses JWT { algorithm: HS256 }.
3. Final design below.

{
  "authentication": {
    "auth_type": "OAuth2 with PKCE",
    "session_management": "JWT"
  },
  "threat_model": [
    {
      "threat": "SQL Injection",
      "mitigation": "Parameterized queries"
    }
  ]
}"""
        parsed: SecurityLLDResponse = self.provider.parse_and_validate(
            raw_output, SecurityLLDResponse, agent_name="test_security"
        )
        self.assertEqual(parsed.authentication.get("auth_type"), "OAuth2 with PKCE")
        self.assertEqual(len(parsed.threat_model), 1)
        self.assertEqual(parsed.threat_model[0].get("threat"), "SQL Injection")

    def test_parses_dict_constraints_in_requirement_analysis(self):
        raw_output = """{
  "system_name": "Library System",
  "system_type": "Web App",
  "domain": "Library",
  "constraints": [
    {"id": "CON-001", "title": "System behaviour", "description": "Auth, Search, Borrow", "category": "constraint"}
  ],
  "modules": [
    {"name": "Auth", "description": "Login/logout"}
  ]
}"""
        parsed: RequirementAnalysisResponse = self.provider.parse_and_validate(
            raw_output, RequirementAnalysisResponse, agent_name="test_req"
        )
        self.assertEqual(parsed.system_name, "Library System")
        self.assertEqual(len(parsed.constraints), 1)
        self.assertEqual(parsed.constraints[0].get("id"), "CON-001")


if __name__ == "__main__":
    unittest.main()
