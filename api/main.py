"""
APEX — LabelSure API entry point.

Minimal FastAPI app — no endpoints yet.  Exists to prove the
container builds and the schema imports work.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, status, Depends
from schemas import (
    Declaration,
    DeclarationType,
    Finding,
    FindingStatus,
    Inspection,
    InspectionStatus,
    RuleConfig,
)

# Temporary simple auth
API_KEY = "dev-key"

async def verify_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
    return True

@app.post("/inspections", response_model=Inspection, dependencies=[Depends(verify_key)])
async def create_inspection():
    """Stub POST /inspections endpoint with mocked response."""
    # Build a mocked Inspection
    inspection = Inspection(
        inspection_id="INS-002",
        images=[{"id": "IMG-01", "path": "local/path/front.jpg", "panel": "front", "quality": "pass"}],
        overall_status=InspectionStatus.REVIEW,
        findings=[
            Finding(
                finding_id="F-0001",
                rule_id="LM-0001",
                status=FindingStatus.FAIL,
                description="Mocked: Product name not detected in OCR.",
                confidence=0.85
            )
        ]
    )
    return inspection


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
