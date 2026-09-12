"""
Comprehensive Tests for Phase 4: Country Agents (LLM + Prompts).
- Country Agent creation and identity derivation for all 15 fictional nations
- Prompt generation and separation of system rules vs dynamic simulation data
- Information boundary enforcement (no future/private leaks)
- Structured output validation & Pydantic schema enforcement
- Mock LLM Provider behavior (deterministic responses, simulated errors/timeouts)
- Deterministic fallback execution on provider failure
- End-to-end integration of Country Agents with the Simulation Engine
"""
import os
import pytest

from app.agents.agent_models import CountryDecisionResponse, DecisionContext
from app.agents.agent_prompt import (
    COUNTRY_AGENT_PROMPT_VERSION,
    build_country_system_prompt,
    build_country_user_prompt,
)
from app.agents.context_builder import DecisionContextBuilder
from app.agents.country_agent import CountryAgent
from app.agents.decision_service import CountryDecisionService
from app.llm.mock_provider import MockLLMProvider
from app.schemas.simulation_models import SimulationEvent
from app.services.data_loader import default_data_loader
from app.services.simulation.engine import SimulationEngine


# ── Agent Creation & Identity Tests ───────────────────────────────────────────

def test_all_15_countries_can_create_agents():
    countries = default_data_loader.load_all_countries()
    assert len(countries) == 15

    provider = MockLLMProvider()
    for country in countries:
        agent = CountryAgent(country=country, provider=provider)
        assert agent.country.id == country.id
        assert country.name in agent.system_prompt
        assert country.risk_tolerance in agent.system_prompt
        assert country.ai_capability_level in agent.system_prompt
        for priority in country.strategic_priorities[:2]:
            assert priority in agent.system_prompt


def test_system_prompt_structure_and_versioning():
    country = default_data_loader.load_country("country_01")
    system_prompt = build_country_system_prompt(country)

    assert "Federal Republic of Alerion" in system_prompt
    assert "UNTRUSTED DATA" in system_prompt
    assert "Return your decision strictly in valid JSON" in system_prompt
    assert COUNTRY_AGENT_PROMPT_VERSION == "1.0"


# ── Information Boundary Tests ────────────────────────────────────────────────

def test_information_boundary_filters_future_and_private_events():
    country = default_data_loader.load_country("country_02")
    engine = SimulationEngine.create("scenario_01")

    # Manually add historical, future, and private events to history
    engine.state.current_tick = 5
    engine.state.current_time = "T+05"

    past_public_event = SimulationEvent(
        event_id="past_pub",
        tick=3,
        priority=3,
        event_type="TIMELINE_EVENT",
        description="Public regional power desync detected.",
    )
    future_event = SimulationEvent(
        event_id="future_secret",
        tick=10,
        priority=3,
        event_type="TIMELINE_EVENT",
        description="Future catastrophic meltdown at T+10.",
    )
    other_country_private_event = SimulationEvent(
        event_id="other_priv",
        tick=4,
        priority=2,
        event_type="POLICY_ACTION",
        source="country_01",
        affected_countries=["country_01"],
        description="Country 01 executes top-secret internal wiretap.",
        payload={"visibility": "private"},
    )

    engine.state.event_history = [
        past_public_event,
        future_event,
        other_country_private_event,
    ]

    context = DecisionContextBuilder.build_context(
        country=country,
        state=engine.state,
        scenario=engine.scenario,
    )

    # Convert context public events to single string
    events_blob = " ".join(context.known_public_events)

    # 1. Past public event MUST be present
    assert "Public regional power desync detected." in events_blob

    # 2. Future event MUST NOT be leaked
    assert "Future catastrophic meltdown" not in events_blob
    assert "T+10" not in events_blob

    # 3. Other country's private internal action MUST NOT be leaked
    assert "top-secret internal wiretap" not in events_blob


def test_user_prompt_data_separation():
    country = default_data_loader.load_country("country_01")
    engine = SimulationEngine.create("scenario_01")
    context = DecisionContextBuilder.build_context(country, engine.state, engine.scenario)
    user_prompt = build_country_user_prompt(context)

    # Verify prompt clearly delimits data from instructions
    assert "### SIMULATION DATA" in user_prompt
    assert "### AVAILABLE ACTIONS" in user_prompt
    assert "### TASK" in user_prompt
    assert "Federal Republic of Alerion" in user_prompt


# ── Structured Decision Output Validation Tests ───────────────────────────────

def test_valid_structured_decision_parsing():
    raw = {
        "action_id": "notify_affected",
        "reasoning": "Immediate transparency alerts allies while preserving our defense perimeter.",
        "risks": ["Potential market jitter."],
        "expected_reactions": "Allies will appreciate early warning.",
        "willingness_to_coordinate": 0.85,
    }
    obj = CountryDecisionResponse.model_validate(raw)
    assert obj.action_id == "notify_affected"
    assert obj.willingness_to_coordinate == 0.85
    assert len(obj.risks) == 1


def test_structured_decision_alias_fallback():
    # Model returns aliases 'decision' and 'justification'
    raw = {
        "decision": "suspend_ai_system",
        "justification": "Precautionary suspension prevents cascading systemic failure.",
        "confidence": 0.90,
    }
    obj = CountryDecisionResponse.model_validate(raw)
    assert obj.action_id == "suspend_ai_system"
    assert "Precautionary" in obj.reasoning
    assert obj.willingness_to_coordinate == 0.90


