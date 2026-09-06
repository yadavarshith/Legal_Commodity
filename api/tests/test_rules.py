import json
import pytest
from schemas.rule_config import RuleConfig

def test_load_all_rules():
    with open('rules/seed_rules.json') as f:
        rules = json.load(f)

    assert len(rules) == 10
    for r_data in rules:
        r = RuleConfig(**r_data)
        assert r.rule_id.startswith("LM-")
