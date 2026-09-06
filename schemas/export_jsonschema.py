"""
Export all four frozen schemas as JSON Schema files.

Run once to generate /schemas/json/*.schema.json files that
can be used by non-Python consumers (Flutter, React, tests).

Usage:
    python -m schemas.export_jsonschema
"""

import json
from pathlib import Path

from schemas.declaration import Declaration
from schemas.finding import Finding
from schemas.inspection import Inspection
from schemas.rule_config import RuleConfig

OUTPUT_DIR = Path(__file__).parent / "json"


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    models = {
        "declaration": Declaration,
        "rule_config": RuleConfig,
        "finding": Finding,
        "inspection": Inspection,
    }

    for name, model in models.items():
        schema = model.model_json_schema()
        out_path = OUTPUT_DIR / f"{name}.schema.json"
        out_path.write_text(json.dumps(schema, indent=2) + "\n")
        print(f"  OK {out_path}")

    print(f"Exported {len(models)} JSON Schema files to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
