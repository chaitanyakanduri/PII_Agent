from __future__ import annotations

import os
import json

# Force Presidio to use the correct spaCy config
os.environ["PRESIDIO_NLP_CONFIG"] = json.dumps({
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": os.getenv("SPACY_MODEL", "en_core_web_lg")}]
})

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

import yaml
from presidio_analyzer import AnalyzerEngine, RecognizerResult  # <-- add RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import SpacyNlpEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer.entities import OperatorConfig  # <-- add this import
from tools.logger import get_logger

logger = get_logger(__name__)

@dataclass
class EntityPolicy:
    name: str
    replace_with: str
    context_keywords: List[str]
    window: int

def _load_policy(path: str = "policies/redaction_policy.yaml") -> List[EntityPolicy]:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    entities = []
    for e in raw.get("entities", []):
        ctx = e.get("context", {})
        entities.append(EntityPolicy(
            name=e["name"],
            replace_with=e.get("replace_with", "[REDACTED]"),
            context_keywords=[k.lower() for k in ctx.get("only_if_near_any", [])],
            window=int(ctx.get("window", 0)),
        ))
    logger.info("Loaded %d entities from policy (Presidio)", len(entities))
    return entities

# filepath: c:\Users\SaiSakethCholleti\Downloads\pii_agent_presidio_azure_di\PII_Agent\tools\pii_detect.py
def _build_analyzer() -> AnalyzerEngine:
    model = os.getenv("SPACY_MODEL", "en_core_web_lg")
    logger.info("Initializing spaCy via NlpEngineProvider with model: %s", model)

    cfg = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "en", "model_name": model}],
    }
    logger.debug("NlpEngineProvider config: %s", cfg)  # Add this line

    nlp_engine = NlpEngineProvider(nlp_configuration=cfg).create_engine()

    return AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

def _build_anonymizer() -> AnonymizerEngine:
    return AnonymizerEngine()

_ANALYZER: Optional[AnalyzerEngine] = None
_ANONYMIZER: Optional[AnonymizerEngine] = None

def _get_analyzer() -> AnalyzerEngine:
    global _ANALYZER
    if _ANALYZER is None:
        _ANALYZER = _build_analyzer()
    return _ANALYZER

def _get_anonymizer() -> AnonymizerEngine:
    global _ANONYMIZER
    if _ANONYMIZER is None:
        _ANONYMIZER = _build_anonymizer()
    return _ANONYMIZER

def detect(text: str, policies: List[EntityPolicy]) -> List[Dict[str, Any]]:
    if not text:
        return []

    analyzer = _get_analyzer()
    target_entities = [p.name for p in policies]
    results = analyzer.analyze(text=text, entities=target_entities, language="en")

    pol_map: Dict[str, EntityPolicy] = {p.name: p for p in policies}
    filtered = []
    tlower = text.lower()

    for r in results:
        ent_type = r.entity_type
        pol = pol_map.get(ent_type)
        if not pol:
            continue

        if ent_type == "DATE_TIME" and pol.context_keywords:
            start = max(0, r.start - pol.window)
            end = min(len(text), r.end + pol.window)
            window_text = tlower[start:end]
            if not any(k in window_text for k in pol.context_keywords):
                continue

        snippet = text[max(0, r.start - 20): min(len(text), r.end + 20)]
        filtered.append({
            "entity": ent_type,
            "match": text[r.start:r.end],
            "span": {"start": r.start, "end": r.end},
            "score": r.score,
            "context": snippet
        })
    return filtered

def redact(text: str, policies: List[EntityPolicy], detections: List[Dict[str, Any]]) -> str:
    if not detections:
        return text
    anonymizer = _get_anonymizer()
    operators: Dict[str, OperatorConfig] = {}
    for p in policies:
        operators[p.name] = OperatorConfig("replace", {"new_value": p.replace_with})
    # Convert dicts to RecognizerResult objects
    entities = [
        RecognizerResult(
            entity_type=d["entity"],
            start=d["span"]["start"],
            end=d["span"]["end"],
            score=d.get("score", 1.0)
        )
        for d in detections
    ]
    res = anonymizer.anonymize(text=text, analyzer_results=entities, operators=operators)
    return res.text

def load_policy(path: str = "policies/redaction_policy.yaml") -> List[EntityPolicy]:
    return _load_policy(path)
