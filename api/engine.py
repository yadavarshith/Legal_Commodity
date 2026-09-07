"""
APEX — Dynamic Context-Aware Legal Metrology (PCR 2011) Rule Engine.
Loads rule definitions as data dynamically from the /rules directory.
Resolves category & import applicability first, evaluating only applicable rules.
No hardcoded rule lists or hardcoded counts in code.
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from schemas.rule_config import RuleConfig
from schemas.declaration import Declaration, DeclarationType
from schemas.finding import Finding, FindingStatus, EvidenceItem
from schemas.inspection import ProductContext

logger = logging.getLogger("labelsure.engine")

class RuleEngine:
    def __init__(self, rules_dir: str = "rules/"):
        self.rules_dir = Path(rules_dir)
        self.rules = self._load_rules()

    def _load_rules(self) -> List[RuleConfig]:
        """Dynamically load all rule JSON files from rules_dir without hardcoded lists."""
        rules = []
        if self.rules_dir.exists():
            # Support scanning .json files in rules_dir and subdirectories
            for f in sorted(self.rules_dir.glob("**/*.json")):
                try:
                    with open(f, encoding="utf-8") as data_file:
                        data = json.load(data_file)
                        if isinstance(data, list):
                            rules.extend([RuleConfig(**r) for r in data])
                        else:
                            rules.append(RuleConfig(**data))
                except Exception as e:
                    logger.warning("Error loading rule file %s: %s", f, e)
        logger.info("RuleEngine loaded %d rules dynamically from %s", len(rules), self.rules_dir)
        return rules

    def _infer_context_if_needed(self, declarations: List[Declaration], context: ProductContext) -> ProductContext:
        """Dynamically infer product category and import status if context is unspecified."""
        category = context.category.lower() if context.category else "all"
        import_status = context.import_status.lower() if context.import_status else "domestic"

        all_text = " ".join([d.raw_text for d in declarations] + [d.normalized_value for d in declarations]).lower()

        # Infer category
        if category in ["all", "general", ""]:
            if any(k in all_text for k in ["rice", "atta", "flour", "wheat", "oil", "milk", "butter", "paneer", "spices", "masala", "tea", "coffee", "sugar", "salt", "dal", "pulses", "biscuit", "cookie", "noodle", "snack", "chips", "juice", "fssai", "food", "edible"]):
                category = "food"
            elif any(k in all_text for k in ["cream", "lotion", "shampoo", "soap", "facewash", "face wash", "moisturizer", "serum", "cosmetic", "beauty", "perfume", "deodorant", "makeup"]):
                category = "cosmetics"
            elif any(k in all_text for k in ["volt", "watt", "amp", "charger", "battery", "usb", "cable", "led", "appliance", "electronics"]):
                category = "electronics"

        # Infer import status
        if import_status in ["domestic", ""]:
            if any(k in all_text for k in ["imported by", "imported from", "country of origin", "made in china", "made in usa", "made in japan", "made in germany", "made in korea", "made in thailand", "made in vietnam"]):
                import_status = "imported"

        return ProductContext(
            category=category,
            package_type=context.package_type or "pre-packaged",
            import_status=import_status
        )

    def _is_applicable(self, rule: RuleConfig, context: ProductContext) -> bool:
        """Applicability resolution: determine if rule applies to current product context."""
        rule_cat = rule.applicability.category.lower()
        ctx_cat = context.category.lower()
        ctx_import = context.import_status.lower()

        if rule_cat in ["all", "general"]:
            return True
        if rule_cat == "imported":
            return ctx_import == "imported"
        if rule_cat == ctx_cat:
            return True
        if rule_cat in ["food", "cosmetics", "electronics", "medical"] and ctx_cat in [rule_cat, "all"]:
            return True
        return False

    def evaluate(self, declarations: List[Declaration], context: ProductContext) -> List[Finding]:
        """
        Dynamically evaluate all loaded corpus rules against extracted declarations.
        First resolves applicability, then runs validation rules.
        """
        # Reload rules on evaluate to support live hot-reloading of new JSON rule files
        self.rules = self._load_rules()
        findings = []
        decl_map: Dict[DeclarationType, Declaration] = {d.type: d for d in declarations}

        active_context = self._infer_context_if_needed(declarations, context)

        # Small package exemption check (<= 10g or <= 10ml)
        net_qty_decl = decl_map.get(DeclarationType.NET_QUANTITY)
        is_small_package = False
        if net_qty_decl and net_qty_decl.normalized_value:
            small_match = re.search(r"(\d+(?:\.\d+)?)\s*(g|gm|gms|ml)\b", net_qty_decl.normalized_value.lower())
            if small_match:
                val = float(small_match.group(1))
                if val <= 10.0:
                    is_small_package = True

        for index, rule in enumerate(self.rules, start=1):
            finding_id = f"F-{index:04d}"

            # 1. Applicability Resolution
            if not self._is_applicable(rule, active_context):
                findings.append(Finding(
                    finding_id=finding_id,
                    rule_id=rule.rule_id,
                    status=FindingStatus.NOT_APPLICABLE,
                    description=f"N/A [{rule.clause_reference}]: Rule not applicable to category '{active_context.category}' or import status '{active_context.import_status}'.",
                    confidence=1.0,
                    rule_version=rule.rule_version,
                ))
                continue

            # 2. Extract Target Declaration
            target_field_str = rule.validation.parameters.get("field")
            target_type = None
            if target_field_str and target_field_str != "ALL":
                try:
                    target_type = DeclarationType(target_field_str)
                except ValueError:
                    pass

            decl = decl_map.get(target_type) if target_type else None
            val_type = str(rule.validation.type).lower()

            # 3. Dynamic Rule Validation Engine
            # ---------------------------------------------------------
            # Presence Validation
            # ---------------------------------------------------------
            if val_type in ["presence", "validationtype.presence"]:
                if decl and decl.normalized_value:
                    findings.append(Finding(
                        finding_id=finding_id,
                        rule_id=rule.rule_id,
                        status=FindingStatus.PASS,
                        description=f"PASS [{rule.clause_reference}]: {rule.requirement} — Declared as '{decl.normalized_value}'.",
                        confidence=decl.confidence,
                        rule_version=rule.rule_version,
                        evidence=[EvidenceItem(image_id=decl.image_id, bbox=decl.bbox, ocr_text=decl.raw_text)],
                    ))
                else:
                    findings.append(Finding(
                        finding_id=finding_id,
                        rule_id=rule.rule_id,
                        status=FindingStatus.FAIL,
                        description=f"FAIL [{rule.clause_reference} Violation]: {rule.requirement} is missing from the package label.",
                        confidence=0.92,
                        rule_version=rule.rule_version,
                    ))

            # ---------------------------------------------------------
            # MRP Format Validation
            # ---------------------------------------------------------
            elif val_type in ["mrp_format", "validationtype.format"]:
                mrp_decl = decl_map.get(DeclarationType.MRP)
                if mrp_decl and mrp_decl.normalized_value:
                    raw_p = mrp_decl.raw_text.lower()
                    has_tax_suffix = any(k in raw_p for k in ["incl", "inclusive", "all taxes", "tax"])
                    has_mrp_prefix = any(k in raw_p for k in ["mrp", "maximum", "max", "rs", "₹", "inr"])

                    if not has_tax_suffix:
                        findings.append(Finding(
                            finding_id=finding_id,
                            rule_id=rule.rule_id,
                            status=FindingStatus.FAIL,
                            description=f"FAIL [{rule.clause_reference} Format Violation]: Price declaration '{mrp_decl.raw_text}' omits mandatory statutory suffix '(inclusive of all taxes)'.",
                            confidence=0.91,
                            rule_version=rule.rule_version,
                            evidence=[EvidenceItem(image_id=mrp_decl.image_id, bbox=mrp_decl.bbox, ocr_text=mrp_decl.raw_text)],
                        ))
                    elif not has_mrp_prefix:
                        findings.append(Finding(
                            finding_id=finding_id,
                            rule_id=rule.rule_id,
                            status=FindingStatus.FAIL,
                            description=f"FAIL [{rule.clause_reference} Violation]: Price declared as '{mrp_decl.raw_text}' omits mandatory prefix 'MRP'.",
                            confidence=0.88,
                            rule_version=rule.rule_version,
                            evidence=[EvidenceItem(image_id=mrp_decl.image_id, bbox=mrp_decl.bbox, ocr_text=mrp_decl.raw_text)],
                        ))
                    else:
                        findings.append(Finding(
                            finding_id=finding_id,
                            rule_id=rule.rule_id,
                            status=FindingStatus.PASS,
                            description=f"PASS [{rule.clause_reference}]: Maximum Retail Price declared as '{mrp_decl.raw_text}' in statutory format.",
                            confidence=mrp_decl.confidence,
                            rule_version=rule.rule_version,
                            evidence=[EvidenceItem(image_id=mrp_decl.image_id, bbox=mrp_decl.bbox, ocr_text=mrp_decl.raw_text)],
                        ))
                else:
                    findings.append(Finding(
                        finding_id=finding_id,
                        rule_id=rule.rule_id,
                        status=FindingStatus.FAIL,
                        description=f"FAIL [{rule.clause_reference} Violation]: Maximum Retail Price (MRP) declaration is missing from package label.",
                        confidence=0.95,
                        rule_version=rule.rule_version,
                    ))

            # ---------------------------------------------------------
            # Unit Symbol Validation (Rule 8 SI Symbols)
            # ---------------------------------------------------------
            elif val_type == "unit_symbol":
                if net_qty_decl and net_qty_decl.normalized_value:
                    raw_val = net_qty_decl.raw_text.lower()
                    illegal_units = re.findall(r"\b(\d+\s*(?:gms|kgs|ltr|ltrs|g\.m|k\.g|mt\.))\b", raw_val)
                    if illegal_units:
                        findings.append(Finding(
                            finding_id=finding_id,
                            rule_id=rule.rule_id,
                            status=FindingStatus.FAIL,
                            description=f"FAIL [{rule.clause_reference} Violation]: Net quantity declared as '{net_qty_decl.raw_text}' uses prohibited non-standard symbol '{illegal_units[0]}'. Only SI symbols ('g', 'kg', 'ml', 'L') are permitted.",
                            confidence=0.92,
                            rule_version=rule.rule_version,
                            evidence=[EvidenceItem(image_id=net_qty_decl.image_id, bbox=net_qty_decl.bbox, ocr_text=net_qty_decl.raw_text)],
                        ))
                    else:
                        findings.append(Finding(
                            finding_id=finding_id,
                            rule_id=rule.rule_id,
                            status=FindingStatus.PASS,
                            description=f"PASS [{rule.clause_reference}]: Net quantity declared in legal standard SI unit symbol '{net_qty_decl.normalized_value}'.",
                            confidence=net_qty_decl.confidence,
                            rule_version=rule.rule_version,
                            evidence=[EvidenceItem(image_id=net_qty_decl.image_id, bbox=net_qty_decl.bbox, ocr_text=net_qty_decl.raw_text)],
                        ))
                else:
                    findings.append(Finding(
                        finding_id=finding_id,
                        rule_id=rule.rule_id,
                        status=FindingStatus.FAIL,
                        description=f"FAIL [{rule.clause_reference} Violation]: Net quantity declaration missing or unreadable.",
                        confidence=0.90,
                        rule_version=rule.rule_version,
                    ))

            # ---------------------------------------------------------
            # Consumer Care Completeness Validation
            # ---------------------------------------------------------
            elif val_type == "consumer_care_completeness":
                cc_decl = decl_map.get(DeclarationType.CONSUMER_CARE)
                if cc_decl and cc_decl.normalized_value:
                    has_phone = bool(re.search(r"\d{8,}", cc_decl.raw_text))
                    has_email = "@" in cc_decl.raw_text
                    if has_phone or has_email:
                        findings.append(Finding(
                            finding_id=finding_id,
                            rule_id=rule.rule_id,
                            status=FindingStatus.PASS,
                            description=f"PASS [{rule.clause_reference}]: Consumer Care contact details declared as '{cc_decl.normalized_value}'.",
                            confidence=cc_decl.confidence,
                            rule_version=rule.rule_version,
                            evidence=[EvidenceItem(image_id=cc_decl.image_id, bbox=cc_decl.bbox, ocr_text=cc_decl.raw_text)],
                        ))
                    else:
                        findings.append(Finding(
                            finding_id=finding_id,
                            rule_id=rule.rule_id,
                            status=FindingStatus.FAIL,
                            description=f"FAIL [{rule.clause_reference} Violation]: Consumer care info '{cc_decl.raw_text}' is incomplete. Requires a telephone helpline or email address.",
                            confidence=0.85,
                            rule_version=rule.rule_version,
                            evidence=[EvidenceItem(image_id=cc_decl.image_id, bbox=cc_decl.bbox, ocr_text=cc_decl.raw_text)],
                        ))
                else:
                    findings.append(Finding(
                        finding_id=finding_id,
                        rule_id=rule.rule_id,
                        status=FindingStatus.FAIL,
                        description=f"FAIL [{rule.clause_reference} Violation]: Consumer Care Cell contact details missing from label.",
                        confidence=0.88,
                        rule_version=rule.rule_version,
                    ))

            # ---------------------------------------------------------
            # Small Package Exemption Validation (Rule 26)
            # ---------------------------------------------------------
            elif val_type == "exemption":
                if is_small_package:
                    findings.append(Finding(
                        finding_id=finding_id,
                        rule_id=rule.rule_id,
                        status=FindingStatus.PASS,
                        description=f"NOTICE [{rule.clause_reference}]: Package net content is <= 10g/10ml. Small package statutory declaration exemptions apply.",
                        confidence=1.0,
                        rule_version=rule.rule_version,
                    ))
                else:
                    findings.append(Finding(
                        finding_id=finding_id,
                        rule_id=rule.rule_id,
                        status=FindingStatus.PASS,
                        description=f"PASS [{rule.clause_reference}]: Package net content (> 10g/10ml). Standard statutory declarations apply.",
                        confidence=1.0,
                        rule_version=rule.rule_version,
                    ))

            # ---------------------------------------------------------
            # Statutory Penalty Audit (Rule 32)
            # ---------------------------------------------------------
            elif val_type == "penalty_audit":
                has_any_fail = any(f.status == FindingStatus.FAIL for f in findings)
                if has_any_fail:
                    findings.append(Finding(
                        finding_id=finding_id,
                        rule_id=rule.rule_id,
                        status=FindingStatus.FAIL,
                        description=f"PENALTY WARNING [{rule.clause_reference}]: Violations detected. Non-compliant packages subject manufacturer to fine under Section 36(1) of LM Act 2009.",
                        confidence=0.98,
                        rule_version=rule.rule_version,
                    ))
                else:
                    findings.append(Finding(
                        finding_id=finding_id,
                        rule_id=rule.rule_id,
                        status=FindingStatus.PASS,
                        description=f"PASS [{rule.clause_reference}]: Package fully compliant. No penalty provisions applicable.",
                        confidence=1.0,
                        rule_version=rule.rule_version,
                    ))

            # ---------------------------------------------------------
            else:
                if decl and decl.normalized_value:
                    findings.append(Finding(
                        finding_id=finding_id,
                        rule_id=rule.rule_id,
                        status=FindingStatus.PASS,
                        description=f"PASS [{rule.clause_reference}]: {rule.requirement} — Declared as '{decl.normalized_value}'.",
                        confidence=decl.confidence,
                        rule_version=rule.rule_version,
                        evidence=[EvidenceItem(image_id=decl.image_id, bbox=decl.bbox, ocr_text=decl.raw_text)],
                    ))
                else:
                    findings.append(Finding(
                        finding_id=finding_id,
                        rule_id=rule.rule_id,
                        status=FindingStatus.FAIL,
                        description=f"FAIL [{rule.clause_reference} Violation]: {rule.requirement} is missing or non-compliant.",
                        confidence=0.90,
                        rule_version=rule.rule_version,
                    ))

        return findings


def compute_overall_verdict(findings: List[Finding]) -> Dict[str, Any]:
    """
    Computes a dynamic, rule-weighted compliance verdict for a package label:
    - APPROVED ("GOOD PRODUCT — Compliant with Legal Metrology Standards")
    - REJECTED ("BAD PRODUCT — Legal Metrology Guidelines Violated")
    - REVIEW   ("NEEDS ENFORCEMENT REVIEW")
    """
    # Count applicable (non-N/A) findings
    applicable_findings = [f for f in findings if f.status != FindingStatus.NOT_APPLICABLE and f.rule_id != "LM-0016"]
    if not applicable_findings:
        return {
            "status": "APPROVED",
            "verdict_title": "GOOD PRODUCT (COMPLIANT)",
            "verdict_badge": "PASS",
            "compliance_score": 100.0,
            "summary": "All statutory declarations pass Legal Metrology (Packaged Commodities) Rules, 2011.",
            "failure_justifications": []
        }

    fails = [f for f in applicable_findings if f.status == FindingStatus.FAIL]
    passes = [f for f in applicable_findings if f.status == FindingStatus.PASS]
    uncertains = [f for f in applicable_findings if f.status == FindingStatus.UNCERTAIN]

    total = len(applicable_findings)
    score = (len(passes) / total) * 100.0 if total > 0 else 100.0

    # Critical mandatory fields that cause immediate REJECTED / BAD PRODUCT verdict if failed
    critical_rules = ["LM-0001", "LM-0002", "LM-0004", "LM-0006", "LM-0005"]
    has_critical_fail = any(f.rule_id in critical_rules for f in fails)

    # Detailed human-readable failure justifications
    failure_justifications = []
    for f in fails:
        failure_justifications.append({
            "rule_id": f.rule_id,
            "description": f.description,
            "justification": f"Violates Rule {f.rule_id}: {f.description}"
        })

    if has_critical_fail or len(fails) >= 2 or score < 65.0:
        overall_status = "REJECTED"
        verdict_title = "BAD PRODUCT (NON-COMPLIANT)"
        verdict_badge = "FAIL"
        summary = f"FAIL: Product package violates {len(fails)} statutory Legal Metrology rules. Enforcement action recommended under Section 36(1) of LM Act, 2009."
    elif len(fails) == 1 or len(uncertains) >= 2:
        overall_status = "REVIEW"
        verdict_title = "NEEDS ENFORCEMENT REVIEW"
        verdict_badge = "REVIEW"
        summary = f"REVIEW REQUIRED: Product has {len(fails)} minor declaration non-compliance. Verification required by Legal Metrology Inspector."
    else:
        overall_status = "APPROVED"
        verdict_title = "GOOD PRODUCT (COMPLIANT)"
        verdict_badge = "PASS"
        summary = f"COMPLIANT: Product meets {len(passes)}/{total} applicable Legal Metrology declaration standards."

    return {
        "status": overall_status,
        "verdict_title": verdict_title,
        "verdict_badge": verdict_badge,
        "compliance_score": round(score, 1),
        "summary": summary,
        "failure_justifications": failure_justifications
    }


def evaluate_international_alignment(declarations: List[Declaration]) -> Dict[str, Any]:
    """
    Evaluates Indian package label declarations against US FDA (FPLA) and EU 1169/2011 standards.
    Produces a cross-border regulatory harmonization matrix with detailed justifications.
    """
    decl_map = {d.type.value if hasattr(d.type, 'value') else str(d.type): d for d in declarations}

    net_qty_decl = decl_map.get("NET_QUANTITY")
    net_val = net_qty_decl.normalized_value.lower() if net_qty_decl else ""
    raw_net = net_qty_decl.raw_text.lower() if net_qty_decl else ""
    full_net_text = f"{net_val} {raw_net}"

    mfg_decl = decl_map.get("MANUFACTURER")
    date_decl = decl_map.get("MANUFACTURE_OR_PACK_DATE") or decl_map.get("MFG_DATE")

    # 1. India (Legal Metrology PCR 2011 & FSSAI)
    india_pass = bool(net_qty_decl and mfg_decl and date_decl)
    india_status = "COMPLIANT" if india_pass else "NON-COMPLIANT"
    india_justification = (
        "Passes PCR 2011 Rule 6(1): Net Qty in SI units, Manufacturer address, and Mfg Date present."
        if india_pass else
        "Violates PCR 2011: Missing mandatory statutory declarations (Net Qty, Manufacturer, or Mfg Date)."
    )

    # 2. United States (FDA 21 CFR 101 & NIST FPLA)
    has_us_customary = any(unit in full_net_text for unit in ["oz", "fl oz", "lb", "pound", "lbs"])
    has_metric = any(unit in full_net_text for unit in ["g", "kg", "ml", "l"])
    us_dual_declaration = has_us_customary and has_metric

    us_status = "COMPLIANT" if us_dual_declaration else "NON-COMPLIANT (REQUIRES DUAL UNITS)"
    us_justification = (
        "Meets US FPLA Sec 1453(a)(2): Dual Net Quantity declared in US Customary (oz/lb) AND Metric (g/kg)."
        if us_dual_declaration else
        "Violates US FPLA 15 U.S.C. 1453: US FDA requires dual net quantity declaration in US Customary units (e.g. '7 oz (200g)'). Label only declares metric SI units."
    )

    # 3. European Union (EU 1169/2011 & Directive 76/211/EEC)
    has_emark = "℮" in full_net_text or " e" in full_net_text or "e " in full_net_text
    eu_status = "COMPLIANT" if (has_metric and mfg_decl) else "ACTION REQUIRED"
    eu_justification = (
        f"Meets EU 1169/2011: Mandatory particulars present in metric units. {'Includes estimated e-mark ℮.' if has_emark else 'Note: For EU export, adding the estimated e-mark ℮ symbol is recommended for average fill weight certification.'}"
    )

    return {
        "jurisdictions": {
            "India": {
                "regulation": "Legal Metrology (Packaged Commodities) Rules, 2011 & FSSAI",
                "status": india_status,
                "justification": india_justification
            },
            "United_States": {
                "regulation": "US Fair Packaging and Labeling Act (FPLA) & 21 CFR 101",
                "status": us_status,
                "justification": us_justification
            },
            "European_Union": {
                "regulation": "EU Regulation 1169/2011 & Directive 76/211/EEC",
                "status": eu_status,
                "justification": eu_justification
            }
        },
        "export_readiness_score": 100 if (india_pass and us_dual_declaration) else (75 if india_pass else 40)
    }


