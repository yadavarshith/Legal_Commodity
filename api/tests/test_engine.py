from api.engine import RuleEngine
from schemas.inspection import ProductContext

def test_engine_eval():
    engine = RuleEngine(rules_dir="rules/")
    context = ProductContext(category="all")

    # Empty decls -> should fail critical rules
    findings = engine.evaluate([], context)
    assert any(f.status == "FAIL" for f in findings)

    # With decls -> should pass
    from schemas.declaration import Declaration, DeclarationType
    decls = [Declaration(type=DeclarationType.PRODUCT_NAME, raw_text="Test", image_id="IMG-01")]
    findings = engine.evaluate(decls, context)
    assert any(f.status == "PASS" for f in findings if f.rule_id == "LM-0001")
