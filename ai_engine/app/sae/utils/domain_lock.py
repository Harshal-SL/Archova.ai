"""Domain Lock & Canonical Requirements Engine for SAE v2.

Ensures domain classification, requirement extraction, actors, modules, workflows,
and domain gap analyses are deterministic, immutable, and strictly validated as the
single source of truth for all downstream agents.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Standard domain feature checklists for gap analysis and archetype grounding
DOMAIN_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "food_delivery": {
        "display_name": "Food Delivery & Quick Commerce",
        "keywords": ["food", "restaurant", "menu", "dish", "cuisine", "delivery partner", "driver", "courier", "kitchen", "meal", "grocery", "order food"],
        "checklist": [
            "Customer Identity & Address Management",
            "Restaurant & Menu Browsing, Search & Filtering",
            "Cart Management, Customization & Pricing Engine",
            "Payment Gateway Integration & Instant Settlement",
            "Order Processing & Kitchen Status Workflow",
            "Delivery Partner Dispatch & Real-Time GPS Tracking",
            "Push Notifications & Order Status Alerts",
            "Restaurant & Platform Admin Management Dashboards",
        ],
        "default_services": [
            "Identity & Access Service",
            "Restaurant & Menu Service",
            "Cart & Order Service",
            "Payment & Billing Service",
            "Delivery & Dispatch Service",
            "Real-Time Tracking Service",
            "Notification & Alert Service",
            "Reporting & Analytics Service",
        ],
        "default_actors": [
            {"role": "Customer", "description": "Browses restaurants, adds items to cart, places orders, and tracks delivery in real-time"},
            {"role": "Restaurant Staff", "description": "Manages menu items, pricing, operating hours, and updates order preparation status"},
            {"role": "Delivery Partner", "description": "Accepts delivery assignments, picks up food from restaurants, and delivers to customer addresses"},
            {"role": "Platform Administrator", "description": "Oversees platform operations, manages vendor onboarding, disputes, and analytics reports"},
        ],
        "default_modules": [
            "Authentication & Profile Management",
            "Restaurant & Menu Management",
            "Cart & Order Processing",
            "Payment & Settlement",
            "Delivery & Fleet Dispatch",
            "Real-Time GPS Tracking",
            "Notification Service",
            "Admin Dashboard & Analytics",
        ],
    },
    "event_management": {
        "display_name": "Event Management & Campus Activities",
        "keywords": ["event catalog", "workshop", "seminar", "hackathon", "cultural fest", "online registration", "seat capacity", "digital pass", "participant", "event organizer", "event attendee"],
        "checklist": [
            "User Authentication & Student/Admin Roles",
            "Event Catalog, Browsing & Filter by Category",
            "Online Event Registration & Seat Capacity Management",
            "Real-Time Event Notifications & Reminder Dispatch",
            "QR-Code / Check-in Attendance Tracking",
            "Participant Management & Registration Status Verification",
            "Admin Dashboard & Event Analytics Reporting",
        ],
        "default_services": [
            "Identity & Access Service",
            "Event Management Service",
            "Registration & Ticket Service",
            "Attendance Tracking Service",
            "Notification & Alert Service",
            "Reporting & Analytics Service",
        ],
        "default_actors": [
            {"role": "Student", "description": "Browses upcoming events, registers online, and views registration status"},
            {"role": "Administrator", "description": "Creates and manages events, monitors registrations, tracks attendance, and generates reports"},
        ],
        "default_modules": [
            "Authentication & Role Management",
            "Event Catalog & Scheduling",
            "Online Registration & Capacity",
            "Attendance Tracking & Verification",
            "Notification & Alerts",
            "Reporting & Analytics",
        ],
    },
    "library": {
        "display_name": "Education & Library Management",
        "keywords": ["library", "book", "borrow", "librarian", "patron", "isbn", "circulation", "overdue"],
        "checklist": [
            "User Authentication & Student/Librarian Roles",
            "Book Catalog Search, Filtering & Availability",
            "Borrowing & Return Circulation Transactions",
            "Due Date Tracking & Overdue Notification Reminders",
            "Hold Reservations Queue Management",
            "Fine Calculation & Overdue Penalty Processing",
            "Inventory Stock & Book Copy Management",
            "Administrative Audit Trail & Circulation Reports",
        ],
        "default_services": [
            "Authentication & Role Service",
            "Catalog & Search Service",
            "Circulation & Borrowing Service",
            "Notification & Reminder Service",
            "Inventory & Asset Service",
            "Reporting & Analytics Service",
        ],
        "default_actors": [
            {"role": "Student", "description": "Searches catalog, borrows available books, and returns items"},
            {"role": "Librarian", "description": "Manages book inventory, patron records, catalogs, and circulation policies"},
        ],
        "default_modules": [
            "Authentication & Access Control",
            "Book & Catalog Management",
            "Borrowing & Circulation",
            "Return & Overdue Management",
        ],
    },
    "ecommerce": {
        "display_name": "E-Commerce & Digital Commerce",
        "keywords": ["cart", "checkout", "product", "order", "payment", "inventory", "store", "shop", "shipping"],
        "checklist": [
            "Customer Identity & Profile Management",
            "Product Catalog & Multi-Faceted Search",
            "Shopping Cart & Checkout Workflow",
            "Payment Gateway Integration & Webhooks",
            "Order Processing & Fulfillment Tracking",
            "Real-Time Inventory Stock Reservation",
            "Discounts, Vouchers & Promo Engine",
            "Admin Inventory & Order Management",
        ],
        "default_services": [
            "Auth & Customer Service",
            "Product Catalog Service",
            "Cart & Checkout Service",
            "Order Processing Service",
            "Payment Service",
            "Inventory Management Service",
        ],
        "default_actors": [
            {"role": "Customer", "description": "Browses catalog, adds products to cart, and completes checkout"},
            {"role": "Store Admin", "description": "Manages inventory, orders, prices, and fulfillments"},
        ],
        "default_modules": [
            "User & Account Management",
            "Product Catalog & Search",
            "Cart & Order Processing",
            "Payment & Settlement",
        ],
    },
    "healthcare": {
        "display_name": "Healthcare & Electronic Health Records",
        "keywords": ["patient", "doctor", "clinic", "hospital", "ehr", "medical", "prescription", "hipaa"],
        "checklist": [
            "Patient & Practitioner Identity Management",
            "Appointment Scheduling & Availability Calendar",
            "Electronic Health Records (EHR) & Clinical Notes",
            "HIPAA Consent & Audit Log Trail",
            "Prescription & Diagnostic Test Orders",
            "Secure Patient Messaging Portal",
            "Insurance Verification & Billing Claims",
        ],
        "default_services": [
            "Identity & Access Service",
            "Appointment Scheduling Service",
            "EHR & Medical Records Service",
            "Prescription Service",
            "Audit & Compliance Service",
        ],
        "default_actors": [
            {"role": "Patient", "description": "Views medical records, schedules appointments, and messages clinic"},
            {"role": "Practitioner", "description": "Records clinical notes, manages schedule, and writes prescriptions"},
        ],
        "default_modules": [
            "Patient Portal & Identity",
            "Appointment Scheduling",
            "EHR Clinical Notes",
            "Prescriptions & Orders",
        ],
    },
    "fintech": {
        "display_name": "Financial Services & Banking",
        "keywords": ["bank", "wallet", "transaction", "transfer", "account", "ledger", "kyc", "fraud", "loan"],
        "checklist": [
            "Customer Onboarding & KYC Verification",
            "Account Balance & Double-Entry Ledger",
            "Peer-to-Peer & Wire Fund Transfers",
            "Fraud Detection & Risk Scoring",
            "Transaction History & Statement Generation",
            "Regulatory Compliance & Reporting",
        ],
        "default_services": [
            "Auth & KYC Service",
            "Account & Ledger Service",
            "Payment Transfer Service",
            "Fraud & Risk Service",
            "Statement & Analytics Service",
        ],
        "default_actors": [
            {"role": "Account Holder", "description": "Initiates transfers, views balances, and downloads statements"},
            {"role": "Compliance Officer", "description": "Audits transactions, flags suspicious activity, and verifies KYC"},
        ],
        "default_modules": [
            "Identity & KYC Verification",
            "Account & Balance Ledger",
            "Payment & Transfers",
            "Audit & Risk Management",
        ],
    },
    "saas": {
        "display_name": "Enterprise SaaS Platform",
        "keywords": ["tenant", "subscription", "workspace", "billing", "api key", "team", "organization"],
        "checklist": [
            "Multi-Tenant Provisioning & Organization Management",
            "Role-Based Access Control & Team Invitations",
            "Subscription Billing & Metered Usage Tracking",
            "API Key Generation & Rate Limiting",
            "Audit Logging & Security Activity Feed",
            "Dashboard Analytics & Data Export",
        ],
        "default_services": [
            "Tenant & Auth Service",
            "Subscription & Billing Service",
            "API Gateway & Rate Limiter",
            "Audit & Activity Service",
            "Analytics Service",
        ],
        "default_actors": [
            {"role": "Workspace Member", "description": "Collaborates on team assets and executes workflows"},
            {"role": "Organization Admin", "description": "Manages billing, member seats, API keys, and security settings"},
        ],
        "default_modules": [
            "Multi-Tenant Organization Management",
            "User Access & Permissions",
            "Billing & Subscriptions",
            "Activity & Audit Log",
        ],
    },
    # ── Appointment Scheduling: narrow scope, NO EHR/clinical/prescription expansion ──
    "appointment_scheduling": {
        "display_name": "Healthcare Appointment Management",
        "keywords": [
            "appointment", "book appointment", "schedule appointment", "doctor availability", "slot availability",
            "doctor search", "doctor profile", "time slot", "cancellation policy",
            "double-booking", "appointment reminder", "booking confirmation",
        ],
        "checklist": [
            "Patient & Doctor Identity & Profile Management",
            "Doctor Search, Filtering & Profile Browsing",
            "Doctor Availability Calendar & Time Slot Management",
            "Appointment Booking, Rescheduling & Cancellation",
            "Double-Booking Prevention & Conflict Detection",
            "Appointment Reminder & Notification Dispatch",
            "Admin Dashboard: User, Doctor & Appointment Management",
        ],
        "default_services": [
            "Identity & Auth Service",
            "Doctor Search & Profile Service",
            "Availability & Scheduling Service",
            "Appointment Management Service",
            "Notification & Reminder Service",
            "Admin Management Service",
        ],
        "default_actors": [
            {"role": "Patient", "description": "Searches doctors, views availability, books and manages appointments, receives reminders"},
            {"role": "Doctor", "description": "Manages profile, sets availability, views and manages appointment calendar"},
            {"role": "System Administrator", "description": "Manages user accounts, doctors, appointments, and system operations"},
        ],
        "default_modules": [
            "Authentication & Access Control",
            "Doctor Search & Profile Management",
            "Appointment Scheduling & Booking",
            "Appointment Rescheduling & Cancellation",
            "Appointment Reminder & Notifications",
        ],
    },
    # ── Inventory & Stock Management ─────────────────────────────────────────
    "inventory_management": {
        "display_name": "Inventory & Stock Management",
        "keywords": [
            "inventory", "stock", "warehouse", "sku", "supplier", "stock-in", "stock-out",
            "reorder", "low-stock", "inventory tracking", "stock level", "restock", "item catalog",
            "product", "item", "goods", "catalog", "purchase", "sale", "batch", "location",
        ],
        "checklist": [
            "Product Catalog & SKU Management",
            "Supplier & Vendor Relationship Management",
            "Stock-In (Goods Receipt) Transaction Processing",
            "Stock-Out (Goods Issue) Transaction Processing",
            "Real-Time Multi-Warehouse Stock Level Tracking",
            "Low-Stock Automated Alerts & Reorder Thresholds",
            "Immutable Inventory Transaction Audit Logs",
            "Role-Based Access Control (Admin, Manager, Staff)",
            "Inventory Valuation & Movement Reports Dashboard",
        ],
        "default_services": [
            "Identity & Access Service",
            "Product Catalog Service",
            "Inventory & Stock Service",
            "Supplier & Vendor Service",
            "Alert & Notification Service",
            "Reporting & Analytics Service",
        ],
        "default_actors": [
            {"role": "Inventory Manager", "description": "Monitors stock levels, sets reorder thresholds, and manages supplier orders"},
            {"role": "Warehouse Staff", "description": "Executes stock-in and stock-out transactions and scans inventory SKUs"},
            {"role": "System Administrator", "description": "Manages user accounts, system configuration, and audit logs"},
        ],
        "default_modules": [
            "Authentication & Access Control",
            "Product Catalog & SKU Management",
            "Stock & Inventory Tracking",
            "Supplier & Vendor Management",
            "Low-Stock Alerts & Notifications",
            "Inventory Reporting & Analytics",
        ],
    },
    # ── Education & Learning Management ──────────────────────────────────────
    "learning_management": {
        "display_name": "Education & Learning Management",
        "keywords": [
            "course", "lms", "learning management", "enrollment", "assignment", "submission",
            "instructor", "student", "syllabus", "lecture", "quiz", "grade", "academic progress",
            "learning material", "course catalog",
        ],
        "checklist": [
            "Course Catalog & Syllabus Module Management",
            "Student Enrollment & Registration Processing",
            "Learning Content Delivery & Video Playback",
            "Assignment Submission & Automated Grading",
            "Student Academic Progress & Analytics Tracking",
            "Instructor Announcements & Discussion Forums",
            "Role-Based Access Control (Student, Instructor, Admin)",
        ],
        "default_services": [
            "Identity & Auth Service",
            "Course Catalog Service",
            "Enrollment & Progress Service",
            "Assignment & Grading Service",
            "Content Delivery Service",
            "Reporting & Analytics Service",
        ],
        "default_actors": [
            {"role": "Student", "description": "Enrolls in courses, accesses materials, submits assignments, and views grades"},
            {"role": "Instructor", "description": "Creates syllabus modules, uploads content, and grades student submissions"},
            {"role": "System Administrator", "description": "Manages user accounts, course approvals, and institutional reporting"},
        ],
        "default_modules": [
            "Authentication & Access Control",
            "Course Catalog & Content Management",
            "Student Enrollment & Progress Tracking",
            "Assignment Submission & Grading",
            "Announcements & Notification Service",
        ],
    },
    # ── Smart Parking & Vehicle Management ────────────────────────────────────
    "smart_parking": {
        "display_name": "Smart Parking & Vehicle Management",
        "keywords": [
            "parking", "parking spot", "parking slot", "parking lot", "vehicle", "driver",
            "attendant", "valet", "license plate", "occupancy", "tariff", "parking fee",
            "parking space", "check-in", "check-out", "gate control", "overstay", "slot availability",
        ],
        "checklist": [
            "Driver & Attendant Identity & Profile Management",
            "Real-Time Parking Spot Search & Availability Map",
            "Parking Slot Reservation & Booking Engine",
            "Digital Parking Fee Calculation & Payment Processing",
            "Vehicle Check-In, Check-Out & License Plate Verification",
            "Real-Time Lot Occupancy Monitoring & Sensor Tracking",
            "Automated Overstay Alerts & Parking Violation Management",
            "Admin Dashboard: Tariff, Zone & Revenue Analytics",
        ],
        "default_services": [
            "Identity & Access Service",
            "Parking Spot & Lot Service",
            "Reservation & Booking Service",
            "Fee & Payment Service",
            "Vehicle Check-In & Gate Service",
            "Occupancy & Sensor Service",
            "Notification & Alert Service",
            "Reporting & Analytics Service",
        ],
        "default_actors": [
            {"role": "Driver", "description": "Searches for available parking spots, reserves slots, and pays parking fees"},
            {"role": "Parking Attendant", "description": "Monitors parking lots, verifies vehicle check-in and check-out, and manages space allocations"},
            {"role": "System Administrator", "description": "Manages parking zones, pricing tariffs, user accounts, and system analytics"},
        ],
        "default_modules": [
            "Authentication & Access Control",
            "Parking Lot & Spot Management",
            "Slot Reservation & Booking",
            "Fee Calculation & Payment Processing",
            "Vehicle Check-In & Gate Control",
            "Real-Time Occupancy Tracking",
            "Tariff & Zone Configuration",
            "Admin Dashboard & Revenue Analytics",
        ],
    },
}


class CanonicalRequirement(BaseModel):
    """Immutable, standardized requirement entity with globally unique stable ID."""
    id: str = Field(..., description="Stable requirement ID (e.g. REQ-001)")
    title: str = Field(..., description="Short summary title")
    category: str = Field(default="Functional", description="Functional, Non-Functional, Security, Compliance")
    description: str = Field(..., description="Clear, testable requirement statement")
    priority: str = Field(default="HIGH", description="CRITICAL, HIGH, MEDIUM, LOW")
    acceptance_criteria: List[str] = Field(default_factory=list)
    domain_module: str = Field(default="", description="Mapped domain module or subsystem")


class DomainContext(BaseModel):
    """Immutable canonical requirement artifact locked in Phase 1 and enforced across all downstream agents."""
    domain_key: str = Field(..., description="Normalized key: library, ecommerce, healthcare, fintech, saas")
    domain_name: str = Field(..., description="Full descriptive domain title")
    system_name: str = Field(default="Enterprise System")
    system_type: str = Field(default="Software Application")
    system_goal: str = Field(default="")
    canonical_requirements: List[CanonicalRequirement] = Field(default_factory=list)
    functional_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    non_functional_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    actors: List[Dict[str, Any]] = Field(default_factory=list)
    modules: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    key_workflows: List[Dict[str, Any]] = Field(default_factory=list)
    domain_gap_analysis: Dict[str, Any] = Field(default_factory=dict)
    domain_checklist: List[str] = Field(default_factory=list)
    default_services: List[str] = Field(default_factory=list)
    is_locked: bool = True

    def get_req_ids(self) -> List[str]:
        return [r.id for r in self.canonical_requirements]

    @property
    def forbidden_keywords(self) -> List[str]:
        from app.sae.utils.domain_fence import get_forbidden_domain_concepts
        forbidden_map = get_forbidden_domain_concepts(self.domain_key)
        tokens = []
        for info in forbidden_map.values():
            tokens.extend(info.get("keywords", []))
        return list(dict.fromkeys(tokens))

    def get_requirements_summary(self) -> str:
        lines = []
        for r in self.canonical_requirements:
            lines.append(f"[{r.id}] ({r.category}/{r.priority}) {r.title}: {r.description}")
        return "\n".join(lines)

    def to_validated_artifact(self) -> Dict[str, Any]:
        """Produce the canonical, validated Requirement Analysis dictionary."""
        return {
            "system_name": self.system_name,
            "system_type": self.system_type,
            "domain": self.domain_name,
            "functional_requirements": self.functional_requirements,
            "non_functional_requirements": self.non_functional_requirements,
            "actors": self.actors,
            "modules": self.modules,
            "constraints": self.constraints,
            "assumptions": self.assumptions,
            "key_workflows": self.key_workflows,
            "domain_gap_analysis": self.domain_gap_analysis,
            "domain_checklist": self.domain_checklist,
        }


class DomainLockEngine:
    """Deterministic Domain Detection, Validation, and Canonical Requirement Locker."""

    @classmethod
    def detect_domain(cls, arsrs: Dict[str, Any], raw_prompt: str = "") -> str:
        """Deterministically determine domain key from ARSRS and user inputs without false archetype hijacking."""
        dom_ctx = arsrs.get("domain_context", {}) if isinstance(arsrs.get("domain_context"), dict) else {}
        industry = str(dom_ctx.get("industry", "")).lower()

        proj_prof = arsrs.get("project_profile", {}) if isinstance(arsrs.get("project_profile"), dict) else {}
        goal = str(proj_prof.get("goal", "")).lower()
        domain_prop = str(arsrs.get("domain") or proj_prof.get("domain") or "").lower()

        combined_text = f"{industry} {domain_prop} {goal} {raw_prompt}".lower()

        # Check explicit matching against known domain taxonomies
        scores: Dict[str, int] = {}
        for key, data in DOMAIN_TAXONOMY.items():
            score = 0
            for kw in data["keywords"]:
                pattern = rf"\b{re.escape(kw.lower())}(?:s|es)?\b"
                if re.search(pattern, combined_text):
                    score += 2 if (kw in industry or kw in goal or kw in domain_prop) else 1

            # Disambiguation filters to prevent false positives from generic words
            if key == "food_delivery" and score > 0:
                if not any(k in combined_text for k in ("restaurant", "menu", "dish", "cuisine", "food item", "kitchen")):
                    score = 0
            if key == "library" and score > 0:
                if not any(k in combined_text for k in ("library", "librarian", "isbn", "circulation", "borrow book", "patron")):
                    score = 0
            if key == "ecommerce" and score > 0:
                if not any(k in combined_text for k in ("cart", "checkout", "shopping cart", "online store", "ecommerce", "e-commerce", "retail store")):
                    score = 0
            if key == "healthcare" and score > 0:
                if not any(k in combined_text for k in ("ehr", "electronic health", "clinical notes", "hospital", "patient record", "icd-10", "medical prescription")):
                    score = 0
            if key == "appointment_scheduling" and score > 0:
                # Require explicit doctor/clinic context to prevent parking/meeting/ticket scheduling collision
                if not any(k in combined_text for k in ("doctor", "clinic", "patient", "consultation", "physician", "medical")):
                    score = 0
            if key == "inventory_management" and score > 0:
                if not any(k in combined_text for k in ("warehouse", "sku", "stock-in", "stock-out", "restocking", "inventory tracking")):
                    score = 0
            if key == "learning_management" and score > 0:
                if not any(k in combined_text for k in ("course", "syllabus", "assignment submission", "instructor", "enrollment", "lms")):
                    score = 0
            if key == "smart_parking" and score > 0:
                if not any(k in combined_text for k in ("parking", "park", "spot", "slot", "lot", "garage", "valet", "license plate", "vehicle")):
                    score = 0

            scores[key] = score

        if scores:
            best_domain = max(scores, key=scores.get)
            if scores[best_domain] >= 3:
                return best_domain

        # Generate a slugified domain key from user domain / industry
        raw_domain_source = domain_prop or industry or (proj_prof.get("name") if isinstance(proj_prof, dict) else "") or "custom_domain"
        clean_slug = re.sub(r"[^a-zA-Z0-9]+", "_", raw_domain_source).strip("_").lower()
        return clean_slug if len(clean_slug) >= 3 else "custom_domain"

    @classmethod
    def lock_domain_and_requirements(
        cls,
        arsrs: Dict[str, Any],
        raw_prompt: str = "",
    ) -> DomainContext:
        """Lock domain and build immutable canonical requirement set with complete field guarantees."""
        domain_key = cls.detect_domain(arsrs, raw_prompt)
        proj_prof = arsrs.get("project_profile", {}) if isinstance(arsrs.get("project_profile"), dict) else {}
        system_goal = proj_prof.get("goal") or arsrs.get("goal") or "Enterprise Production Architecture"
        system_type = proj_prof.get("system_type") or arsrs.get("system_type") or "Software Application"
        domain_str = proj_prof.get("domain") or arsrs.get("domain") or (dom_ctx := arsrs.get("domain_context", {})).get("industry") if isinstance(arsrs.get("domain_context"), dict) else ""
        if not domain_str:
            domain_str = system_type if system_type != "Software Application" else "Enterprise Application Domain"

        if domain_key in DOMAIN_TAXONOMY:
            taxonomy = DOMAIN_TAXONOMY[domain_key]
        else:
            # Dynamically derive checklist and defaults from input ARSRS requirements for custom domains
            raw_fr_list = arsrs.get("functional_requirements", [])
            dynamic_checklist: List[str] = []
            if isinstance(raw_fr_list, list):
                for fr in raw_fr_list:
                    if isinstance(fr, dict):
                        t = fr.get("title") or fr.get("description", "")
                        clean_t = str(t).split(".")[0].strip()
                        if clean_t and clean_t not in dynamic_checklist and len(clean_t) <= 60:
                            dynamic_checklist.append(clean_t)
            
            raw_mods = arsrs.get("modules", [])
            if isinstance(raw_mods, list):
                for m in raw_mods:
                    m_str = m if isinstance(m, str) else (m.get("name") if isinstance(m, dict) else "")
                    if m_str and m_str not in dynamic_checklist:
                        dynamic_checklist.append(m_str)

            if not dynamic_checklist:
                dynamic_checklist = ["Core Workflow Execution", "User Identity & Authentication", "Resource Management", "Audit Logging & Reporting"]

            taxonomy = {
                "display_name": domain_str,
                "keywords": [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", f"{domain_str} {system_type}")],
                "checklist": dynamic_checklist[:8],
                "default_services": [f"{re.sub(r'[^a-zA-Z0-9]+', '', item)}Service" for item in dynamic_checklist[:6]],
                "default_actors": [{"role": "User", "description": "Primary application user"}, {"role": "Administrator", "description": "System administrator"}],
                "default_modules": dynamic_checklist[:6],
            }

        # Derive system name dynamically from user input
        system_name = (
            arsrs.get("system_name")
            or proj_prof.get("name")
            or arsrs.get("title")
            or (proj_prof.get("goal", "").split(".")[0].strip() if proj_prof.get("goal") and len(proj_prof.get("goal", "")) < 80 else None)
        )
        if not system_name:
            if domain_str and "custom" not in domain_str.lower() and "enterprise" not in domain_str.lower():
                system_name = f"{domain_str.strip()} System"
            elif raw_prompt:
                first_line = raw_prompt.strip().split("\n")[0].split(".")[0].strip()
                system_name = first_line[:60] if len(first_line) > 3 else "Enterprise Architecture System"
            else:
                system_name = "Enterprise Architecture System"

        # ── 1. Extract Actors ─────────────────────────────────────────────────
        actors: List[Dict[str, Any]] = []
        raw_actors = arsrs.get("actors", [])
        if isinstance(raw_actors, list) and raw_actors:
            for a in raw_actors:
                if isinstance(a, dict):
                    role_name = a.get("title") or a.get("role") or a.get("name") or "User"
                    desc = a.get("description") or f"System actor: {role_name}"
                    actors.append({"role": role_name, "description": desc})
                elif isinstance(a, str) and a.strip():
                    actors.append({"role": a.strip(), "description": f"System actor: {a.strip()}"})

        # Fallback from business_context.stakeholders
        biz_ctx = arsrs.get("business_context", {}) if isinstance(arsrs.get("business_context"), dict) else {}
        if not actors and isinstance(biz_ctx.get("stakeholders"), list):
            for s in biz_ctx["stakeholders"]:
                if isinstance(s, str) and s.strip():
                    actors.append({"role": s.strip(), "description": f"Primary system stakeholder: {s.strip()}"})

        if not actors:
            actors = taxonomy.get("default_actors", [{"role": "User", "description": "Standard authorized user"}])

        # ── 2. Extract Modules ────────────────────────────────────────────────
        modules: List[str] = []
        raw_modules = arsrs.get("modules", [])
        if isinstance(raw_modules, list) and raw_modules:
            for m in raw_modules:
                if isinstance(m, str) and m.strip():
                    modules.append(m.strip())
                elif isinstance(m, dict) and m.get("name"):
                    modules.append(str(m["name"]).strip())

        if not modules:
            modules = taxonomy.get("default_modules", ["Core Application Module", "Authentication & Security Module"])

        # ── 3. Extract Constraints & Assumptions ──────────────────────────────
        constraints: List[str] = []
        if isinstance(arsrs.get("constraints"), list):
            for c in arsrs["constraints"]:
                if isinstance(c, dict):
                    constraints.append(c.get("description") or c.get("title") or str(c))
                elif isinstance(c, str) and c.strip():
                    constraints.append(c.strip())

        if isinstance(biz_ctx.get("constraints"), list):
            for c in biz_ctx["constraints"]:
                if isinstance(c, str) and c.strip():
                    constraints.append(c.strip())

        if not constraints:
            constraints = [
                "Must enforce relational ACID consistency for core transactions.",
                "Must expose OpenAPI 3.0 compliant RESTful endpoints.",
            ]

        assumptions: List[str] = []
        if isinstance(biz_ctx.get("assumptions"), list):
            for a in biz_ctx["assumptions"]:
                if isinstance(a, str) and a.strip():
                    assumptions.append(a.strip())

        if not assumptions:
            assumptions = [
                "Target peak workload: 500 concurrent active users with sub-250ms p95 latency.",
                "Standard containerized deployment on cloud Kubernetes infrastructure.",
            ]

        # ── 4. Extract Key Workflows ──────────────────────────────────────────
        key_workflows: List[Dict[str, Any]] = []
        raw_wf = arsrs.get("workflows", [])
        if isinstance(raw_wf, list) and raw_wf:
            for wf in raw_wf:
                if isinstance(wf, dict):
                    wname = wf.get("name") or wf.get("title") or "Core Workflow"
                    wsteps = wf.get("steps") if isinstance(wf.get("steps"), list) else ["Initiate Request", "Validate & Process", "Persist Result"]
                    key_workflows.append({"name": wname, "steps": wsteps, "actor": wf.get("actor", "User")})

        if not key_workflows:
            key_workflows = [
                {"name": "Core Transaction Workflow", "steps": ["Submit Request", "Authenticate & Authorize", "Process Domain Logic", "Commit to Database"]}
            ]

        # ── 5. Extract Functional & Non-Functional Requirements ───────────────
        canonical_reqs: List[CanonicalRequirement] = []
        func_reqs: List[Dict[str, Any]] = []
        nfr_reqs: List[Dict[str, Any]] = []

        fr_counter = 1
        nfr_counter = 1
        seen_descs: Set[str] = set()

        # Gather Explicit Functional Requirements from ARSRS
        raw_fr_list = arsrs.get("functional_requirements", [])
        if isinstance(raw_fr_list, list):
            for fr in raw_fr_list:
                if isinstance(fr, dict):
                    desc = str(fr.get("description") or fr.get("title") or "").strip()
                    if not desc or desc.lower() in seen_descs:
                        continue
                    seen_descs.add(desc.lower())
                    raw_id = str(fr.get("id", "")).strip()
                    req_id = raw_id if (raw_id.startswith("FR-") or raw_id.startswith("REQ-")) else f"FR-{fr_counter:03d}"
                    title = str(fr.get("title") or desc[:45]).strip()
                    pri = str(fr.get("priority", "HIGH")).upper()
                    
                    item = {
                        "id": req_id,
                        "title": title,
                        "description": desc,
                        "priority": pri,
                        "category": "Functional",
                    }
                    func_reqs.append(item)
                    canonical_reqs.append(
                        CanonicalRequirement(
                            id=req_id,
                            title=title,
                            category="Functional",
                            description=desc,
                            priority=pri,
                            acceptance_criteria=[f"Verified functional execution of {title}"],
                        )
                    )
                    fr_counter += 1

        # Fallback: Add Core Business Objectives from business_context as Functional Requirements
        if isinstance(biz_ctx.get("business_objectives"), list):
            for obj in biz_ctx["business_objectives"]:
                if isinstance(obj, str) and obj.strip() and obj.strip().lower() not in seen_descs:
                    desc = obj.strip()
                    seen_descs.add(desc.lower())
                    req_id = f"FR-{fr_counter:03d}"
                    title = "Core Domain Workflow Objective"
                    pri = "HIGH"
                    item = {
                        "id": req_id,
                        "title": title,
                        "description": desc,
                        "priority": pri,
                        "category": "Functional",
                    }
                    func_reqs.append(item)
                    canonical_reqs.append(
                        CanonicalRequirement(
                            id=req_id,
                            title=title,
                            category="Functional",
                            description=desc,
                            priority=pri,
                            acceptance_criteria=[f"Core workflow executed with 100% transaction consistency"],
                        )
                    )
                    fr_counter += 1

        # Fallback: Extract from parameters.functional_requirements
        if not func_reqs:
            param_fr = arsrs.get("parameters", {}).get("functional_requirements", {}).get("value", [])
            if isinstance(param_fr, list):
                for p in param_fr:
                    if isinstance(p, str) and p.strip() and len(p.strip()) > 3 and p.strip().lower() not in seen_descs:
                        desc = p.strip()
                        seen_descs.add(desc.lower())
                        req_id = f"FR-{fr_counter:03d}"
                        title = desc[:45]
                        item = {"id": req_id, "title": title, "description": desc, "priority": "HIGH", "category": "Functional"}
                        func_reqs.append(item)
                        canonical_reqs.append(CanonicalRequirement(id=req_id, title=title, category="Functional", description=desc, priority="HIGH", acceptance_criteria=[f"Execution of {title}"]))
                        fr_counter += 1

        # Fallback: Extract semantic functional requirements from raw prompt / goal if still empty
        if not func_reqs:
            ps_text = raw_prompt or arsrs.get("raw_input") or system_goal
            if ps_text:
                from app.ree.agents.text_normalizer import extract_semantic_functional_requirements
                fallback_frs = extract_semantic_functional_requirements(ps_text)
                for item_text in fallback_frs:
                    if item_text and item_text.lower() not in seen_descs:
                        seen_descs.add(item_text.lower())
                        req_id = f"FR-{fr_counter:03d}"
                        title = item_text.split(".")[0][:45]
                        item = {"id": req_id, "title": title, "description": item_text, "priority": "HIGH", "category": "Functional"}
                        func_reqs.append(item)
                        canonical_reqs.append(CanonicalRequirement(id=req_id, title=title, category="Functional", description=item_text, priority="HIGH", acceptance_criteria=[f"Verified functional capability of {title}"]))
                        fr_counter += 1

        # Gather Non-Functional Requirements from ARSRS
        raw_nfr_list = arsrs.get("non_functional_requirements", [])
        if isinstance(raw_nfr_list, list):
            for nfr in raw_nfr_list:
                if isinstance(nfr, dict):
                    desc = str(nfr.get("description") or nfr.get("title") or nfr.get("requirement") or "").strip()
                    if not desc or desc.lower() in seen_descs:
                        continue
                    seen_descs.add(desc.lower())
                    raw_id = str(nfr.get("id", "")).strip()
                    req_id = raw_id if (raw_id.startswith("NFR-") or raw_id.startswith("REQ-")) else f"NFR-{nfr_counter:03d}"
                    title = str(nfr.get("title") or desc[:45]).strip()
                    cat = "Performance" if any(k in desc.lower() for k in ["latency", "response time", "throughput", "scale"]) else ("Security" if "encrypt" in desc.lower() or "auth" in desc.lower() else "Non-Functional")
                    pri = str(nfr.get("priority", "HIGH")).upper()

                    item = {
                        "id": req_id,
                        "title": title,
                        "category": cat,
                        "requirement": desc,
                        "description": desc,
                        "priority": pri,
                    }
                    nfr_reqs.append(item)
                    canonical_reqs.append(
                        CanonicalRequirement(
                            id=req_id,
                            title=title,
                            category="Non-Functional",
                            description=desc,
                            priority=pri,
                            acceptance_criteria=[f"System satisfies {cat} standard: {desc[:60]}"],
                        )
                    )
                    nfr_counter += 1

        # Guarantee minimum standard NFRs if empty
        if not nfr_reqs:
            default_nfr = {
                "id": f"NFR-{nfr_counter:03d}",
                "title": "Sub-250ms API Latency SLA",
                "category": "Performance",
                "requirement": "p95 API response time shall remain under 250ms under concurrent peak load.",
                "description": "p95 API response time shall remain under 250ms under concurrent peak load.",
                "priority": "HIGH",
            }
            nfr_reqs.append(default_nfr)
            canonical_reqs.append(
                CanonicalRequirement(
                    id=default_nfr["id"],
                    title=default_nfr["title"],
                    category="Non-Functional",
                    description=default_nfr["description"],
                    priority="HIGH",
                    acceptance_criteria=["p95 < 250ms under peak load"],
                )
            )
            nfr_counter += 1

        # ── 6. Deterministic Domain Gap Analysis (Without Hallucination) ──────
        # Cross-checks domain checklist against actual requirements.
        # Present features are marked PRESENT; unstated features remain properly classified as
        # ABSENT_POTENTIAL_GAP with RECOMMENDED or FUTURE_RELEASE status (NEVER hallucinated as required).
        checklist = taxonomy.get("checklist", [])
        all_req_text = " ".join([r.description.lower() for r in canonical_reqs] + [m.lower() for m in modules])
        checklist_status = []

        for item in checklist:
            item_words = [w.lower() for w in re.split(r"[&\s/,]+", item) if len(w) > 3 and w.lower() not in ("user", "data", "with", "system", "management")]
            matched_req = None
            for r in canonical_reqs:
                if any(w in r.description.lower() or w in r.title.lower() for w in item_words):
                    matched_req = r.id
                    break

            if matched_req:
                checklist_status.append({
                    "feature": item,
                    "status": "PRESENT",
                    "requirement_ref": matched_req,
                    "classification": "REQUIRED",
                })
            else:
                checklist_status.append({
                    "feature": item,
                    "status": "ABSENT_POTENTIAL_GAP",
                    "classification": "RECOMMENDED_FUTURE_PHASE",
                    "recommendation": f"Consider implementing {item} in subsequent iteration if required by business growth.",
                })

        domain_gap_analysis = {
            "domain_evaluated": taxonomy["display_name"],
            "checklist_items_total": len(checklist),
            "checklist_status": checklist_status,
        }

        dom_concepts = taxonomy.get("keywords", [])[:6]

        return DomainContext(
            domain_key=domain_key,
            domain_name=taxonomy["display_name"],
            system_name=system_name,
            system_type=system_type,
            system_goal=system_goal,
            canonical_requirements=canonical_reqs,
            functional_requirements=func_reqs,
            non_functional_requirements=nfr_reqs,
            actors=actors,
            modules=modules,
            constraints=constraints,
            assumptions=assumptions,
            key_workflows=key_workflows,
            domain_gap_analysis=domain_gap_analysis,
            domain_checklist=checklist,
            default_services=taxonomy.get("default_services", []),
            is_locked=True,
        )

    @classmethod
    def validate_requirement_quality(cls, domain_ctx: DomainContext) -> Dict[str, Any]:
        """Validate requirement completeness score and health status."""
        func_count = len(domain_ctx.functional_requirements)
        nfr_count = len(domain_ctx.non_functional_requirements)
        actors_count = len(domain_ctx.actors)
        modules_count = len(domain_ctx.modules)
        total_reqs = func_count + nfr_count

        checklist = domain_ctx.domain_checklist
        present_count = sum(1 for item in domain_ctx.domain_gap_analysis.get("checklist_status", []) if item.get("status") == "PRESENT")
        coverage_ratio = round(present_count / max(len(checklist), 1), 2)

        is_healthy = (
            func_count >= 1
            and nfr_count >= 1
            and actors_count >= 1
            and modules_count >= 1
            and bool(domain_ctx.system_name)
            and bool(domain_ctx.domain_name)
        )

        quality_score = 1.0 if is_healthy else round(
            (0.30 * min(1.0, func_count / 2.0))
            + (0.25 * min(1.0, nfr_count / 2.0))
            + (0.25 * min(1.0, actors_count / 1.0))
            + (0.20 * min(1.0, modules_count / 2.0)),
            2
        )

        return {
            "is_healthy": is_healthy,
            "quality_score": quality_score,
            "total_requirements": total_reqs,
            "functional_count": func_count,
            "non_functional_count": nfr_count,
            "actors_count": actors_count,
            "modules_count": modules_count,
            "domain_checklist_coverage": coverage_ratio,
            "domain_locked": domain_ctx.domain_name,
        }

    # Alias for convenience
    lock_domain = lock_domain_and_requirements



def validate_requirement_contract(
    req_analysis: Dict[str, Any],
    domain_ctx: DomainContext,
) -> Tuple[bool, float, List[str]]:
    """Strict Pipeline Contract Validator for Requirement Analysis Artifact."""
    violations: List[str] = []

    if not isinstance(req_analysis, dict) or not req_analysis:
        return False, 0.0, ["Requirement Analysis artifact is empty or null"]

    system_name = req_analysis.get("system_name")
    if not system_name or not str(system_name).strip():
        violations.append("Contract Violation: 'system_name' is missing or empty")

    domain = req_analysis.get("domain")
    if not domain or not str(domain).strip():
        violations.append("Contract Violation: 'domain' is missing or empty")

    func_reqs = req_analysis.get("functional_requirements", [])
    if not isinstance(func_reqs, list) or len(func_reqs) == 0:
        violations.append("Contract Violation: 'functional_requirements' is empty")

    nfr_reqs = req_analysis.get("non_functional_requirements", [])
    if not isinstance(nfr_reqs, list) or len(nfr_reqs) == 0:
        violations.append("Contract Violation: 'non_functional_requirements' is empty")

    actors = req_analysis.get("actors", [])
    if not isinstance(actors, list) or len(actors) == 0:
        violations.append("Contract Violation: 'actors' is empty")

    modules = req_analysis.get("modules", [])
    if not isinstance(modules, list) or len(modules) == 0:
        violations.append("Contract Violation: 'modules' is empty")

    # Check that requirement IDs are non-empty strings
    for idx, fr in enumerate(func_reqs):
        if not isinstance(fr, dict) or not fr.get("id"):
            violations.append(f"Contract Violation: functional_requirements[{idx}] missing valid 'id'")

    is_valid = len(violations) == 0
    score = 1.0 if is_valid else round(max(0.0, 1.0 - len(violations) * 0.20), 2)
    return is_valid, score, violations
