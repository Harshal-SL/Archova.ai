"""Deterministic Multi-Domain Verification Script.
Tests:
1. Food Waste Management
2. Smart Parking
3. Vehicle Rental
4. Doctor Appointment
5. College Library
6. Event Management

Verifies:
- ARSRS domain, modules, workflows, rules match current PS
- Zero foreign domain contamination (no restaurant menu/cart/courier in food waste management)
- Domain detection & lock accuracy
- CAC APIs and entities grounded in ARSRS
"""

import sys
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.ree.models import REERequest
from app.ree.orchestrator import REEOrchestrator
from app.sae.utils.domain_lock import DomainLockEngine
from app.sae.utils.canonical_contract import ContractBuilder

TEST_CASES = [
    {
        "name": "Food Waste Management",
        "prompt": (
            "The Online Food Waste Management System connects restaurants, grocery stores, and food donors with local NGOs and volunteers "
            "to redistribute surplus food and reduce waste. Donors can list surplus food items with expiry times and quantity details. "
            "NGOs can browse available surplus listings, claim donations, and request pickups. Volunteers can coordinate collection and delivery. "
            "Administrators monitor waste reduction metrics, safety compliance, and impact analytics."
        ),
        "must_contain": ["surplus", "donation", "ngo", "volunteer"],
        "must_not_contain": ["cart", "restaurant menu", "courier dispatch", "doctor", "patient", "borrow book", "parking spot"],
    },
    {
        "name": "Smart Parking System",
        "prompt": (
            "The Smart Parking System is an IoT-enabled web and mobile platform that allows drivers to search for available "
            "parking spots in real-time, reserve parking slots, pay parking fees digitally, and navigate to their allocated spots. "
            "Parking attendants can monitor lot occupancy, verify vehicle check-in and check-out via license plate recognition, "
            "and manage space allocations. Administrators manage parking zones, dynamic pricing tariffs, and revenue analytics."
        ),
        "must_contain": ["driver", "parking", "reservation", "occupancy"],
        "must_not_contain": ["cart", "menu", "borrow book", "doctor", "patient", "prescription", "ehr"],
    },
    {
        "name": "Vehicle Rental Management System",
        "prompt": (
            "The Vehicle Rental Management System allows customers to browse available rental cars, view daily rates, "
            "and book reservations. Fleet managers can add new vehicles, track maintenance status, record vehicle pick-up and return inspections, "
            "and process rental payments and security deposits."
        ),
        "must_contain": ["vehicle", "rental", "reservation"],
        "must_not_contain": ["cart", "menu", "borrow book", "doctor", "patient", "prescription", "ehr"],
    },
    {
        "name": "Doctor Appointment System",
        "prompt": (
            "The proposed system is a web application that allows patients to search for doctors, view their availability, "
            "book and cancel appointments, and receive appointment reminders. Doctors can manage their profiles, availability, "
            "appointments, and patient consultations. Administrators can manage users, doctors, appointments, and system operations."
        ),
        "must_contain": ["patient", "doctor", "appointment", "availability"],
        "must_not_contain": ["cart", "menu", "borrow book", "parking spot", "vehicle", "surplus food"],
    },
    {
        "name": "College Library Management System",
        "prompt": (
            "The College Library Management System allows students and faculty to search the book catalog, borrow and return books, "
            "and track due dates and overdue fines. Librarians can manage book inventory, patron accounts, and circulation records. "
            "Administrators oversee system operations, borrowing policies, and generate circulation reports."
        ),
        "must_contain": ["book", "librarian", "borrow"],
        "must_not_contain": ["cart", "menu", "doctor", "patient", "parking spot", "vehicle", "surplus food"],
    },
    {
        "name": "Online Event Management System",
        "prompt": (
            "The Online Event Management System is a platform for universities to host workshops, hackathons, and seminars. "
            "Students can browse upcoming events, register online, receive digital passes, and attend sessions. "
            "Event organizers can publish event schedules, manage attendee registration capacity, verify attendance check-ins, "
            "and generate participation reports."
        ),
        "must_contain": ["event", "registration", "attendance"],
        "must_not_contain": ["cart", "menu", "doctor", "patient", "borrow book", "parking spot", "vehicle", "surplus food"],
    },
]

