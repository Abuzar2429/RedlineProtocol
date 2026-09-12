"""
Tests for Phase 2 Data Layer:
- Country data loading, uniqueness, schemas, relational integrity, value ranges
- Scenario data loading, uniqueness, schemas, affected countries, actions, timeline
- Governance document loading, frontmatter metadata, sections, markdown parsing
- DataLoader service operations and failure handling
- Minimal read-only API endpoints: /api/countries, /api/scenarios
"""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.data_loader import (
    DataLoader,
    load_all_countries,
    load_country,
    load_all_scenarios,
    load_scenario,
    load_governance_documents,
    load_governance_document,
)
from app.schemas.data_models import CountryData, ScenarioData, GovernanceDocument


# ── Country Tests ─────────────────────────────────────────────────────────────

def test_load_all_countries_count():
    countries = load_all_countries()
    assert len(countries) == 15, f"Expected exactly 15 countries, got {len(countries)}"


def test_country_ids_unique():
    countries = load_all_countries()
    ids = [c.id for c in countries]
    assert len(ids) == len(set(ids)), f"Duplicate country IDs found: {ids}"


def test_country_names_unique():
    countries = load_all_countries()
    names = [c.name for c in countries]
    assert len(names) == len(set(names)), f"Duplicate country names found: {names}"


def test_country_value_ranges():
    countries = load_all_countries()
    for c in countries:
        assert 0 <= c.economic_strength <= 100
        assert 0 <= c.technology_capacity <= 100
        assert 0 <= c.ai_capability <= 100
        assert 0 <= c.military_capacity <= 100
        assert 0 <= c.political_stability <= 100
        assert 0 <= c.governance_capacity <= 100
        assert 0.0 <= c.diplomatic_influence <= 1.0
        assert c.risk_tolerance in ["low", "medium", "high"]
        assert c.transparency in ["low", "medium", "high"]
        assert c.coordination_willingness in ["low", "medium", "high"]
        assert c.decision_speed in ["slow", "medium", "fast"]
        assert c.ai_capability_level in ["low", "medium", "high"]


def test_country_relational_integrity():
    countries = load_all_countries()
    valid_ids = {c.id for c in countries}

    for c in countries:
        # Allies validation
        for ally in c.allies:
            assert ally in valid_ids, f"Country {c.id} ally '{ally}' does not exist"
            assert ally != c.id, f"Country {c.id} lists itself as ally"

        # Rivals validation
        for rival in c.rivals:
            assert rival in valid_ids, f"Country {c.id} rival '{rival}' does not exist"
            assert rival != c.id, f"Country {c.id} lists itself as rival"

        # Relationships validation
        for target_id, score in c.initial_relationships.items():
            assert target_id in valid_ids, f"Country {c.id} relationship target '{target_id}' does not exist"
            assert target_id != c.id, f"Country {c.id} defines relationship with itself"
            assert -100 <= score <= 100, f"Relationship score for {c.id}->{target_id} out of bounds: {score}"


def test_country_strategic_priorities_present():
    countries = load_all_countries()
    for c in countries:
        assert len(c.strategic_priorities) >= 3, f"Country {c.id} has insufficient strategic priorities"
        assert len(c.ai_policy_position) > 20, f"Country {c.id} policy position narrative too short"


# ── Scenario Tests ────────────────────────────────────────────────────────────

def test_load_all_scenarios_count():
    scenarios = load_all_scenarios()
    assert len(scenarios) == 3, f"Expected exactly 3 scenarios, got {len(scenarios)}"


def test_scenario_ids_unique():
    scenarios = load_all_scenarios()
    ids = [s.id for s in scenarios]
    assert len(ids) == len(set(ids)), f"Duplicate scenario IDs found: {ids}"


def test_scenario_country_references():
    scenarios = load_all_scenarios()
    countries = load_all_countries()
    valid_country_ids = {c.id for c in countries}

    for s in scenarios:
        assert s.origin_country in valid_country_ids, f"Origin country {s.origin_country} in {s.id} not found"
        for ac in s.affected_countries:
            assert ac in valid_country_ids, f"Affected country {ac} in {s.id} not found"
        for id_country in s.information_delay.keys():
            assert id_country in valid_country_ids, f"Information delay country {id_country} in {s.id} not found"