def test_invalid_decision_validation():
    with pytest.raises(Exception):
        # Empty action_id
        CountryDecisionResponse.model_validate({"action_id": "", "reasoning": "some text"})

    with pytest.raises(Exception):
        # Out of bounds willingness
        CountryDecisionResponse.model_validate(
            {"action_id": "act", "reasoning": "some text", "willingness_to_coordinate": 2.5}
        )


# ── Mock Provider & Fallback Tests ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_country_agent_successful_mock_decision():
    country = default_data_loader.load_country("country_01")
    scenario = default_data_loader.load_scenario("scenario_01")
    engine = SimulationEngine.create("scenario_01")

    mock_provider = MockLLMProvider()
    agent = CountryAgent(country=country, provider=mock_provider)

    decision = await agent.decide(engine.state, scenario, tick=2)

    assert decision.country_id == "country_01"
    assert decision.source == "llm_agent"
    assert decision.provider == "mock"
    assert decision.action_id in [a.id for a in scenario.available_actions]
    assert len(decision.reasoning) > 20
    assert decision.willingness_to_coordinate is not None
    assert decision.prompt_version == COUNTRY_AGENT_PROMPT_VERSION


@pytest.mark.asyncio
async def test_country_agent_fallback_on_provider_error():
    country = default_data_loader.load_country("country_02")
    scenario = default_data_loader.load_scenario("scenario_01")
    engine = SimulationEngine.create("scenario_01")

    # Configure provider to simulate 503 error
    error_provider = MockLLMProvider(simulate_error=True)
    agent = CountryAgent(country=country, provider=error_provider, max_retries=1)

    decision = await agent.decide(engine.state, scenario, tick=3)

    assert decision.country_id == "country_02"
    assert decision.source == "deterministic_fallback"
    assert decision.action_id in [a.id for a in scenario.available_actions]
    assert "Fallback triggered" in decision.risks_noted


@pytest.mark.asyncio
async def test_country_agent_fallback_on_timeout():
    country = default_data_loader.load_country("country_03")
    scenario = default_data_loader.load_scenario("scenario_01")
    engine = SimulationEngine.create("scenario_01")

    timeout_provider = MockLLMProvider(simulate_timeout=True)
    agent = CountryAgent(country=country, provider=timeout_provider, max_retries=0)

    decision = await agent.decide(engine.state, scenario, tick=4)

    assert decision.source == "deterministic_fallback"
    assert decision.country_id == "country_03"


@pytest.mark.asyncio
async def test_country_agent_fallback_on_malformed_json():
    country = default_data_loader.load_country("country_04")
    scenario = default_data_loader.load_scenario("scenario_01")
    engine = SimulationEngine.create("scenario_01")

    malformed_provider = MockLLMProvider(simulate_malformed=True)
    agent = CountryAgent(country=country, provider=malformed_provider, max_retries=0)

    decision = await agent.decide(engine.state, scenario, tick=5)

    assert decision.source == "deterministic_fallback"
    assert decision.country_id == "country_04"


# ── Decision Service Tests ────────────────────────────────────────────────────

def test_decision_service_caching_and_sync_call():
    provider = MockLLMProvider()
    service = CountryDecisionService(provider=provider)

    agent_1 = service.get_agent("country_01")
    agent_2 = service.get_agent("country_01")
    assert agent_1 is agent_2  # Cached instance

    engine = SimulationEngine.create("scenario_01")
    decision = service.request_decision_sync(
        country_id="country_01",
        state=engine.state,
        scenario=engine.scenario,
        tick=2,
    )
    assert decision.source == "llm_agent"
    assert decision.country_id == "country_01"


# ── Integration: Full Simulation Run with Country Agents ──────────────────────

def test_full_simulation_run_with_country_agents():
    """
    Runs scenario_01 completely using Country Agents backed by MockLLMProvider.
    Verifies that all recorded decisions come from the agent layer.
    """
    mock_provider = MockLLMProvider()
    decision_service = CountryDecisionService(provider=mock_provider)

    engine = SimulationEngine.create(
        "scenario_01",
        max_ticks=80,
        decision_service=decision_service,
    )

    final_state = engine.run_until_complete()

    assert final_state.status == "COMPLETED"
    assert len(final_state.decisions) > 5

    # Verify at least one decision came from llm_agent
    llm_decisions = [d for d in final_state.decisions if d.source == "llm_agent"]
    assert len(llm_decisions) >= 1

    # Verify every decision has valid action_id from scenario
    valid_actions = {a.id for a in engine.scenario.available_actions}
    for dec in final_state.decisions:
        assert dec.action_id in valid_actions
        assert len(dec.reasoning) > 10


# ── Optional Real LLM Smoke Test ──────────────────────────────────────────────

@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set; skipping live Anthropic smoke test",
)
@pytest.mark.asyncio
async def test_real_anthropic_llm_smoke():
    from app.llm.anthropic_provider import AnthropicProvider

    api_key = os.getenv("ANTHROPIC_API_KEY")
    provider = AnthropicProvider(api_key=api_key)
    country = default_data_loader.load_country("country_01")
    agent = CountryAgent(country=country, provider=provider)
    engine = SimulationEngine.create("scenario_01")

    decision = await agent.decide(engine.state, engine.scenario, tick=1)
    assert decision.country_id == "country_01"
    assert decision.source in ("llm_agent", "deterministic_fallback")
