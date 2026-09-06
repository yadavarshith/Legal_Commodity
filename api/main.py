"""
APEX — LabelSure API entry point.

Minimal FastAPI app — no endpoints yet.  Exists to prove the
container builds and the schema imports work.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

# Prove that the frozen schemas are importable from the API layer.
from schemas import (
    Declaration,
    DeclarationType,
    Finding,
    FindingStatus,
    Inspection,
    InspectionStatus,
    RuleConfig,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks (placeholder)."""
    yield


app = FastAPI(
    title="APEX — LabelSure API",
    description=(
        "AI-assisted Legal Metrology (Packaged Commodities) "
        "compliance and inspection platform."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    """Liveness probe — returns 200 when the service is up."""
    return {
        "status": "ok",
        "service": "labelsure-api",
        "schemas_loaded": [
            "Declaration",
            "RuleConfig",
            "Finding",
            "Inspection",
        ],
    }
