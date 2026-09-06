"""
APEX — LabelSure Rule Engine.
"""

import json
from pathlib import Path
from typing import List
from schemas.rule_config import RuleConfig
from schemas.declaration import Declaration, DeclarationType
from schemas.finding import Finding, FindingStatus, EvidenceItem
from schemas.inspection import ProductContext

class RuleEngine:
    def __init__(self, rules_dir: str = "rules/"):
        self.rules = self._load_rules(rules_dir)

    def _load_rules(self, rules_dir: str) -> List[RuleConfig]:
        rules = []
        for f in Path(rules_dir).glob("*.json"):
            with open(f) as data:
                data = json.load(data)
                if isinstance(data, list):
                    rules.extend([RuleConfig(**r) for r in data])
                else:
                    rules.append(RuleConfig(**data))
        return rules

    def _is_applicable(self, rule: RuleConfig, context: ProductContext) -> bool:
        """Context-aware rule selection."""
        if rule.applicability.category == "all": return True
        return rule.applicability.category == context.category

    def evaluate(self, declarations: List[Declaration], context: ProductContext) -> List[Finding]:
        findings = []
        # Map declaration types
        declaration_map = {d.type.value: d for d in declarations}

        for rule in self.rules:
            if not self._is_applicable(rule, context):
                continue

            # Basic presence evaluation
            field = rule.validation.parameters.get("field")
            if field and field not in declaration_map:
                findings.append(Finding(
                    finding_id=f"F-{rule.rule_id.split('-')[1]}",
                    rule_id=rule.rule_id,
                    status=FindingStatus.FAIL,
                    description=rule.requirement,
                    confidence=0.9
                ))
            else:
                findings.append(Finding(
                    finding_id=f"F-{rule.rule_id.split('-')[1]}",
                    rule_id=rule.rule_id,
                    status=FindingStatus.PASS,
                    description=f"Rule met: {rule.requirement}",
                    confidence=1.0
                ))
        return findings
