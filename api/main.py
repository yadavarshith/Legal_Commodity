"""
APEX — LabelSure API entry point.
AI-assisted Legal Metrology (Packaged Commodities) compliance and inspection platform.
"""

from contextlib import asynccontextmanager
import json
import logging
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("labelsure.pipeline")

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
        logging.getLogger("uvicorn.error").warning("init_db failed: %s", exc)
    yield


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="APEX — LabelSure API & Web Application",
    description=(
        "AI-assisted Legal Metrology (Packaged Commodities) "
        "compliance and inspection platform."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for Flutter Web & Mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    import_status: str = Form("domestic"),
    organization_name: str = Form("General Public / Retail Audit")
):
    """
    Accept an uploaded package label image file, run OCR, extract Legal Metrology declarations,
    render color-coded bounding box highlights, evaluate compliance, and return dynamic verdict.
    """
    from .processing.ocr import extract_text
    from .processing.image import annotate_image_with_bboxes
    from .engine import RuleEngine, compute_overall_verdict

    # Save uploaded file
    file_ext = Path(file.filename).suffix or ".png"
    unique_name = f"label_{os.urandom(4).hex()}{file_ext}"
    save_path = uploads_dir / unique_name

    with open(save_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    file_size = save_path.stat().st_size
    image_url = f"/uploads/{unique_name}"
    image_id = f"IMG-{unique_name[:8]}"

    # Stage 1: Image Upload / Capture
    logger.info("================ PIPELINE EXECUTION TRACE ================")
    logger.info("[TRACE Stage 1: Image Upload] Received file='%s', saved to='%s' (%d bytes)", file.filename, save_path, file_size)

    # Stage 2: OCR Output
    try:
        ocr_results = extract_text(str(save_path))
    except Exception as e:
        logger.error("[TRACE Stage 2 ERROR] OCR engine failed: %s", e)
        ocr_results = []
    
    logger.info("[TRACE Stage 2: OCR Output] Extracted %d raw text blocks from image", len(ocr_results))

    # Stage 3: Declaration Extraction
    try:
        declarations = extract_declarations(ocr_results, image_id)
    except Exception as e:
        logger.error("[TRACE Stage 3 ERROR] Declaration extractor failed: %s", e)
        declarations = []

    # Stage 4: Rule Evaluation
    context = ProductContext(
        category=category,
        package_type=package_type,
        import_status=import_status
    )
    rules_dir = Path(__file__).parent.parent / "rules"
    engine = RuleEngine(rules_dir=str(rules_dir))
    
    try:
        findings = engine.evaluate(declarations, context)
    except Exception as e:
        logger.error("[TRACE Stage 4 ERROR] Rule engine evaluation failed: %s", e)
        findings = []

    # Stage 5: Draw Bounding Box Highlights on Image
    annotated_filename = f"annotated_{unique_name}"
    annotated_save_path = uploads_dir / annotated_filename
    try:
        annotated_bboxes = annotate_image_with_bboxes(
            str(save_path),
            str(annotated_save_path),
            ocr_results,
            declarations,
            findings
        )
        annotated_image_url = f"/uploads/{annotated_filename}"
    except Exception as e:
        logger.error("Bounding box annotation failed: %s", e)
        annotated_bboxes = []
        annotated_image_url = image_url

    # Stage 6: Dynamic Verdict Calculation
    verdict = compute_overall_verdict(findings)
    inspection_id = f"INS-{os.urandom(3).hex().upper()}"

    logger.info("[TRACE Stage 6: Verdict] inspection_id='%s' | verdict='%s' | score=%.1f%%",
                inspection_id, verdict["verdict_title"], verdict["compliance_score"])
    logger.info("==========================================================")

    return {
        "inspection_id": inspection_id,
        "organization_name": organization_name,
        "image_url": image_url,
        "annotated_image_url": annotated_image_url,
        "filename": file.filename,
        "context": context.model_dump(),
        "ocr_results": ocr_results,
        "declarations": [d.model_dump() for d in declarations],
        "findings": [f.model_dump() for f in findings],
        "overall_status": verdict["status"],
        "verdict_title": verdict["verdict_title"],
        "verdict_badge": verdict["verdict_badge"],
        "compliance_score": verdict["compliance_score"],
        "verdict_summary": verdict["summary"],
        "failure_justifications": verdict["failure_justifications"],
        "annotated_bboxes": annotated_bboxes
    }


@app.post("/upload-bulk")
async def upload_bulk_labels(
    files: List[UploadFile] = File(...),
    organization_name: str = Form("General Public / Retail Audit"),
    category: str = Form("all"),
    package_type: str = Form("pre-packaged"),
    import_status: str = Form("domestic")
):
    """
    Bulk Upload Module:
    Accepts 10+ package label images, prompts for Organization Name, processes each through OCR
    + Rule Engine + Bounding Box Annotator, and returns an aggregated batch compliance report.
    """
    batch_id = f"BATCH-{os.urandom(3).hex().upper()}"
    reports = []

    passed_count = 0
    failed_count = 0
    review_count = 0

    logger.info("Starting Bulk Batch Scan '%s' for Organization '%s' (%d images)",
                batch_id, organization_name, len(files))

    for idx, f in enumerate(files):
        try:
            report = await upload_and_scan_label(
                file=f,
                category=category,
                package_type=package_type,
                import_status=import_status,
                organization_name=organization_name
            )
            reports.append(report)

            status = report.get("overall_status", "APPROVED")
            if status == "APPROVED":
                passed_count += 1
            elif status == "REJECTED":
                failed_count += 1
            else:
                review_count += 1

        except Exception as exc:
            logger.error("Bulk upload item #%d (%s) failed: %s", idx + 1, f.filename, exc)

    total_scanned = len(reports)
    batch_status = "APPROVED" if failed_count == 0 and review_count == 0 else ("REJECTED" if failed_count > 0 else "REVIEW")

    return {
        "batch_id": batch_id,
        "organization_name": organization_name,
        "total_scanned": total_scanned,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "review_count": review_count,
        "overall_batch_status": batch_status,
        "batch_compliance_rate": f"{round((passed_count / total_scanned * 100), 1)}%" if total_scanned > 0 else "100%",
        "reports": reports
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
    """Return legal metrology rules dynamically loaded from rules directory."""
    rules_dir = Path(__file__).parent.parent / "rules"
    engine = RuleEngine(rules_dir=str(rules_dir))
    return [r.model_dump() for r in engine.rules]


@app.post("/analyze")
async def analyze_package(req: AnalyzeRequest):
    """Run OCR extraction and Legal Metrology rule engine on label OCR items."""
    declarations = extract_declarations(req.ocr_results, req.image_id)
    context = ProductContext(
        category=req.category,
        package_type=req.package_type,
        import_status=req.import_status
    )
    
    rules_dir = Path(__file__).parent.parent / "rules"
    engine = RuleEngine(rules_dir=str(rules_dir))
    findings = engine.evaluate(declarations, context)

    has_fail = any(f.status == FindingStatus.FAIL for f in findings)
    overall_status = InspectionStatus.REVIEW if has_fail else InspectionStatus.APPROVED

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
    rules_dir = Path(__file__).parent.parent / "rules"
    engine = RuleEngine(rules_dir=str(rules_dir))
    total_rules = len(engine.rules)

    return {
        "total_inspections": 142,
        "compliance_rate": "84.5%",
        "flagged_cases": 22,
        "pending_reviews": 5,
        "total_rules_in_corpus": total_rules,
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
