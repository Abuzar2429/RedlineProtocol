"""
Tests for Phase 5 — International Coordinator Agent.
Verifies:
1. Coordinator construction and configuration
2. Context builder and information containment boundaries (no private reasoning leaks)
3. Structured proposal schema, business validation, and non-self-approval rule
4. Mock LLM provider integration
5. Deterministic fallback generation and reproducibility
6. Simulation engine integration on COORDINATION_REQUEST
7. Multi-round coordination support
8. REST API endpoints (/coordinate, /proposals)
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.coordinator_context_builder import CoordinatorContextBuilder
from app.agents.coordinator_models import (
    CoordinatorContext,
    CoordinatorProposal,
    PredictedVotes,
)
from app.agents.coordinator_prompt import (
    COORDINATOR_PROMPT_VERSION,
    build_coordinator_system_prompt,
    build_coordinator_user_prompt,
)
from app.agents.coordinator_service import CoordinatorService
from app.llm.mock_provider import MockLLMProvider
from app.main import app
from app.schemas.simulation_models import (
    CrisisOperationalState,
    CountrySimulationState,
    DecisionRecord,
    SimulationEvent,
    SimulationState,
)
from app.services.data_loader import default_data_loader
from app.services.simulation.engine import SimulationEngine
from app.services.simulation.repository import default_simulation_repository


# ── Helper Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def sample_simulation_state() -> SimulationState:
    """Creates a controlled SimulationState with aware countries and decisions."""
    return SimulationState(
        simulation_id="sim_test_coord_123",
        scenario_id="scenario_01",
        mode="coordinated",
        status="RUNNING",
        current_tick=15,
        current_time="T+15",
        crisis_state=CrisisOperationalState(
            scenario_id="scenario_01",
            phase="INVESTIGATION",
            severity="high",
            severity_score=0.8,
            current_risk=70.0,
            origin_country="country_01",
            affected_countries=["country_01", "country_02", "country_03", "country_04"],
            title="The Autonomous Defection Crisis",
            summary="Frontier autonomous military model showing uncontrolled exfiltration.",
        ),
        countries={
            "country_01": CountrySimulationState(
                country_id="country_01", name="Country One", status="Coordinating", information_completeness=0.8
            ),
            "country_02": CountrySimulationState(
                country_id="country_02", name="Country Two", status="Coordinating", information_completeness=0.9
            ),
            "country_03": CountrySimulationState(
                country_id="country_03", name="Country Three", status="Investigating", information_completeness=0.5
            ),
            "country_04": CountrySimulationState(
                country_id="country_04", name="Country Four", status="Unaware", information_completeness=0.0
            ),
        },
        decisions=[
            DecisionRecord(
                decision_id="dec_01",
                simulation_id="sim_test_coord_123",
                country_id="country_01",
                tick=10,
                action_id="share_telemetry_multilateral",
                label="Share Telemetry Multilaterally",
                reasoning="TOP SECRET NATIONAL REASONING: Must protect sovereign intelligence apparatus.",
                risks_noted="Risk of accidental capability leak; proprietary exposure",
                willingness_to_coordinate=0.85,
            ),
            DecisionRecord(
                decision_id="dec_02",
                simulation_id="sim_test_coord_123",
                country_id="country_02",
                tick=12,
                action_id="share_telemetry_multilateral",
                label="Share Telemetry Multilaterally",
                reasoning="CLASSIFIED CABINET DECREE: Rival state might weaponize information.",
                risks_noted="Escalation risk if rival bloc withholds data",
                willingness_to_coordinate=0.75,
            ),
            DecisionRecord(
                decision_id="dec_03",
                simulation_id="sim_test_coord_123",
                country_id="country_03",
                tick=14,
                action_id="investigate_internally",
                label="Investigate Internally",
                reasoning="INTERNAL MEMO: Do not trust international inspectors.",
                risks_noted="Delayed containment; unilateral vulnerability",
                willingness_to_coordinate=0.30,
            ),
        ],
        event_history=[
            SimulationEvent(
                event_id="ev_00",
                tick=0,
                event_type="CRISIS_TRIGGERED",
                description="Uncontrolled exfiltration flagged by frontier lab.",
                payload={"title": "Model Defection Detected"},
            ),
            SimulationEvent(
                event_id="ev_10",
                tick=10,
                event_type="TIMELINE_EVENT",
                description="Cross-border weight anomalies identified.",
                payload={"title": "Telemetry Anomaly Confirmed"},
            ),
            SimulationEvent(
                event_id="ev_future_99",
                tick=99,
                event_type="TIMELINE_EVENT",
                description="Future secret event that must NEVER leak.",
                payload={"title": "SECRET FUTURE WAR EVENT"},
            ),
        ],
    )


# ── 1. Construction & Prompt Tests ───────────────────────────────────────────

def test_coordinator_agent_initialization():
    provider = MockLLMProvider()
    agent = CoordinatorAgent(provider=provider, temperature=0.3)

    assert agent.temperature == 0.3
    assert agent.provider == provider
    assert "International Coordinator" in agent.system_prompt
    assert "UNTRUSTED DATA" in agent.system_prompt
    assert "PROPOSAL" in agent.system_prompt


def test_coordinator_prompt_generation(sample_simulation_state):
    context = CoordinatorContextBuilder.build_context(sample_simulation_state)
    prompt = build_coordinator_user_prompt(context)

    assert "The Autonomous Defection Crisis" in prompt
    assert "Virtual Clock: T+15" in prompt
    assert "Deterministic Position Aggregation" in prompt
    assert "country_01" in prompt
    assert "share_telemetry_multilateral" in prompt


# ── 2. Information Boundary Tests ────────────────────────────────────────────

def test_information_boundary_no_private_reasoning_leak(sample_simulation_state):
    """
    CRITICAL: Validates that country internal classified reasoning
    is never leaked to the Coordinator Agent or prompt.
    """
    context = CoordinatorContextBuilder.build_context(sample_simulation_state)
    user_prompt = build_coordinator_user_prompt(context)

    # Verify context position summaries omit private reasoning
    for pos in context.participating_countries:
        assert not hasattr(pos, "reasoning")
        assert not hasattr(pos, "justification")

    # Verify string search in full prompt does NOT contain private strings
    assert "TOP SECRET NATIONAL REASONING" not in user_prompt
    assert "CLASSIFIED CABINET DECREE" not in user_prompt
    assert "INTERNAL MEMO" not in user_prompt


def test_information_boundary_no_future_event_leak(sample_simulation_state):
    """
    CRITICAL: Validates that future events (tick > current_tick) are strictly omitted.
    """
    context = CoordinatorContextBuilder.build_context(sample_simulation_state)
    user_prompt = build_coordinator_user_prompt(context)

    assert "SECRET FUTURE WAR EVENT" not in user_prompt
    for ev_str in context.public_event_history:
        assert "SECRET FUTURE WAR EVENT" not in ev_str
        assert "T+99" not in ev_str


# ── 3. Structured Output & Validation Tests ──────────────────────────────────

def test_coordinator_proposal_valid():
    proposal = CoordinatorProposal(
        proposal_id="prop_001_sim123_t15",
        simulation_id="sim_123",
        event_id="ev_coord_01",
        tick=15,
        round=1,
        title="Joint Containment Framework",
        summary="Multilateral agreement on rapid telemetry sharing.",
        items=[
            "Establish bilateral telemetry exchange.",
            "Authorize joint technical review.",
        ],
        rationale="Balances immediate containment against national autonomy.",
        predicted_votes=PredictedVotes(
            approve=["country_01", "country_02"],
            oppose=["country_03"],
            abstain=["country_04"],
        ),
        unresolved_issues=["Confidentiality of proprietary weights"],
        supporting_countries=["country_01", "country_02"],
        opposing_countries=["country_03"],
        confidence=0.85,
        source="llm_coordinator",
        status="PROPOSED",
    )

    assert proposal.proposal_id == "prop_001_sim123_t15"
    assert proposal.confidence == 0.85
    assert len(proposal.items) == 2
    assert proposal.status == "PROPOSED"


def test_coordinator_cannot_self_approve():
    """
    Strict business rule: Coordinator cannot mark proposal as APPROVED or PASSED.
    """
    with pytest.raises(ValueError, match="Coordinator cannot self-approve"):
        CoordinatorProposal(
            proposal_id="prop_001_illegal",
            simulation_id="sim_123",
            tick=15,
            title="Illegal Auto Approval",
            summary="This should fail validation",
            items=["Item 1"],
            rationale="Rationale",
            status="APPROVED",  # Prohibited
        )


def test_coordinator_confidence_bounds():
    with pytest.raises(ValueError):
        CoordinatorProposal(
            proposal_id="prop_001_bad_conf",
            simulation_id="sim_123",
            tick=15,
            title="Bad Confidence",
            summary="Summary",
            items=["Item 1"],
            rationale="Rationale",
            confidence=1.5,  # Must be <= 1.0
        )


# ── 4. Mock LLM Provider & Proposal Generation ───────────────────────────────

@pytest.mark.asyncio
async def test_coordinator_mock_provider_generation(sample_simulation_state):
    provider = MockLLMProvider()
    agent = CoordinatorAgent(provider=provider)

    proposal = await agent.propose(
        state=sample_simulation_state,
        current_event=None,
        round_index=1,
    )

    assert isinstance(proposal, CoordinatorProposal)
    assert proposal.source == "llm_coordinator"
    assert proposal.round == 1
    assert proposal.status == "PROPOSED"
    assert len(proposal.items) >= 2
    assert len(proposal.predicted_votes.approve) > 0
    # Referenced countries must be in sample_simulation_state
    for c in proposal.predicted_votes.approve:
        assert c in sample_simulation_state.countries


# ── 5. Deterministic Fallback & Reproducibility Tests ─────────────────────────

@pytest.mark.asyncio
async def test_coordinator_fallback_on_provider_error(sample_simulation_state):
    """
    When LLM raises an error, Coordinator must cleanly fall back to deterministic synthesis.
    """
    failing_provider = MockLLMProvider(simulate_error=True)
    agent = CoordinatorAgent(provider=failing_provider)

    proposal = await agent.propose(
        state=sample_simulation_state,
        current_event=None,
        round_index=1,
    )

    assert proposal is not None
    assert proposal.source == "deterministic_fallback"
    assert proposal.status == "PROPOSED"
    assert "country_01" in proposal.supporting_countries
    assert "country_03" in proposal.opposing_countries
    assert len(proposal.unresolved_issues) > 0


@pytest.mark.asyncio
async def test_coordinator_fallback_on_timeout(sample_simulation_state):
    timeout_provider = MockLLMProvider(simulate_timeout=True)
    agent = CoordinatorAgent(provider=timeout_provider)

    proposal = await agent.propose(
        state=sample_simulation_state,
        current_event=None,
        round_index=1,
    )

    assert proposal.source == "deterministic_fallback"
    assert proposal.status == "PROPOSED"


@pytest.mark.asyncio
async def test_coordinator_fallback_reproducibility(sample_simulation_state):
    """
    Determinism test: calling fallback twice with identical input state
    must generate an IDENTICAL proposal.
    """
    failing_provider = MockLLMProvider(simulate_error=True)
    agent = CoordinatorAgent(provider=failing_provider)

    prop1 = await agent.propose(sample_simulation_state, round_index=1)
    prop2 = await agent.propose(sample_simulation_state, round_index=1)

    assert prop1.proposal_id == prop2.proposal_id
    assert prop1.title == prop2.title
    assert prop1.items == prop2.items
    assert prop1.predicted_votes.approve == prop2.predicted_votes.approve
    assert prop1.predicted_votes.oppose == prop2.predicted_votes.oppose
    assert prop1.confidence == prop2.confidence


# ── 6. Simulation Engine Integration Tests ────────────────────────────────────

def test_engine_handles_coordination_request():
    """
    Verifies that COORDINATION_REQUEST event invokes the Coordinator,
    stores the proposal in state.proposals, and does NOT auto-approve it.
    """
    scenario = default_data_loader.load_scenario("scenario_01")
    countries = default_data_loader.load_all_countries()

    engine = SimulationEngine(
        scenario=scenario,
        countries=countries,
        mode="coordinated",
    )

    # Dispatch synthetic decisions for 3 countries to populate positions
    engine.state.current_tick = 14
    engine.state.countries["country_01"].status = "Coordinating"
    engine.state.countries["country_02"].status = "Coordinating"
    engine.state.decisions.append(
        DecisionRecord(
            decision_id="dec_01",
            simulation_id=engine.simulation_id,
            country_id="country_01",
            tick=10,
            action_id="share_telemetry_multilateral",
            label="Share Telemetry",
            reasoning="Critical national security interest to share telemetry and stop cross-border breach.",
            willingness_to_coordinate=0.9,
        )
    )

    # Fire a COORDINATION_REQUEST event
    coord_event = SimulationEvent(
        event_id="ev_coord_test",
        tick=14,
        event_type="COORDINATION_REQUEST",
        description="Emergency multilateral consultation convened.",
        payload={"title": "Emergency AI Safety Summit"},
    )

    engine.event_processor.process_event(coord_event, engine.state)

    # Verify proposal is recorded
    assert len(engine.state.proposals) == 1
    proposal = engine.state.proposals[0]

    assert proposal.round == 1
    assert proposal.status == "PROPOSED"
    assert proposal.simulation_id == engine.simulation_id
    assert engine.state.crisis_state.phase == "NEGOTIATION"

    # Verify coordinator did NOT mutate country state directly
    assert engine.state.countries["country_01"].status == "Coordinating"


def test_multiple_coordination_rounds(sample_simulation_state):
    """
    Verifies Coordinator supports multiple rounds without overwriting proposal history.
    """
    service = CoordinatorService(provider=MockLLMProvider())

    prop_r1 = service.request_coordination_sync(sample_simulation_state, round_index=1)
    sample_simulation_state.proposals.append(prop_r1)

    prop_r2 = service.request_coordination_sync(sample_simulation_state, round_index=2)
    sample_simulation_state.proposals.append(prop_r2)

    assert len(sample_simulation_state.proposals) == 2
    assert sample_simulation_state.proposals[0].round == 1
    assert sample_simulation_state.proposals[1].round == 2
    assert sample_simulation_state.proposals[0].proposal_id != sample_simulation_state.proposals[1].proposal_id


# ── 7. REST API Route Tests ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_coordinate_and_proposals_endpoints():
    scenario = default_data_loader.load_scenario("scenario_01")
    countries = default_data_loader.load_all_countries()

    engine = SimulationEngine(
        scenario=scenario,
        countries=countries,
        mode="coordinated",
    )
    default_simulation_repository.save(engine)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Trigger coordination endpoint
        coord_resp = await client.post(f"/api/simulations/{engine.simulation_id}/coordinate")
        assert coord_resp.status_code == 200
        proposal_data = coord_resp.json()

        assert "proposal_id" in proposal_data
        assert proposal_data["status"] == "PROPOSED"
        assert proposal_data["round"] == 1
        assert len(proposal_data["items"]) > 0

        proposal_id = proposal_data["proposal_id"]

        # 2. List proposals endpoint
        list_resp = await client.get(f"/api/simulations/{engine.simulation_id}/proposals")
        assert list_resp.status_code == 200
        proposals_list = list_resp.json()
        assert len(proposals_list) == 1
        assert proposals_list[0]["proposal_id"] == proposal_id

        # 3. Get single proposal endpoint
        single_resp = await client.get(
            f"/api/simulations/{engine.simulation_id}/proposals/{proposal_id}"
        )
        assert single_resp.status_code == 200
        single_data = single_resp.json()
        assert single_data["proposal_id"] == proposal_id
        assert single_data["title"] == proposal_data["title"]

        # 4. Nonexistent proposal returns 404
        not_found_resp = await client.get(
            f"/api/simulations/{engine.simulation_id}/proposals/prop_nonexistent"
        )
        assert not_found_resp.status_code == 404
