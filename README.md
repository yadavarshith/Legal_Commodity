# APEX — LabelSure

**AI-assisted Legal Metrology (Packaged Commodities) compliance and inspection platform.**

> SIH26034 — Design law: *AI observes; rules decide; evidence explains; inspectors verify.*

## Repository layout

```
/api          FastAPI backend service
/app          Flutter inspector mobile app
/dashboard    React admin dashboard (placeholder)
/rules        Versioned JSON rule corpus
/schemas      Frozen contract schemas (Pydantic + JSON Schema)
```

## Quick start (Docker)

```bash
docker compose up --build
```

This starts:
- **PostgreSQL 16** on port 5432
- **FastAPI** on port 8000 (with live reload)

Health check: `curl http://localhost:8000/health`

## Schemas

Four frozen contracts under `/schemas`:

| Schema | File | Purpose |
|--------|------|---------|
| Declaration | `declaration.py` | One extracted label field |
| RuleConfig | `rule_config.py` | One versioned LM rule |
| Finding | `finding.py` | One rule evaluation + evidence |
| Inspection | `inspection.py` | Top-level inspection document |

JSON Schema exports live in `/schemas/json/` — regenerate with:

```bash
python -m schemas.export_jsonschema
```
