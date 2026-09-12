"""
AI Governance Crisis Simulator — Data Consistency & Validation Checker

Validates:
- 15 Fictional Countries: unique IDs, unique names, schema compliance, valid relational references.
- 3 Crisis Scenarios: unique IDs, schema compliance, affected/origin country references, timeline structure.
- 6 Governance Documents: frontmatter metadata, substantive markdown sections.
- Referential integrity: cross-links between countries, scenarios, and governance docs.
"""
import sys
from pathlib import Path
from typing import List, Set

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.data_loader import DataLoader, DEFAULT_DATA_DIR
from app.schemas.data_models import CountryData, ScenarioData, GovernanceDocument


def validate_all_data(data_dir: Path = DEFAULT_DATA_DIR) -> bool:
    """
    Executes full data layer validation.
    Returns True if all validation checks pass, False otherwise.
    """
    errors: List[str] = []
    loader = DataLoader(data_dir)

    # ── 1. Validate Countries ─────────────────────────────────────────────────
    countries: List[CountryData] = []
    country_ids: Set[str] = set()
    country_names: Set[str] = set()

    try:
        raw_countries = loader.load_all_countries()
        for c in raw_countries:
            # Check duplicate ID
            if c.id in country_ids:
                errors.append(f"Duplicate country ID: {c.id}")
            country_ids.add(c.id)

            # Check duplicate Name
            if c.name in country_names:
                errors.append(f"Duplicate country name: {c.name}")
            country_names.add(c.name)

            # Check capacity ranges
            for field in [
                "economic_strength",
                "technology_capacity",
                "ai_capability",
                "military_capacity",
                "political_stability",
                "governance_capacity",
            ]:
                val = getattr(c, field)
                if not (0 <= val <= 100):
                    errors.append(f"Country {c.id} {field} out of range [0, 100]: {val}")

            if not (0.0 <= c.diplomatic_influence <= 1.0):
                errors.append(f"Country {c.id} diplomatic_influence out of range [0.0, 1.0]: {c.diplomatic_influence}")

            countries.append(c)

    except Exception as exc:
        errors.append(f"Failed to load countries: {exc}")

    country_valid_count = len(countries)

    # ── 2. Validate Country Referential Integrity ─────────────────────────────
    ref_integrity_valid = True
    for c in countries:
        # Check allies reference valid countries
        for ally in c.allies:
            if ally not in country_ids:
                errors.append(f"Country {c.id} references non-existent ally: {ally}")
                ref_integrity_valid = False
            if ally == c.id:
                errors.append(f"Country {c.id} lists itself as ally")
                ref_integrity_valid = False

        # Check rivals reference valid countries
        for rival in c.rivals:
            if rival not in country_ids:
                errors.append(f"Country {c.id} references non-existent rival: {rival}")
                ref_integrity_valid = False
            if rival == c.id:
                errors.append(f"Country {c.id} lists itself as rival")
                ref_integrity_valid = False

        # Check initial_relationships reference valid countries
        for target_id, score in c.initial_relationships.items():
            if target_id not in country_ids:
                errors.append(f"Country {c.id} has relationship score with unknown country: {target_id}")
                ref_integrity_valid = False
            if target_id == c.id:
                errors.append(f"Country {c.id} defines relationship with itself")
                ref_integrity_valid = False
            if not (-100 <= score <= 100):
                errors.append(f"Country {c.id} relationship score with {target_id} out of bounds: {score}")
                ref_integrity_valid = False

    # ── 3. Validate Governance Documents ──────────────────────────────────────
    gov_docs: List[GovernanceDocument] = []
    gov_doc_ids: Set[str] = set()

    try:
        raw_docs = loader.load_governance_documents()
        for doc in raw_docs:
            did = doc.metadata.doc_id
            if did in gov_doc_ids:
                errors.append(f"Duplicate governance doc_id: {did}")
            gov_doc_ids.add(did)

            if not doc.content.strip():
                errors.append(f"Governance document {did} has empty content")
            if not doc.sections:
                errors.append(f"Governance document {did} has no parsed sections")

            gov_docs.append(doc)
    except Exception as exc:
        errors.append(f"Failed to load governance documents: {exc}")

    gov_valid_count = len(gov_docs)

    # ── 4. Validate Scenarios ─────────────────────────────────────────────────
    scenarios: List[ScenarioData] = []
    scenario_ids: Set[str] = set()

    try:
        raw_scenarios = loader.load_all_scenarios()
        for s in raw_scenarios:
            if s.id in scenario_ids:
                errors.append(f"Duplicate scenario ID: {s.id}")
            scenario_ids.add(s.id)

            # Check origin country exists
            if s.origin_country not in country_ids:
                errors.append(f"Scenario {s.id} origin_country '{s.origin_country}' does not exist in countries")
                ref_integrity_valid = False

            # Check affected countries exist
            for ac in s.affected_countries:
                if ac not in country_ids:
                    errors.append(f"Scenario {s.id} affected_country '{ac}' does not exist in countries")
                    ref_integrity_valid = False

            # Check information delay keys exist in affected countries
            for id_country in s.information_delay.keys():
                if id_country not in country_ids:
                    errors.append(f"Scenario {s.id} information_delay country '{id_country}' unknown")
                    ref_integrity_valid = False

            # Check governance docs referenced exist
            for gdoc in s.governance_docs_relevant:
                if gdoc not in gov_doc_ids:
                    errors.append(f"Scenario {s.id} references unknown governance doc: '{gdoc}'")
                    ref_integrity_valid = False

            # Check timeline is ordered by time_offset
            offsets = [t.time_offset for t in s.timeline]
            if offsets != sorted(offsets):
                errors.append(f"Scenario {s.id} timeline is not sequentially ordered by time_offset")

            scenarios.append(s)
    except Exception as exc:
        errors.append(f"Failed to load scenarios: {exc}")

    scenario_valid_count = len(scenarios)

    # ── Summary Output ────────────────────────────────────────────────────────
    schema_status = "VALID" if not errors else "INVALID"
    ref_status = "VALID" if ref_integrity_valid else "INVALID"

    print("\nAI Governance Crisis Simulator — Data Validation\n")
    print(f"Countries:     {country_valid_count}/15 valid")
    print(f"Scenarios:      {scenario_valid_count}/3 valid")
    print(f"Governance:     {gov_valid_count}/6 valid")
    print(f"References:     {ref_status}")
    print(f"Schema:         {schema_status}")

    if errors:
        print("\nValidation Errors Encountered:")
        for err in errors:
            print(f"  ❌ {err}")
        print("\nDATA VALIDATION FAILED\n")
        return False
    else:
        print("\nDATA VALIDATION PASSED\n")
        return True


if __name__ == "__main__":
    success = validate_all_data()
    sys.exit(0 if success else 1)
