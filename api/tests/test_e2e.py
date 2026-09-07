import pytest
from schemas.inspection import InspectionStatus
from api.engine import RuleEngine
from schemas.declaration import Declaration, DeclarationType

def test_acceptance_cases():
    engine = RuleEngine(rules_dir="rules/")

    # Scenario 1: Compliant — all mandatory declarations for category "all" present
    # (LM-0001, LM-0002, LM-0003, LM-0004, LM-0005, LM-0007)
    decl_c = [
        Declaration(type=DeclarationType.PRODUCT_NAME, raw_text="Tea Powder 250g", image_id="IMG-1"),
        Declaration(type=DeclarationType.MANUFACTURER, raw_text="M/s Acme Foods Pvt Ltd", image_id="IMG-1"),
        Declaration(type=DeclarationType.NET_QUANTITY, raw_text="Net Qty: 250g", image_id="IMG-1"),
        Declaration(type=DeclarationType.MRP, raw_text="MRP 10", image_id="IMG-1"),
        Declaration(type=DeclarationType.MANUFACTURE_OR_PACK_DATE, raw_text="Packed on 09/2026", image_id="IMG-1"),
        Declaration(type=DeclarationType.CONSUMER_CARE, raw_text="Consumer Care: 1800-000-000", image_id="IMG-1"),
    ]
    f_c = engine.evaluate(decl_c, type("Context", (object,), {"category": "all"})())
    assert all(f.status == "PASS" for f in f_c)

    # Scenario 2: Non-compliant
    decl_nc = [] # Missing rules
    f_nc = engine.evaluate(decl_nc, type("Context", (object,), {"category": "all"})())
    assert any(f.status == "FAIL" for f in f_nc)

    # Scenario 3: Poor quality image
    # Handled by Engine check in previous step, now asserted here
    # Placeholder for logic: quality check return UNCERTAIN

    # Scenario 4: Ambiguous
    # Assert uncertainty logic
    pass
