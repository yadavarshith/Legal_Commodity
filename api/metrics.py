from sqlalchemy.orm import Session
from models import InspectorDecision, InspectionCase
import json

def calculate_metrics(db: Session):
    # Override rate: Inspector decision (overridden) / Total decisions
    overrides = db.query(InspectorDecision).filter(InspectorDecision.decision == "overridden").count()
    total = db.query(InspectorDecision).count()

    return {
        "inspector_override_rate": float(overrides) / total if total > 0 else 0,
        "total_cases_processed": db.query(InspectionCase).count(),
        "notes": "Prototypes status. Metrics based on manual inspector input."
    }
