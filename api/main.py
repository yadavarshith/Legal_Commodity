"""
APEX — LabelSure API entry point.

Minimal FastAPI app — no endpoints yet.  Exists to prove the
container builds and the schema imports work.
"""

from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Header, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import SessionLocal, get_db, init_db
from .models import InspectorDecision as DecisionModel
from .engine import RuleEngine
from .processing.extractor import extract_declarations
from schemas import (
    Declaration, DeclarationType, Finding, FindingStatus, Inspection, InspectionStatus, RuleConfig,
    InspectorDecisionRequest, ProductContext
)

API_KEY = "dev-key"

async def verify_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    try:
        init_db()
    except Exception as exc:
        import logging
        logging.getLogger("uvicorn.error").warning("init_db failed: %s", exc)
    yield


app = FastAPI(
    title="APEX — LabelSure API & Web Application",
    description=(
        "AI-assisted Legal Metrology (Packaged Commodities) "
        "compliance and inspection platform."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Ensure static & upload directories exist
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

uploads_dir = Path(__file__).parent.parent / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")


class AnalyzeRequest(BaseModel):
    ocr_results: List[Dict[str, Any]]
    category: str = "all"
    package_type: str = "pre-packaged"
    import_status: str = "domestic"
    image_id: str = "IMG-001"


@app.post("/upload-and-scan")
async def upload_and_scan_label(
    file: UploadFile = File(...),
    category: str = Form("all"),
    package_type: str = Form("pre-packaged"),
    import_status: str = Form("domestic")
):
    """
    Accept an uploaded package label image file, run OCR, extract Legal Metrology declarations,
    and evaluate compliance against Rule 6(1) of PCR 2011.
    """
    from .processing.ocr import extract_text

    # Save uploaded file
    file_ext = Path(file.filename).suffix or ".png"
    unique_name = f"label_{os.urandom(4).hex()}{file_ext}"
    save_path = uploads_dir / unique_name

    with open(save_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    image_url = f"/uploads/{unique_name}"

    # Run OCR on saved image
    ocr_results = extract_text(str(save_path))
    image_id = f"IMG-{unique_name[:8]}"

    # Extract Declarations
    declarations = extract_declarations(ocr_results, image_id)

    # Build Context
    context = ProductContext(
        category=category,
        package_type=package_type,
        import_status=import_status
    )

    # Run Rule Engine
    rules_dir = Path(__file__).parent.parent / "rules"
    engine = RuleEngine(rules_dir=str(rules_dir))
    findings = engine.evaluate(declarations, context)

    has_fail = any(f.status == FindingStatus.FAIL for f in findings)
    overall_status = InspectionStatus.REVIEW if has_fail else InspectionStatus.PASS

    return {
        "inspection_id": f"INS-{os.urandom(3).hex().upper()}",
        "image_url": image_url,
        "filename": file.filename,
        "context": context.model_dump(),
        "ocr_results": ocr_results,
        "declarations": [d.model_dump() for d in declarations],
        "findings": [f.model_dump() for f in findings],
        "overall_status": overall_status.value
    }


@app.get("/")
async def serve_web_app():
    """Serves the APEX — LabelSure Web Application UI."""
    index_path = Path(__file__).parent.parent / "static" / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {
        "message": "APEX — LabelSure API is running. Web UI loading..."
    }


@app.get("/rules")
async def get_rules():
    """Return legal metrology seed rules."""
    rules_path = Path(__file__).parent.parent / "rules" / "seed_rules.json"
    if rules_path.exists():
        with open(rules_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


@app.post("/analyze")
async def analyze_package(req: AnalyzeRequest):
    """Run OCR extraction and Legal Metrology rule engine on label OCR items."""
    declarations = extract_declarations(req.ocr_results, req.image_id)
    context = ProductContext(
        category=req.category,
        package_type=req.package_type,
        import_status=req.import_status
    )
    
    # Initialize rule engine with rules directory
    rules_dir = Path(__file__).parent.parent / "rules"
    engine = RuleEngine(rules_dir=str(rules_dir))
    findings = engine.evaluate(declarations, context)

    # Determine overall status
    has_fail = any(f.status == FindingStatus.FAIL for f in findings)
    overall_status = InspectionStatus.REVIEW if has_fail else InspectionStatus.PASS

    return {
        "inspection_id": f"INS-{os.urandom(3).hex().upper()}",
        "image_id": req.image_id,
        "context": context.model_dump(),
        "declarations": [d.model_dump() for d in declarations],
        "findings": [f.model_dump() for f in findings],
        "overall_status": overall_status.value
    }


@app.get("/stats")
async def get_stats():
    """Return dashboard analytics and compliance summary."""
    return {
        "total_inspections": 142,
        "compliance_rate": "84.5%",
        "flagged_cases": 22,
        "pending_reviews": 5,
        "category_breakdown": {
            "food": 65,
            "cosmetics": 34,
            "electronics": 23,
            "household": 20
        },
        "top_failing_rules": [
            {"rule_id": "LM-0002", "name": "Manufacturer Name/Address", "count": 14},
            {"rule_id": "LM-0005", "name": "Mfg/Pack Date", "count": 9},
            {"rule_id": "LM-0007", "name": "Consumer Care Info", "count": 7},
            {"rule_id": "LM-0008", "name": "Country of Origin", "count": 4}
        ]
    }


@app.post("/inspections/{inspection_id}/review")
async def review_finding(inspection_id: str, req: InspectorDecisionRequest, db: Session = Depends(get_db)):
    db_decision = DecisionModel(
        inspection_id=inspection_id,
        finding_id=req.finding_id,
        decision=req.decision,
        reason=req.reason
    )
    db.add(db_decision)
    db.commit()
    return {"status": "recorded"}


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


@app.post("/inspections", response_model=Inspection, dependencies=[Depends(verify_key)])
async def create_inspection():
    """Stub POST /inspections endpoint with mocked response."""
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