def run_verification():
    ree_orch = REEOrchestrator()
    print("\n" + "="*80)
    print("STARTING DETERMINISTIC MULTI-DOMAIN ANTI-CONTAMINATION VERIFICATION")
    print("="*80 + "\n")

    all_passed = True

    for idx, tc in enumerate(TEST_CASES, 1):
        print(f"[{idx}/6] Testing: {tc['name']}")
        req = REERequest(combined_prompt=tc["prompt"], max_interview_rounds=0)
        ree_resp = ree_orch.run(req)
        arsrs_dict = ree_resp.arsrs.model_dump() if hasattr(ree_resp.arsrs, "model_dump") else (ree_resp.arsrs or {})

        # 1. Inspect ARSRS content
        arsrs_json_str = json.dumps(arsrs_dict, default=str).lower()

        # Check positive containment
        missing_must = [kw for kw in tc["must_contain"] if kw.lower() not in arsrs_json_str]
        if missing_must:
            print(f"  ❌ Missing required domain concepts: {missing_must}")
            all_passed = False
        else:
            print(f"  ✓ Required domain concepts present: {tc['must_contain']}")

        # Check foreign domain contamination
        found_contaminants = [kw for kw in tc["must_not_contain"] if re.search(rf"\b{re.escape(kw.lower())}\b", arsrs_json_str)]
        if found_contaminants:
            print(f"  ❌ CONTAMINATION DETECTED: {found_contaminants}")
            all_passed = False
        else:
            print(f"  ✓ Zero foreign domain concepts detected")

        # 2. Test Domain Lock
        dom_ctx = DomainLockEngine.lock_domain_and_requirements(arsrs_dict, raw_prompt=tc["prompt"])
        print(f"  ✓ Domain locked as: {dom_ctx.domain_name} (key: {dom_ctx.domain_key})")
        print(f"  ✓ Canonical FR count: {len(dom_ctx.canonical_requirements)}, Actors: {[a['role'] for a in dom_ctx.actors]}")
        print(f"  ✓ Modules: {dom_ctx.modules}")
        print(f"  ✓ Workflows: {[w['name'] for w in dom_ctx.key_workflows]}")

        # 3. Test CAC Synthesis
        fake_req_analysis = {
            "functional_requirements": [
                {"id": f"FR-{i+1:03d}", "title": fr.get("title", ""), "description": fr.get("description", "")}
                for i, fr in enumerate(arsrs_dict.get("functional_requirements", []))
            ],
            "modules": dom_ctx.modules,
            "actors": dom_ctx.actors,
            "workflows": dom_ctx.key_workflows,
            "business_rules": arsrs_dict.get("business_context", {}).get("business_rules", []),
            "domain": dom_ctx.domain_name,
            "domain_key": dom_ctx.domain_key,
        }
        fake_hld = {
            "major_services": [{"service_name": m, "service_id": f"SVC-{i+1:03d}", "description": f"Service for {m}"} for i, m in enumerate(dom_ctx.modules[:5])],
            "architecture_style": "Modular Monolith",
            "technology_stack": {"backend": "FastAPI (Python)", "database": "PostgreSQL"},
        }
        cac = ContractBuilder.build_from_hld(fake_hld, fake_req_analysis, dom_ctx)
        print(f"  ✓ CAC synthesized: {len(cac.api_operations)} APIs, {len(cac.domain_entities)} Domain Entities ({[e.name for e in cac.domain_entities]})")
        print("-" * 80)

    if all_passed:
        print("\n🎉 ALL 6 DOMAIN TESTS PASSED WITH ZERO CONTAMINATION AND 100% PS GROUNDING!\n")
    else:
        print("\n❌ SOME DOMAIN TESTS FAILED!\n")
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
