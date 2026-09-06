# APEX — LabelSure: Rule Corpus

This directory holds the versioned JSON rule definitions used by
the rule engine.  Each rule conforms to the `RuleConfig` schema
in `/schemas/rule_config.py`.

## Files

- `seed_rules.json` — Initial set of Legal Metrology (Packaged
  Commodities) Rules, 2011 baseline rules.

Rules are designed to be **hot-reloadable**: the engine reads this
directory at startup and can refresh without restarting the service.
