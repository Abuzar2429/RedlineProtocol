"""
Tests for Phase 6 — Negotiation & Voting Logic.
Verifies:
1. Negotiation domain models, Vote validation, and state machine transitions
2. Three-mode voting rules matrix: no_coordination, partial, coordinated
3. Quorum calculations and threshold boundaries
4. Tie handling and abstention (Undecided) behavior
5. Multi-round negotiation, proposal versioning, and max round termination
6. Stable deadlock detection
7. Deterministic replay
8. Simulation engine event integration
9. REST API endpoints
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.negotiation.negotiation_service import default_negotiation_service
from app.negotiation.negotiation_session import NegotiationSessionManager
from app.negotiation.position_service import CountryPositionEvaluator
from app.negotiation.voting_engine import (
    CoordinatedVotingRule,
    NoCoordinationVotingRule,
    PartialCoordinationVotingRule,
    get_voting_rule,
)
from app.schemas.coordinator_models import CoordinatorProposal, PredictedVotes
from app.schemas.data_models import CountryData
from app.schemas.negotiation_models import (
    NegotiationOutcome,
    NegotiationRound,
    NegotiationSession,
    ProposalVersion,
    Vote,
    VotingResult,
)
from app.schemas.simulation_models import (
    CountrySimulationState,
    CrisisOperationalState,
    DecisionRecord,
    SimulationEvent,
    SimulationState,
)
from app.services.data_loader import default_data_loader
from app.services.simulation.engine import SimulationEngine
from app.services.simulation.repository import default_simulation_repository


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_proposal() -> CoordinatorProposal:
    return CoordinatorProposal(
        proposal_id="prop_test_001",
        simulation_id="sim_neg_test",
        event_id="ev_coord_01",
        tick=14,
        round=1,
        title="Emergency AI Model Telemetry Accord",
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


@pytest.fixture
def sample_state() -> SimulationState:
    countries_dict = {}
    for i in range(1, 16):
        cid = f"country_{i:02d}"
        countries_dict[cid] = CountrySimulationState(
            country_id=cid,
            name=f"Country {i}",
            status="Coordinating" if i <= 10 else "Investigating",
            information_completeness=0.8,
        )

    return SimulationState(
        simulation_id="sim_neg_test",
        scenario_id="scenario_01",
        mode="coordinated",
        status="RUNNING",
        current_tick=15,
        current_time="T+15",
        crisis_state=CrisisOperationalState(
            scenario_id="scenario_01",
            phase="NEGOTIATION",
            severity="high",
            severity_score=0.8,
            current_risk=75.0,
            origin_country="country_01",
            affected_countries=["country_01", "country_02"],
            title="The Autonomous Defection Crisis",
            summary="Frontier autonomous military model showing uncontrolled exfiltration.",
        ),
        countries=countries_dict,
        decisions=[
            DecisionRecord(
                decision_id="dec_01",
                simulation_id="sim_neg_test",
                country_id="country_01",
                tick=10,
                action_id="share_telemetry_multilateral",
                label="Share Telemetry",
                reasoning="Vital national security interest to coordinate.",
                willingness_to_coordinate=0.90,
            ),
            DecisionRecord(
                decision_id="dec_02",
                simulation_id="sim_neg_test",
                country_id="country_02",
                tick=12,
                action_id="share_telemetry_multilateral",
                label="Share Telemetry",
                reasoning="Protect sovereign infrastructure through coordination.",
                willingness_to_coordinate=0.80,
            ),
        ],
        proposals=[],
        negotiations=[],
        event_history=[],
    )


# ── 1. Domain Model & Validation Tests ───────────────────────────────────────

def test_vote_normalization():
    v1 = Vote(
        vote_id="v_01",
        country_id="country_01",
        round=1,
        proposal_id="prop_01",
        proposal_version=1,
        vote="approve",  # lowercase alias
        rationale="Endorsed",
    )
    assert v1.vote == "Approve"

    v2 = Vote(
        vote_id="v_02",
        country_id="country_02",
        round=1,
        proposal_id="prop_01",
        proposal_version=1,
        vote="abstain",  # alias for Undecided
        rationale="Abstaining",
    )
    assert v2.vote == "Undecided"

    v3 = Vote(
        vote_id="v_03",
        country_id="country_03",
        round=1,
        proposal_id="prop_01",
        proposal_version=1,
        vote="Oppose",  # alias for Reject
        rationale="Dissenting",
    )
    assert v3.vote == "Reject"


def test_negotiation_session_creation(sample_state, sample_proposal):
    session = NegotiationSessionManager.create_session(
        state=sample_state,
        initial_proposal=sample_proposal,
        max_rounds=3,
    )
    assert session.status == "PROPOSED"
    assert session.current_round == 1
    assert session.max_rounds == 3
    assert len(session.proposal_versions) == 1
    assert session.proposal_versions[0].version == 1
    assert session.proposal_versions[0].proposal_id == sample_proposal.proposal_id
    assert len(session.participating_countries) == 15


def test_illegal_state_transition(sample_state, sample_proposal):
    session = NegotiationSessionManager.create_session(sample_state, sample_proposal)
    with pytest.raises(ValueError, match="Invalid negotiation state transition"):
        NegotiationSessionManager.transition(session, "ACCEPTED")


# ── 2. Three Coordination Modes Voting Matrix ────────────────────────────────

def test_mode_no_coordination_always_fails(sample_proposal):
    rule = get_voting_rule("no_coordination")
    assert isinstance(rule, NoCoordinationVotingRule)

    v1 = ProposalVersion(
        version=1,
        proposal_id=sample_proposal.proposal_id,
        title=sample_proposal.title,
        summary=sample_proposal.summary,
        items=sample_proposal.items,
        rationale=sample_proposal.rationale,
    )

    eligible = [f"country_{i:02d}" for i in range(1, 16)]
    # Even if 100% vote Approve
    votes = {
        cid: Vote(
            vote_id=f"v_{cid}", country_id=cid, round=1,
            proposal_id="p1", proposal_version=1, vote="Approve", rationale="Support"
        )
        for cid in eligible
    }

    result = rule.evaluate(1, v1, votes, eligible)
    assert result.passed is False
    assert result.status == "FAILED"
    assert "no_coordination" in result.failure_reason


def test_mode_partial_coordination_simple_majority(sample_proposal):
    rule = get_voting_rule("partial")
    assert isinstance(rule, PartialCoordinationVotingRule)

    v1 = ProposalVersion(
        version=1,
        proposal_id=sample_proposal.proposal_id,
        title=sample_proposal.title,
        summary=sample_proposal.summary,
        items=sample_proposal.items,
        rationale=sample_proposal.rationale,
    )
    eligible = [f"country_{i:02d}" for i in range(1, 11)]  # 10 countries

    # 6 Approve, 4 Reject -> 60% > 50% -> Passes
    votes = {}
    for i, cid in enumerate(eligible):
        v_choice = "Approve" if i < 6 else "Reject"
        votes[cid] = Vote(
            vote_id=f"v_{cid}", country_id=cid, round=1,
            proposal_id="p1", proposal_version=1, vote=v_choice, rationale="R"
        )

    res = rule.evaluate(1, v1, votes, eligible)
    assert res.is_quorum_met is True
    assert res.passed is True
    assert res.status == "PASSED"
    assert res.achieved_threshold == 0.60


def test_mode_partial_tie_fails(sample_proposal):
    rule = PartialCoordinationVotingRule()
    v1 = ProposalVersion(
        version=1, proposal_id="p1", title="T", summary="S", items=["I"], rationale="R"
    )
    eligible = [f"country_{i:02d}" for i in range(1, 11)]

    # 5 Approve, 5 Reject -> Tie -> Fails simple majority
    votes = {}
    for i, cid in enumerate(eligible):
        v_choice = "Approve" if i < 5 else "Reject"
        votes[cid] = Vote(
            vote_id=f"v_{cid}", country_id=cid, round=1,
            proposal_id="p1", proposal_version=1, vote=v_choice, rationale="R"
        )

    res = rule.evaluate(1, v1, votes, eligible)
    assert res.passed is False
    assert res.status == "TIE"


def test_mode_coordinated_qualified_majority(sample_proposal):
    rule = get_voting_rule("coordinated")
    assert isinstance(rule, CoordinatedVotingRule)

    v1 = ProposalVersion(
        version=1, proposal_id="p1", title="T", summary="S", items=["I"], rationale="R"
    )
    eligible = [f"country_{i:02d}" for i in range(1, 11)]  # 10 countries

    # Case A: 6 Approve, 4 Reject -> 6/10 = 60.0% -> Meets 60% Qualified Majority -> Passes!
    votes_pass = {
        cid: Vote(
            vote_id=f"v_{cid}", country_id=cid, round=1,
            proposal_id="p1", proposal_version=1,
            vote="Approve" if idx < 6 else "Reject", rationale="R"
        )
        for idx, cid in enumerate(eligible)
    }
    res_pass = rule.evaluate(1, v1, votes_pass, eligible)
    assert res_pass.passed is True
    assert res_pass.status == "PASSED"
    assert res_pass.achieved_threshold == 0.60

    # Case B: 5 Approve, 5 Reject -> 50.0% < 60% -> Fails
    votes_fail = {
        cid: Vote(
            vote_id=f"v_{cid}", country_id=cid, round=1,
            proposal_id="p1", proposal_version=1,
            vote="Approve" if idx < 5 else "Reject", rationale="R"
        )
        for idx, cid in enumerate(eligible)
    }
    res_fail = rule.evaluate(1, v1, votes_fail, eligible)
    assert res_fail.passed is False
    assert res_fail.status == "TIE"


# ── 3. Quorum & Abstention Edge Cases ────────────────────────────────────────

def test_quorum_failure_coordinated(sample_proposal):
    rule = CoordinatedVotingRule()  # Quorum = 60%
    v1 = ProposalVersion(
        version=1, proposal_id="p1", title="T", summary="S", items=["I"], rationale="R"
    )
    eligible = [f"country_{i:02d}" for i in range(1, 11)]  # 10 countries

    # Only 5 countries vote (50% < 60% required quorum)
    votes = {
        f"country_{i:02d}": Vote(
            vote_id=f"v_{i}", country_id=f"country_{i:02d}", round=1,
            proposal_id="p1", proposal_version=1, vote="Approve", rationale="R"
        )
        for i in range(1, 6)
    }

    res = rule.evaluate(1, v1, votes, eligible)
    assert res.is_quorum_met is False
    assert res.passed is False
    assert res.status == "NO_QUORUM"


def test_abstentions_count_to_quorum_not_denominator(sample_proposal):
    rule = CoordinatedVotingRule()
    v1 = ProposalVersion(
        version=1, proposal_id="p1", title="T", summary="S", items=["I"], rationale="R"
    )
    eligible = [f"country_{i:02d}" for i in range(1, 11)]  # 10 countries

    # 4 Approve, 1 Reject, 5 Undecided
    # Quorum: 10/10 = 100% (Met!)
    # Non-abstaining: 4 + 1 = 5
    # Achieved: 4/5 = 80.0% >= 60.0% -> Passes!
    votes = {}
    for i, cid in enumerate(eligible):
        if i < 4:
            v_choice = "Approve"
        elif i < 5:
            v_choice = "Reject"
        else:
            v_choice = "Undecided"
        votes[cid] = Vote(
            vote_id=f"v_{cid}", country_id=cid, round=1,
            proposal_id="p1", proposal_version=1, vote=v_choice, rationale="R"
        )

    res = rule.evaluate(1, v1, votes, eligible)
    assert res.is_quorum_met is True
    assert res.abstentions == 5
    assert res.achieved_threshold == 0.80
    assert res.passed is True
    assert res.status == "PASSED"


def test_all_abstentions_fails(sample_proposal):
    rule = CoordinatedVotingRule()
    v1 = ProposalVersion(
        version=1, proposal_id="p1", title="T", summary="S", items=["I"], rationale="R"
    )
    eligible = [f"country_{i:02d}" for i in range(1, 11)]

    # All Undecided
    votes = {
        cid: Vote(
            vote_id=f"v_{cid}", country_id=cid, round=1,
            proposal_id="p1", proposal_version=1, vote="Undecided", rationale="R"
        )
        for cid in eligible
    }
    res = rule.evaluate(1, v1, votes, eligible)
    assert res.is_quorum_met is True
    assert res.passed is False
    assert res.status == "INSUFFICIENT_SUPPORT"


# ── 4. Multi-Round Negotiation & Revisions ───────────────────────────────────

def test_multi_round_negotiation_success_in_round_2(sample_state, sample_proposal):
    countries_map = {c.id: c for c in default_data_loader.load_all_countries()}
    session = NegotiationSessionManager.create_session(sample_state, sample_proposal, max_rounds=3)

    # Round 1: Inject votes that will FAIL (e.g. 5 Approve, 5 Reject, 5 Undecided -> 50% < 60%)
    manual_r1 = {}
    for i, cid in enumerate(session.participating_countries):
        if i < 5:
            v = "Approve"
        elif i < 10:
            v = "Reject"
        else:
            v = "Undecided"
        manual_r1[cid] = Vote(
            vote_id=f"v_{cid}_1", country_id=cid, round=1,
            proposal_id=sample_proposal.proposal_id, proposal_version=1,
            vote=v, rationale="Round 1 position",
            objections_raised=["Telemetry disclosure too broad"] if v == "Reject" else [],
        )

    round_1_rec = NegotiationSessionManager.run_round(session, sample_state, countries_map, manual_votes=manual_r1)
    assert round_1_rec.voting_result.passed is False
    assert session.status == "REVISION_REQUIRED"
    assert session.current_round == 2
    assert len(session.proposal_versions) == 2
    assert "Telemetry disclosure too broad" in session.proposal_versions[1].unresolved_issues

    # Round 2: Compromise drafted -> 10 Approve, 2 Reject, 3 Undecided (10/12 = 83.3% >= 60%)
    manual_r2 = {}
    for i, cid in enumerate(session.participating_countries):
        if i < 10:
            v = "Approve"
        elif i < 12:
            v = "Reject"
        else:
            v = "Undecided"
        manual_r2[cid] = Vote(
            vote_id=f"v_{cid}_2", country_id=cid, round=2,
            proposal_id=sample_proposal.proposal_id, proposal_version=2,
            vote=v, rationale="Round 2 compromise endorsed",
        )

    round_2_rec = NegotiationSessionManager.run_round(session, sample_state, countries_map, manual_votes=manual_r2)
    assert round_2_rec.voting_result.passed is True
    assert session.status == "ACCEPTED"
    assert session.outcome is not None
    assert session.outcome.agreement_reached is True
    assert session.outcome.rounds_completed == 2
    assert session.outcome.final_proposal_version == 2


def test_max_rounds_termination(sample_state, sample_proposal):
    countries_map = {c.id: c for c in default_data_loader.load_all_countries()}
    session = NegotiationSessionManager.create_session(sample_state, sample_proposal, max_rounds=2)

    # Force 2 rounds of rejections
    for r in [1, 2]:
        manual = {
            cid: Vote(
                vote_id=f"v_{cid}_{r}", country_id=cid, round=r,
                proposal_id=sample_proposal.proposal_id, proposal_version=r,
                vote="Reject" if (i + r) % 2 == 0 else "Approve",  # Alternating to avoid deadlock detector
                rationale="Dissenting",
            )
            for i, cid in enumerate(session.participating_countries)
        }
        NegotiationSessionManager.run_round(session, sample_state, countries_map, manual_votes=manual)

    assert session.status == "MAX_ROUNDS_REACHED"
    assert session.outcome is not None
    assert session.outcome.agreement_reached is False
    assert session.outcome.rounds_completed == 2


def test_deadlock_detection_terminates_negotiation(sample_state, sample_proposal):
    countries_map = {c.id: c for c in default_data_loader.load_all_countries()}
    session = NegotiationSessionManager.create_session(sample_state, sample_proposal, max_rounds=3)

    # Two consecutive rounds with identical vote counts
    identical_votes = {
        cid: Vote(
            vote_id=f"v_{cid}", country_id=cid, round=1,
            proposal_id=sample_proposal.proposal_id, proposal_version=1,
            vote="Approve" if i < 5 else "Reject",
            rationale="Unchanging position",
        )
        for i, cid in enumerate(session.participating_countries)
    }

    # Round 1
    NegotiationSessionManager.run_round(session, sample_state, countries_map, manual_votes=identical_votes)
    assert session.status == "REVISION_REQUIRED"

    # Round 2: same votes submitted
    identical_votes_r2 = {
        cid: Vote(
            vote_id=f"v_{cid}_2", country_id=cid, round=2,
            proposal_id=sample_proposal.proposal_id, proposal_version=2,
            vote="Approve" if i < 5 else "Reject",
            rationale="Unchanging position",
        )
        for i, cid in enumerate(session.participating_countries)
    }
    NegotiationSessionManager.run_round(session, sample_state, countries_map, manual_votes=identical_votes_r2)

    assert session.status == "BREAKDOWN"
    assert session.outcome.agreement_reached is False
    assert "Deadlock" in session.outcome.failure_reason


# ── 5. Deterministic Replay Test ─────────────────────────────────────────────

def test_deterministic_replay(sample_state, sample_proposal):
    """
    Determinism requirement: running the negotiation twice on identical state
    produces identical results, vote tallies, and statuses.
    """
    countries_map = {c.id: c for c in default_data_loader.load_all_countries()}

    # Session A
    session_a = NegotiationSessionManager.create_session(sample_state, sample_proposal, max_rounds=3)
    outcome_a = default_negotiation_service.run_full_negotiation(session_a, sample_state)

    # Session B
    session_b = NegotiationSessionManager.create_session(sample_state, sample_proposal, max_rounds=3)
    outcome_b = default_negotiation_service.run_full_negotiation(session_b, sample_state)

    assert outcome_a.final_status == outcome_b.final_status
    assert outcome_a.agreement_reached == outcome_b.agreement_reached
    assert outcome_a.rounds_completed == outcome_b.rounds_completed
    assert outcome_a.supporting_countries == outcome_b.supporting_countries
    assert outcome_a.opposing_countries == outcome_b.opposing_countries
    assert outcome_a.abstaining_countries == outcome_b.abstaining_countries


# ── 6. Simulation Engine Event Integration ───────────────────────────────────

def test_simulation_engine_coordination_and_negotiation():
    scenario = default_data_loader.load_scenario("scenario_01")
    countries = default_data_loader.load_all_countries()

    engine = SimulationEngine(
        scenario=scenario,
        countries=countries,
        mode="coordinated",
    )

    # Trigger a COORDINATION_REQUEST event
    coord_event = SimulationEvent(
        event_id="ev_coord_test",
        tick=14,
        event_type="COORDINATION_REQUEST",
        description="Emergency multilateral AI summit convened.",
        payload={"title": "Emergency Summit"},
    )

    engine.event_processor.process_event(coord_event, engine.state)

    # Verify both Proposal and NegotiationSession were generated
    assert len(engine.state.proposals) >= 1
    assert len(engine.state.negotiations) >= 1

    session = engine.state.negotiations[0]
    assert session.coordination_mode == "coordinated"
    assert len(session.rounds) >= 1
    assert session.outcome is not None


# ── 7. REST API Endpoints ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_negotiation_lifecycle():
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
        # 1. Run negotiation endpoint
        neg_resp = await client.post(f"/api/simulations/{engine.simulation_id}/negotiate")
        assert neg_resp.status_code == 200
        outcome = neg_resp.json()
        assert "negotiation_id" in outcome
        assert "final_status" in outcome
        assert outcome["rounds_completed"] >= 1

        neg_id = outcome["negotiation_id"]

        # 2. List negotiations endpoint
        list_resp = await client.get(f"/api/simulations/{engine.simulation_id}/negotiations")
        assert list_resp.status_code == 200
        neg_list = list_resp.json()
        assert len(neg_list) == 1
        assert neg_list[0]["negotiation_id"] == neg_id

        # 3. Get single negotiation session endpoint
        single_resp = await client.get(f"/api/simulations/{engine.simulation_id}/negotiations/{neg_id}")
        assert single_resp.status_code == 200
        single_neg = single_resp.json()
        assert single_neg["negotiation_id"] == neg_id
        assert len(single_neg["rounds"]) >= 1

        # 4. Get outcome endpoint
        out_resp = await client.get(f"/api/simulations/{engine.simulation_id}/negotiations/{neg_id}/outcome")
        assert out_resp.status_code == 200
        assert out_resp.json()["negotiation_id"] == neg_id