def test_scenario_timeline_order():
    scenarios = load_all_scenarios()
    for s in scenarios:
        offsets = [t.time_offset for t in s.timeline]
        assert offsets == sorted(offsets), f"Timeline in {s.id} not sorted chronologically"
        assert len(s.timeline) >= 5, f"Timeline in {s.id} too short"


def test_scenario_available_actions():
    scenarios = load_all_scenarios()
    for s in scenarios:
        assert len(s.available_actions) >= 4, f"Scenario {s.id} has too few available actions"
        action_ids = [a.id for a in s.available_actions]
        assert len(action_ids) == len(set(action_ids)), f"Duplicate action IDs in {s.id}"


# ── Governance Document Tests ─────────────────────────────────────────────────

def test_load_governance_documents_count():
    docs = load_governance_documents()
    assert len(docs) == 6, f"Expected exactly 6 governance documents, got {len(docs)}"


def test_governance_doc_ids_unique():
    docs = load_governance_documents()
    ids = [d.metadata.doc_id for d in docs]
    assert len(ids) == len(set(ids)), f"Duplicate governance doc_ids found: {ids}"


def test_governance_doc_structure():
    docs = load_governance_documents()
    for doc in docs:
        assert doc.metadata.title, "Document missing title"
        assert doc.metadata.category in [
            "principles",
            "response",
            "cooperation",
            "data_sharing",
            "emergency",
            "liability",
        ]
        assert len(doc.content) > 200, f"Document {doc.metadata.doc_id} content too brief"
        assert len(doc.sections) >= 3, f"Document {doc.metadata.doc_id} has too few parsed sections"


def test_scenario_governance_references_exist():
    scenarios = load_all_scenarios()
    docs = load_governance_documents()
    valid_doc_ids = {d.metadata.doc_id for d in docs}

    for s in scenarios:
        for ref_doc in s.governance_docs_relevant:
            assert ref_doc in valid_doc_ids, f"Scenario {s.id} references non-existent doc '{ref_doc}'"


# ── Loader Specific Operations & Failure Tests ────────────────────────────────

def test_load_country_by_id():
    c = load_country("country_01")
    assert isinstance(c, CountryData)
    assert c.id == "country_01"
    assert "Alerion" in c.name


def test_load_country_unknown_raises_key_error():
    with pytest.raises(KeyError):
        load_country("country_999")


def test_load_scenario_by_id():
    s = load_scenario("scenario_01")
    assert isinstance(s, ScenarioData)
    assert s.id == "scenario_01"

    # Also test by crisis alias
    s2 = load_scenario("crisis_001")
    assert s2.id == "scenario_01"


def test_load_scenario_unknown_raises_key_error():
    with pytest.raises(KeyError):
        load_scenario("nonexistent_scenario")


def test_load_governance_doc_by_id():
    doc = load_governance_document("ai_principles")
    assert isinstance(doc, GovernanceDocument)
    assert doc.metadata.doc_id == "ai_principles"


def test_load_governance_doc_unknown_raises_key_error():
    with pytest.raises(KeyError):
        load_governance_document("unknown_doctrine")


# ── API Endpoint Tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_list_countries():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/countries")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 15
    assert data[0]["id"] == "country_01"


@pytest.mark.asyncio
async def test_api_get_country_valid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/countries/country_01")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "country_01"
    assert data["name"] == "Federal Republic of Alerion"


@pytest.mark.asyncio
async def test_api_get_country_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/countries/nonexistent_xyz")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_list_scenarios():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3


@pytest.mark.asyncio
async def test_api_get_scenario_valid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/scenarios/scenario_01")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "scenario_01"
    assert "Infrastructure" in data["title"]


@pytest.mark.asyncio
async def test_api_get_scenario_by_alias():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/scenarios/crisis_001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "scenario_01"


@pytest.mark.asyncio
async def test_api_get_scenario_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/scenarios/crisis_999")
    assert response.status_code == 404
