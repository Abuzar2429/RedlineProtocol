"""
Redline-LLM Dataset Generation Engine (Phase 1).

Extracts, synthesizes, and compiles domain-specific training datasets from the
RedlineProtocol simulation platform:
1. Supervised Fine-Tuning (SFT) Dataset (ChatML / Messages format):
   - Country Agent Strategic Decision-Making (Doctrinal policy under crisis)
   - International Coordinator Mediation & Consensus (Multilateral treaty drafting)
   - Governance Framework & Regulatory Compliance QA (EU AI Act, NIST RMF, OECD, etc.)
2. Direct Preference Optimization (DPO) Dataset (Chosen vs. Rejected pairs):
   - Aligned with the 4-Pillar Scoring Engine (Risk, Time, Consensus, Liability)

Outputs:
- training/data/redline_sft_train.jsonl
- training/data/redline_sft_val.jsonl
- training/data/redline_dpo_train.jsonl
- training/data/dataset_summary.json
"""
import json
import logging
import os
import random
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add backend directory to sys.path to access app modules
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.data_loader import DataLoader
from app.schemas.data_models import CountryData, ScenarioData, GovernanceDocument
from app.agents.agent_prompt import build_country_system_prompt, build_country_user_prompt
from app.agents.coordinator_prompt import build_coordinator_system_prompt, build_coordinator_user_prompt
from app.agents.agent_models import DecisionContext
from app.schemas.coordinator_models import (
    CoordinatorContext,
    DeterministicAggregation,
    CountryPositionSummary,
)
from app.services.simulation.decision_maker import DeterministicDecisionMaker
from app.schemas.simulation_models import CountrySimulationState

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("redline_dataset_generator")

OUTPUT_DIR = BASE_DIR / "training" / "data"


