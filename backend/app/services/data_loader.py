"""
Data Loader Service for AI Governance Crisis Simulator.

Authoritative loading, validation, and retrieval interface for:
- 15 Fictional Countries (JSON)
- 3 Crisis Scenarios (YAML)
- 6 Governance Knowledge Documents (Markdown with frontmatter)
"""
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from app.schemas.data_models import (
    CountryData,
    GovernanceDocument,
    GovernanceDocumentMetadata,
    ScenarioData,
)

logger = logging.getLogger(__name__)

# Base directory for static data files
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


class DataLoader:
    """
    Service for loading and validating data files from disk.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DEFAULT_DATA_DIR
        self.countries_dir = self.data_dir / "countries"
        self.scenarios_dir = self.data_dir / "scenarios"
        self.governance_dir = self.data_dir / "governance"

    # ── Country Loaders ───────────────────────────────────────────────────────

    def load_all_countries(self) -> List[CountryData]:
        """
        Loads and validates all country profile JSON files.
        Returns a list of CountryData sorted by country id.
        """
        if not self.countries_dir.exists():
            raise FileNotFoundError(f"Countries directory not found: {self.countries_dir}")

        countries: List[CountryData] = []
        for file_path in sorted(self.countries_dir.glob("country_*.json")):
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            country = CountryData.model_validate(raw_data)
            countries.append(country)

        if not countries:
            raise FileNotFoundError(f"No country JSON files found in {self.countries_dir}")

        return countries

    def load_country(self, country_id: str) -> CountryData:
        """
        Retrieves a single country profile by its ID (e.g. 'country_01').
        Raises KeyError if the country is not found.
        """
        # Normalize input (strip whitespace, lower)
        cid = country_id.strip().lower()
        if not cid.startswith("country_") and cid.isdigit():
            cid = f"country_{int(cid):02d}"

        target_file = self.countries_dir / f"{cid}.json"
        if not target_file.exists():
            # Search by ID inside files in case file name doesn't match
            for file_path in self.countries_dir.glob("*.json"):
                if file_path.name == "index.json":
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    if raw.get("id") == cid or raw.get("country_id") == cid:
                        return CountryData.model_validate(raw)
                except Exception:
                    continue
            raise KeyError(f"Country with ID '{country_id}' not found in {self.countries_dir}")

        with open(target_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        return CountryData.model_validate(raw_data)

    # ── Scenario Loaders ──────────────────────────────────────────────────────

    def load_all_scenarios(self) -> List[ScenarioData]:
        """
        Loads and validates all crisis scenario YAML files.
        Returns a list of ScenarioData sorted by scenario id.
        """
        if not self.scenarios_dir.exists():
            raise FileNotFoundError(f"Scenarios directory not found: {self.scenarios_dir}")

        scenarios: List[ScenarioData] = []
        for file_path in sorted(self.scenarios_dir.glob("scenario_*.yaml")):
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)
            scenario = ScenarioData.model_validate(raw_data)
            scenarios.append(scenario)

        if not scenarios:
            raise FileNotFoundError(f"No scenario YAML files found in {self.scenarios_dir}")

        return scenarios

    def load_scenario(self, scenario_id: str) -> ScenarioData:
        """
        Retrieves a single crisis scenario by ID (e.g. 'scenario_01' or 'crisis_001').
        Raises KeyError if not found.
        """
        sid = scenario_id.strip().lower()

        # Try direct file match
        target_file = self.scenarios_dir / f"{sid}.yaml"
        if target_file.exists():
            with open(target_file, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f)
            return ScenarioData.model_validate(raw)

        # Search all YAML files for matching id or scenario_id
        for file_path in self.scenarios_dir.glob("*.yaml"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f)
                if raw.get("id") == sid or raw.get("scenario_id") == sid:
                    return ScenarioData.model_validate(raw)
            except Exception:
                continue

        raise KeyError(f"Scenario with ID '{scenario_id}' not found in {self.scenarios_dir}")

    # ── Governance Document Loaders ───────────────────────────────────────────

    def load_governance_documents(self) -> List[GovernanceDocument]:
        """
        Loads and parses all 6 governance knowledge documents from markdown files.
        Extracts YAML frontmatter metadata and markdown sections.
        """
        if not self.governance_dir.exists():
            raise FileNotFoundError(f"Governance directory not found: {self.governance_dir}")

        documents: List[GovernanceDocument] = []
        for file_path in sorted(self.governance_dir.glob("*.md")):
            doc = self._parse_governance_markdown(file_path)
            documents.append(doc)

        if not documents:
            raise FileNotFoundError(f"No governance markdown files found in {self.governance_dir}")

        return documents

    def load_governance_document(self, doc_id: str) -> GovernanceDocument:
        """
        Retrieves a single governance document by doc_id (e.g. 'ai_principles').
        Raises KeyError if not found.
        """
        did = doc_id.strip().lower()
        if did.endswith(".md"):
            did = did[:-3]

        target_file = self.governance_dir / f"{did}.md"
        if target_file.exists():
            return self._parse_governance_markdown(target_file)

        # Search all documents for matching doc_id in frontmatter
        for file_path in self.governance_dir.glob("*.md"):
            try:
                doc = self._parse_governance_markdown(file_path)
                if doc.metadata.doc_id == did:
                    return doc
            except Exception:
                continue

        raise KeyError(f"Governance document with ID '{doc_id}' not found in {self.governance_dir}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _parse_governance_markdown(self, file_path: Path) -> GovernanceDocument:
        """
        Extracts YAML frontmatter and body from a Markdown document.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw_text, re.DOTALL)
        if not frontmatter_match:
            # Fallback if no frontmatter
            stem = file_path.stem
            metadata = GovernanceDocumentMetadata(
                doc_id=stem,
                title=stem.replace("_", " ").title(),
                category="principles",
                relevance_tags=[],
            )
            body = raw_text
        else:
            fm_text, body = frontmatter_match.groups()
            fm_data = yaml.safe_load(fm_text) or {}
            metadata = GovernanceDocumentMetadata.model_validate(fm_data)

        # Parse top-level sections by header
        sections: Dict[str, str] = {}
        current_section = "Introduction"
        current_lines: List[str] = []

        for line in body.splitlines():
            if line.startswith("#"):
                if current_lines:
                    sections[current_section] = "\n".join(current_lines).strip()
                    current_lines = []
                current_section = line.lstrip("#").strip()
            else:
                current_lines.append(line)
        if current_lines:
            sections[current_section] = "\n".join(current_lines).strip()

        return GovernanceDocument(
            metadata=metadata,
            content=body.strip(),
            sections=sections,
        )


# Global default instance
default_data_loader = DataLoader()


# Convenience functional accessors
def load_all_countries() -> List[CountryData]:
    return default_data_loader.load_all_countries()


def load_country(country_id: str) -> CountryData:
    return default_data_loader.load_country(country_id)


def load_all_scenarios() -> List[ScenarioData]:
    return default_data_loader.load_all_scenarios()


def load_scenario(scenario_id: str) -> ScenarioData:
    return default_data_loader.load_scenario(scenario_id)


def load_governance_documents() -> List[GovernanceDocument]:
    return default_data_loader.load_governance_documents()


def load_governance_document(doc_id: str) -> GovernanceDocument:
    return default_data_loader.load_governance_document(doc_id)