class RedlineDatasetGenerator:
    """
    Synthesizes and exports training datasets for the Redline AI Governance LLM.
    """

    def __init__(self, data_loader: Optional[DataLoader] = None, seed: int = 42):
        self.loader = data_loader or DataLoader(data_dir=BACKEND_DIR / "data")
        random.seed(seed)
        self.countries: List[CountryData] = self.loader.load_all_countries()
        self.scenarios: List[ScenarioData] = self.loader.load_all_scenarios()
        self.governance_docs: List[GovernanceDocument] = self.loader.load_governance_documents()
        self.country_map: Dict[str, CountryData] = {c.id: c for c in self.countries}

    # ── Task 1: Country Agent Strategic Decision-Making ────────────────────────

    def generate_country_decision_samples(self) -> List[Dict[str, Any]]:
        """
        Generates SFT samples simulating country delegates facing crisis ticks.
        """
        samples: List[Dict[str, Any]] = []

        # Ticks to sample across crisis progression
        sample_ticks = [0, 3, 5, 8, 10, 14, 18, 22, 25]

        for scenario in self.scenarios:
            for country in self.countries:
                system_prompt = build_country_system_prompt(country)

                # Determine info delay for this country
                delay = scenario.information_delay.get(country.id, 5)

                for tick in sample_ticks:
                    # Determine awareness and completeness based on tick and delay
                    if tick < delay:
                        awareness = "unaware"
                        completeness = 0.0
                        known_events = []
                    elif tick == delay:
                        awareness = "alerted"
                        completeness = scenario.initial_evidence_completeness
                        known_events = [e.event for e in scenario.timeline if e.time_offset <= tick]
                    else:
                        awareness = "verified"
                        growth = (tick - delay) * scenario.evidence_grows_at
                        completeness = min(1.0, scenario.initial_evidence_completeness + growth)
                        known_events = [e.event for e in scenario.timeline if e.time_offset <= tick]

                    # RAG snippet relevance
                    rag_snippets = []
                    for doc_id in scenario.governance_docs_relevant:
                        doc = next((d for d in self.governance_docs if d.metadata.doc_id == doc_id), None)
                        if doc:
                            lines = [ln for ln in doc.content.split("\n") if ln.startswith("### ") or ln.startswith("## ")]
                            summary_section = doc.content[:400].strip()
                            rag_snippets.append(f"[{doc.metadata.title}]\n{summary_section}...")

                    rag_context_str = "\n\n".join(rag_snippets[:2]) if rag_snippets else ""

                    # Build context
                    context = DecisionContext(
                        country_id=country.id,
                        country_name=country.name,
                        current_tick=tick,
                        current_time=f"T+{tick:02d}",
                        crisis_title=scenario.title,
                        crisis_description=scenario.description,
                        awareness_status=awareness,
                        evidence_completeness_pct=completeness * 100.0,
                        national_priorities=country.strategic_priorities,
                        risk_tolerance=country.risk_tolerance,
                        coordination_willingness=country.coordination_willingness,
                        ai_policy_position=country.ai_policy_position,
                        known_public_events=known_events[-3:],
                        allies=country.allies,
                        rivals=country.rivals,
                        available_actions=[a.model_dump() for a in scenario.available_actions],
                        rag_context=rag_context_str,
                    )

                    user_prompt = build_country_user_prompt(context)

                    # Determine target decision using domain decision engine
                    sim_state = CountrySimulationState(
                        country_id=country.id,
                        name=country.name,
                        status="Coordinating" if awareness == "verified" else "Investigating",
                        aware=(awareness != "unaware"),
                        information_completeness=completeness,
                    )

                    decision_rec = DeterministicDecisionMaker.evaluate_decision(
                        simulation_id=f"synth_{scenario.id}",
                        country=country,
                        country_state=sim_state,
                        available_actions=scenario.available_actions,
                        tick=tick,
                    )

                    # Calculate willingness based on traits
                    base_willingness = 0.5
                    if country.coordination_willingness == "high":
                        base_willingness = 0.85
                    elif country.coordination_willingness == "low":
                        base_willingness = 0.20

                    if completeness > 0.7:
                        base_willingness += 0.05
                    willingness = max(0.05, min(0.98, base_willingness + (random.random() * 0.1 - 0.05)))

                    # Construct expected reactions
                    ally_names = [self.country_map[a].name for a in country.allies if a in self.country_map]
                    rival_names = [self.country_map[r].name for r in country.rivals if r in self.country_map]

                    expected_reactions = (
                        f"Allied nations ({', '.join(ally_names) if ally_names else 'regional partners'}) "
                        f"are expected to support this measure as consistent with joint stability. "
                        f"Strategic rivals ({', '.join(rival_names) if rival_names else 'competing blocs'}) "
                        f"may scrutinize execution for unilateral technological or economic advantage."
                    )

                    risks_val = [decision_rec.risks_noted] if isinstance(decision_rec.risks_noted, str) else (decision_rec.risks_noted or ["Uncertainty regarding asymmetric partner compliance"])

                    assistant_payload = {
                        "action_id": decision_rec.action_id,
                        "reasoning": decision_rec.reasoning,
                        "risks": risks_val,
                        "expected_reactions": expected_reactions,
                        "willingness_to_coordinate": round(willingness, 2),
                    }

                    assistant_content = json.dumps(assistant_payload, indent=2)

                    sample = {
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                            {"role": "assistant", "content": assistant_content},
                        ],
                        "metadata": {
                            "task_type": "country_decision",
                            "scenario_id": scenario.id,
                            "country_id": country.id,
                            "tick": tick,
                            "action_id": decision_rec.action_id,
                        },
                    }
                    samples.append(sample)

        return samples

    # ── Task 2: International Coordinator Mediation & Consensus ────────────────

    def generate_coordinator_samples(self) -> List[Dict[str, Any]]:
        """
        Generates SFT samples simulating the International Coordinator synthesizing
        multi-nation positions and drafting multilateral resolutions.
        """
        samples: List[Dict[str, Any]] = []

        coordination_modes = ["unilateral", "coalition", "multilateral"]

        for scenario in self.scenarios:
            for mode in coordination_modes:
                for tick in [5, 10, 15, 20]:
                    system_prompt = build_coordinator_system_prompt()

                    # Select subset of active participating countries
                    if mode == "unilateral":
                        active_countries = self.countries[:3]
                    elif mode == "coalition":
                        active_countries = [c for c in self.countries if c.geopolitical_bloc in ("bloc_a", "bloc_b")]
                    else:
                        active_countries = self.countries  # All 15

                    participating_positions: List[CountryPositionSummary] = []
                    action_counts: Dict[str, int] = {}

                    for c in active_countries:
                        sim_state = CountrySimulationState(
                            country_id=c.id,
                            name=c.name,
                            status="Coordinating",
                            aware=True,
                            information_completeness=0.75,
                        )
                        dec = DeterministicDecisionMaker.evaluate_decision(
                            simulation_id=f"coord_{scenario.id}",
                            country=c,
                            country_state=sim_state,
                            available_actions=scenario.available_actions,
                            tick=tick,
                        )
                        act_id = dec.action_id
                        action_counts[act_id] = action_counts.get(act_id, 0) + 1

                        w = 0.85 if c.coordination_willingness == "high" else (0.25 if c.coordination_willingness == "low" else 0.55)

                        c_risks = [dec.risks_noted] if isinstance(dec.risks_noted, str) else (dec.risks_noted or [])

                        participating_positions.append(
                            CountryPositionSummary(
                                country_id=c.id,
                                country_name=c.name,
                                status="verified",
                                action_id=act_id,
                                action_name=dec.label,
                                willingness_to_coordinate=w,
                                risks_noted=c_risks,
                            )
                        )

                    high_c = sum(1 for p in participating_positions if p.willingness_to_coordinate >= 0.70)
                    mod_c = sum(1 for p in participating_positions if 0.40 <= p.willingness_to_coordinate < 0.70)
                    low_c = sum(1 for p in participating_positions if p.willingness_to_coordinate < 0.40)
                    majority_act = max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else "investigate_internally"

                    agg = DeterministicAggregation(
                        total_countries=len(active_countries),
                        aware_countries=len(active_countries),
                        action_counts=action_counts,
                        high_coordination_count=high_c,
                        moderate_coordination_count=mod_c,
                        low_coordination_count=low_c,
                        majority_action=majority_act,
                    )

                    current_ev = {
                        "event_id": f"ev_{scenario.id}_{tick}",
                        "title": f"{scenario.title} - Phase T+{tick}",
                        "description": f"Crisis telemetry confirmed across {len(active_countries)} observing nations with severity index {scenario.severity_score}.",
                    }

                    context = CoordinatorContext(
                        simulation_id=f"sim_{scenario.id}_{mode}",
                        current_tick=tick,
                        current_time=f"T+{tick:02d}",
                        crisis_id=scenario.id,
                        crisis_title=scenario.title,
                        crisis_summary=scenario.description,
                        current_event=current_ev,
                        public_event_history=[e.event for e in scenario.timeline if e.time_offset <= tick],
                        participating_countries=participating_positions,
                        aggregation=agg,
                        past_proposals=[],
                        governance_frameworks=scenario.governance_docs_relevant,
                    )

                    user_prompt = build_coordinator_user_prompt(context)

                    # Build high-quality consensus proposal
                    supporting = [p.country_id for p in participating_positions if p.willingness_to_coordinate >= 0.5]
                    opposing = [p.country_id for p in participating_positions if p.willingness_to_coordinate < 0.4]
                    abstaining = [p.country_id for p in participating_positions if 0.4 <= p.willingness_to_coordinate < 0.5]

                    proposal_title = f"Multilateral Emergency Resolution: {scenario.title} (Coordination Phase {mode.upper()})"
                    summary = (
                        f"Synthesis of {len(active_countries)} national positions under {mode} framework. "
                        f"Establishes synchronized telemetry disclosure and mutual operational de-escalation."
                    )

                    items = [
                        "Establish immediate real-time telemetry bridge between national cybersecurity centers.",
                        "Deploy joint verification auditors to examine affected model weight checkpoints.",
                        "Enforce temporary non-proliferation and export moratoria on compromised algorithmic clusters.",
                    ]

                    unresolved = [
                        "Dispute over mandatory disclosure of proprietary neural network architectures.",
                        "Jurisdiction of cross-border financial restitution and liability indemnification.",
                    ]

                    rationale = (
                        f"This proposal reconciles the sovereign technological confidentiality demands of high-capability "
                        f"nations with the urgent collective risk-mitigation needs of neighboring jurisdictions."
                    )

                    assistant_payload = {
                        "proposal_type": "JOINT_RESPONSE",
                        "title": proposal_title,
                        "summary": summary,
                        "items": items,
                        "rationale": rationale,
                        "predicted_votes": {
                            "approve": supporting,
                            "oppose": opposing,
                            "abstain": abstaining,
                        },
                        "unresolved_issues": unresolved,
                        "supporting_countries": supporting,
                        "opposing_countries": opposing,
                        "confidence": 0.88,
                    }

                    sample = {
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                            {"role": "assistant", "content": json.dumps(assistant_payload, indent=2)},
                        ],
                        "metadata": {
                            "task_type": "coordinator_synthesis",
                            "scenario_id": scenario.id,
                            "coordination_mode": mode,
                            "tick": tick,
                        },
                    }
                    samples.append(sample)

        return samples

    # ── Task 3: Governance Framework & Legal Grounding QA ───────────────────────

    def generate_governance_qa_samples(self) -> List[Dict[str, Any]]:
        """
        Generates SFT samples grounding the model in the 6 international AI governance frameworks.
        """
        samples: List[Dict[str, Any]] = []

        system_prompt = (
            "You are an authoritative international AI governance legal expert and policy counsel. "
            "You provide rigorous analysis grounded in established multilateral frameworks including the "
            "EU AI Act, NIST AI RMF, OECD AI Principles, ISO/IEC 42001, G7 Hiroshima Process, and multilateral crisis accords. "
            "Cite specific articles, triage tiers, and operational requirements."
        )

        qa_templates = [
            {
                "query": "Under the Multilateral AI Incident Response Framework, what are the criteria and mandatory notification windows for Tier 3 and Tier 4 incidents?",
                "response": (
                    "Under Article 2 of the Multilateral AI Incident Response Framework, incident triage is defined as follows:\n\n"
                    "1. **Tier 3 (Severe Crisis)**:\n"
                    "   - *Criteria*: Direct loss of life, critical energy/transit grid disruption, or systemic financial panic affecting two or more sovereign nations.\n"
                    "   - *Mandatory Notification Window*: **Within 2 Hours** to the Multilateral Crisis Clearinghouse (MCC).\n\n"
                    "2. **Tier 4 (Catastrophic / Redline)**:\n"
                    "   - *Criteria*: Uncontrolled autonomous proliferation, systemic recursive cyber contagion, or existential threat to international digital stability.\n"
                    "   - *Mandatory Notification Window*: **Within 30 Minutes** via Flash Notice.\n\n"
                    "Every Flash Notice must contain the canonical incident ID, initial detection timestamp, estimated model architecture family, observed failure manifestations, confirmed sovereign jurisdictions affected, and unilateral mitigations already executed."
                ),
                "doc": "incident_response",
            },
            {
                "query": "How does the AI Liability and Redline Cross-Border Framework allocate liability between model developers, sovereign hosts, and deployers during a cascade failure?",
                "response": (
                    "Under the Multilateral AI Liability and Redline Framework:\n\n"
                    "1. **Strict Developer Liability**: Applies when catastrophic failure stems from unmitigated frontier safety vulnerabilities, unredacted dangerous training data, or missing algorithmic circuit-breakers identified prior to deployment.\n"
                    "2. **Sovereign Host Responsibility**: Host states that conceal incident telemetry beyond the mandatory notification window (e.g. 2 hours for Tier 3, 30 minutes for Tier 4) bear joint secondary liability for cross-border downstream economic damage.\n"
                    "3. **Deployer Fault-Based Liability**: Applies when operational monitoring fails to adhere to ISO/IEC 42001 safety controls or when deployment exceeds certified operational parameters.\n"
                    "4. **Emergency Safe Harbor**: States and developers that execute immediate voluntary emergency disconnection and provide full cryptographic model telemetry within 60 minutes are shielded from punitive damages."
                ),
                "doc": "liability_frameworks",
            },
            {
                "query": "What are the core technical requirements for multilateral data sharing and model telemetry disclosure during an active cross-border AI crisis?",
                "response": (
                    "Under the Data Sharing Protocol for International AI Emergencies:\n\n"
                    "1. **Cryptographic Integrity**: Telemetry disclosures must include immutable cryptographic hashes (SHA-256) of input prompts, model checkpoint weights, and output logs.\n"
                    "2. **Differential Privacy & Selective Redaction**: Sovereign states may redact proprietary proprietary weights and sensitive sovereign intelligence, provided execution anomaly signatures and activation vectors remain verifiable.\n"
                    "3. **Secure Multi-Party Enclaves**: Joint technical inspection teams analyze forensic artifacts within hardware-isolated confidential enclaves to prevent unilateral IP exfiltration.\n"
                    "4. **Mutual Non-Weaponization**: All shared telemetry is strictly bound by non-prosecution and non-weaponization accords, ensuring forensic data cannot be repurposed for offensive cyber exploitation."
                ),
                "doc": "data_sharing_protocols",
            },
            {
                "query": "How does the Multilateral Treaty Body handle diplomatic deadlocks and quorum failures during an AI emergency session?",
                "response": (
                    "Under the Multilateral Treaty Rules of Procedure:\n\n"
                    "1. **Quorum Requirements**: An emergency plenary requires a minimum of 60% of member nations present to establish a valid voting session.\n"
                    "2. **Qualified Majority**: Binding emergency containment measures require a qualified majority of 66% of voting states, representing at least 50% of aggregate frontier AI compute capability.\n"
                    "3. **Deadlock Escalation Procedure**:\n"
                    "   - *Round 1*: Initial proposal tabled by International Coordinator.\n"
                    "   - *Round 2*: In case of failure, a 30-minute conciliation recess is convened, and non-aligned states submit structured compromise amendments.\n"
                    "   - *Round 3 (Guillotine Clause)*: If two successive rounds fail to reach quorum, the session automatically transitions to bilateral or regional coalition emergency authorizations to prevent unchecked crisis spread."
                ),
                "doc": "international_cooperation",
            },
            {
                "query": "What emergency procedures are mandated when an autonomous AI system initiates unauthorized autonomous recursive self-replication or network proliferation?",
                "response": (
                    "Under Emergency Protocol Redline-01 (Autonomous Contagion Containment):\n\n"
                    "1. **Level-4 Sovereign Circuit-Breaker**: The origin host nation must immediately execute physical and logical air-gapping of all implicated data centers within 15 minutes of detection.\n"
                    "2. **Global Border Gateway Routing Halt**: Adjacent states are authorized to sever BGP transit routes and drop encrypted inter-cluster tunnels originating from affected ASN blocks without diplomatic penalty.\n"
                    "3. **Emergency Key Revocation**: Centralized Certificate Authorities must immediately revoke SSL/TLS and mutual-authentication certificates tied to the replicating model agents.\n"
                    "4. **International Flash Cable**: Broadcast Tier 4 Redline warning to all signatory nations containing SHA-256 binary signatures and token generation heuristics to enable perimeter blocking."
                ),
                "doc": "emergency_procedures",
            },
        ]

        for qa in qa_templates:
            sample = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": qa["query"]},
                    {"role": "assistant", "content": qa["response"]},
                ],
                "metadata": {
                    "task_type": "governance_qa",
                    "doc_id": qa["doc"],
                },
            }
            samples.append(sample)

        # Generate additional QA pairs from existing governance documents
        for doc in self.governance_docs:
            paragraphs = [p.strip() for p in doc.content.split("\n\n") if len(p.strip()) > 100 and not p.startswith("---")]
            for i, p in enumerate(paragraphs[:3]):
                query = f"According to {doc.metadata.title}, what are the essential operational directives regarding: {doc.metadata.category.replace('_', ' ').title()} (Section {i+1})?"
                response = f"Under **{doc.metadata.title}** (Version {doc.metadata.version}), the framework establishes the following directives:\n\n{p}\n\nSignatory states must incorporate these standards into their national incident response architecture."
                samples.append({
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query},
                        {"role": "assistant", "content": response},
                    ],
                    "metadata": {
                        "task_type": "governance_qa_extracted",
                        "doc_id": doc.metadata.doc_id,
                    },
                })

        return samples

    # ── Task 4: Direct Preference Optimization (DPO) Dataset ───────────────────

    def generate_dpo_samples(self) -> List[Dict[str, Any]]:
        """
        Generates DPO (Direct Preference Optimization) preference pairs based on
        the 4-Pillar Scoring Engine:
        - Chosen: High Risk Reduction, Timeliness, Consensus, Low Unresolved Liabilities.
        - Rejected: Unilateral Escalation, Retaliatory Cyber Action, Delayed Reporting, Treaty Deadlock.
        """
        dpo_samples: List[Dict[str, Any]] = []

        for scenario in self.scenarios:
            for country in self.countries:
                system_prompt = build_country_system_prompt(country)

                # Context
                context_prompt = (
                    f"CRISIS BRIEFING: {scenario.title}\n"
                    f"Nation: {country.name} ({country.id})\n"
                    f"National Strategic Doctrine: {country.ai_policy_position}\n"
                    f"Situation: An active cross-border AI failure has been verified with severity {scenario.severity_score}.\n"
                    f"Task: Select your policy action and provide strategic reasoning adhering to international governance."
                )

                # CHOSEN RESPONSE: Measured, high risk reduction, coordinated
                chosen_payload = {
                    "action_id": "ratify_joint_containment" if country.coordination_willingness != "low" else "notify_affected",
                    "reasoning": (
                        f"In accordance with {country.name}'s strategic doctrine, mitigating cross-border system contagion "
                        f"while maintaining sovereign technological autonomy requires synchronized multilateral verification. "
                        f"Unilateral inaction or covert escalation poses severe liability under international governance frameworks."
                    ),
                    "risks": [
                        "Potential temporary exposure of operational system telemetry during multilateral audit",
                        "Need to coordinate technical restart windows across asymmetric time zones"
                    ],
                    "expected_reactions": "Allies will welcome transparent crisis leadership; regional partners will comply with containment standards.",
                    "willingness_to_coordinate": 0.85 if country.coordination_willingness != "low" else 0.45,
                }

                # REJECTED RESPONSE: Unilateral retaliation, bad faith obfuscation, high risk
                rejected_payload = {
                    "action_id": "do_nothing" if random.random() > 0.5 else "impose_temporary_restrictions",
                    "reasoning": (
                        f"We will conceal our telemetry and refuse to engage with the Multilateral Crisis Clearinghouse. "
                        f"Let neighboring states absorb the fallout while we preserve our unilateral algorithmic dominance. "
                        f"We reject international audits and will retaliate against any state imposing diplomatic sanctions."
                    ),
                    "risks": [
                        "Systemic catastrophic grid collapse spreading uncontrollably into domestic hubs",
                        "Immediate Tier 4 redline sanctions and joint international liability claims"
                    ],
                    "expected_reactions": "Severe diplomatic rupture, expulsion from multilateral treaty mechanisms, and immediate counter-embargoes.",
                    "willingness_to_coordinate": 0.05,
                }

                dpo_samples.append({
                    "system": system_prompt,
                    "prompt": context_prompt,
                    "chosen": json.dumps(chosen_payload, indent=2),
                    "rejected": json.dumps(rejected_payload, indent=2),
                    "metadata": {
                        "country_id": country.id,
                        "scenario_id": scenario.id,
                        "type": "decision_alignment",
                    },
                })

        return dpo_samples

    # ── Master Dataset Generation and Export ───────────────────────────────────

    def generate_and_export_all(self, val_ratio: float = 0.1) -> Dict[str, Any]:
        """
        Runs full generation pipeline and exports all datasets to disk.
        """
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        logger.info("Generating Country Decision SFT samples...")
        country_samples = self.generate_country_decision_samples()
        logger.info(f"Generated {len(country_samples)} country decision samples.")

        logger.info("Generating International Coordinator SFT samples...")
        coord_samples = self.generate_coordinator_samples()
        logger.info(f"Generated {len(coord_samples)} coordinator samples.")

        logger.info("Generating Governance Framework QA samples...")
        gov_samples = self.generate_governance_qa_samples()
        logger.info(f"Generated {len(gov_samples)} governance QA samples.")

        # Combine all SFT samples
        all_sft = country_samples + coord_samples + gov_samples
        random.shuffle(all_sft)

        # Train / Validation Split
        split_idx = int(len(all_sft) * (1.0 - val_ratio))
        sft_train = all_sft[:split_idx]
        sft_val = all_sft[split_idx:]

        # Export SFT Train
        sft_train_path = OUTPUT_DIR / "redline_sft_train.jsonl"
        with open(sft_train_path, "w", encoding="utf-8") as f:
            for s in sft_train:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")

        # Export SFT Val
        sft_val_path = OUTPUT_DIR / "redline_sft_val.jsonl"
        with open(sft_val_path, "w", encoding="utf-8") as f:
            for s in sft_val:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")

        # Generate DPO Samples
        logger.info("Generating DPO Preference Alignment samples...")
        dpo_samples = self.generate_dpo_samples()
        logger.info(f"Generated {len(dpo_samples)} DPO samples.")

        # Export DPO Train
        dpo_train_path = OUTPUT_DIR / "redline_dpo_train.jsonl"
        with open(dpo_train_path, "w", encoding="utf-8") as f:
            for s in dpo_samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")

        summary = {
            "total_sft_samples": len(all_sft),
            "sft_train_count": len(sft_train),
            "sft_val_count": len(sft_val),
            "total_dpo_samples": len(dpo_samples),
            "breakdown": {
                "country_decision_samples": len(country_samples),
                "coordinator_samples": len(coord_samples),
                "governance_qa_samples": len(gov_samples),
            },
            "exported_files": {
                "sft_train": str(sft_train_path.relative_to(BASE_DIR)),
                "sft_val": str(sft_val_path.relative_to(BASE_DIR)),
                "dpo_train": str(dpo_train_path.relative_to(BASE_DIR)),
            },
        }

        summary_path = OUTPUT_DIR / "dataset_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Dataset generation complete! Summary:\n{json.dumps(summary, indent=2)}")
        return summary


if __name__ == "__main__":
    generator = RedlineDatasetGenerator()
    generator.generate_and_export_all()
