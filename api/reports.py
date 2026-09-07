"""
APEX — LabelSure PDF Report Generator Module.
Renders comprehensive, court-admissible Legal Metrology compliance reports with:
- Organization & Inspection Metadata
- Dynamic Product Verdict Banner (GOOD PRODUCT vs BAD PRODUCT)
- Guideline Failure Justifications Section
- International Regulatory Comparison (India vs US FDA vs EU 1169/2011)
- Single Consolidated Bulk Batch PDF Report Generator
"""

import os
from fpdf import FPDF
from typing import Dict, Any, List


class LegalMetrologyPdfReport(FPDF):
    def __init__(self, organization_name: str = "General Public / Retail Audit"):
        super().__init__()
        self.organization_name = organization_name

    def header(self):
        self.set_font("Arial", "B", 11)
        self.set_fill_color(22, 30, 46)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "  LEGAL METROLOGY & INTERNATIONAL COMPLIANCE AUDIT REPORT", ln=True, align="L", fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()} | Official Enforcement Record | {self.organization_name}", align="C")

    def _render_international_comparison(self, report_data: Dict[str, Any]):
        """Render International Cross-Border Regulatory Comparison (India vs US vs EU)."""
        intl = report_data.get("international_alignment", {})
        jurisdictions = intl.get("jurisdictions", {})
        if not jurisdictions:
            return

        self.set_font("Arial", "B", 11)
        self.cell(0, 8, "Cross-Border Regulatory Alignment (India vs US FDA vs EU 1169/2011)", ln=True)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

        self.set_font("Arial", "B", 8)
        self.set_fill_color(230, 238, 248)
        self.cell(35, 6, "Jurisdiction", border=1, fill=True)
        self.cell(75, 6, "Regulatory Standard", border=1, fill=True)
        self.cell(30, 6, "Status", border=1, fill=True)
        self.cell(50, 6, "Export Alignment Notes", border=1, fill=True, ln=True)

        self.set_font("Arial", "", 8)
        for country, data in jurisdictions.items():
            reg = data.get("regulation", "")
            st = data.get("status", "")
            just = data.get("justification", "")

            c_name = country.replace("_", " ")
            self.cell(35, 8, str(c_name), border=1)
            self.cell(75, 8, str(reg)[:45], border=1)
            self.cell(30, 8, str(st)[:18], border=1)
            self.cell(50, 8, str(just)[:30], border=1, ln=True)

        self.ln(4)

    def generate_pdf(self, report_data: Dict[str, Any], output_path: str):
        self.add_page()

        inspection_id = report_data.get("inspection_id", "INS-000")
        org_name = report_data.get("organization_name", self.organization_name)
        verdict_title = report_data.get("verdict_title", "PRODUCT VERDICT: UNDER REVIEW")
        overall_status = report_data.get("overall_status", "REVIEW")
        score = report_data.get("compliance_score", 0.0)
        summary = report_data.get("verdict_summary", "")
        filename = report_data.get("filename", "label.png")
        justifications = report_data.get("failure_justifications", [])

        # Metadata Header
        self.set_font("Arial", "B", 10)
        self.cell(35, 6, "Organization:", border=0)
        self.set_font("Arial", "", 10)
        self.cell(65, 6, str(org_name), border=0)

        self.set_font("Arial", "B", 10)
        self.cell(35, 6, "Inspection ID:", border=0)
        self.set_font("Arial", "", 10)
        self.cell(55, 6, str(inspection_id), border=0, ln=True)

        self.set_font("Arial", "B", 10)
        self.cell(35, 6, "Product Image:", border=0)
        self.set_font("Arial", "", 10)
        self.cell(65, 6, str(filename), border=0)

        self.set_font("Arial", "B", 10)
        self.cell(35, 6, "Compliance Score:", border=0)
        self.set_font("Arial", "B", 10)
        self.cell(55, 6, f"{score:.1f}%", border=0, ln=True)
        self.ln(4)

        # Dynamic Verdict Banner
        if overall_status == "APPROVED" or "GOOD" in verdict_title.upper():
            self.set_fill_color(220, 245, 230)
            self.set_text_color(0, 120, 50)
            status_label = "[PASS] PRODUCT VERDICT: GOOD PRODUCT (COMPLIANT)"
        elif overall_status == "REJECTED" or "BAD" in verdict_title.upper():
            self.set_fill_color(255, 225, 225)
            self.set_text_color(180, 20, 20)
            status_label = "[FAIL] PRODUCT VERDICT: BAD PRODUCT (NON-COMPLIANT)"
        else:
            self.set_fill_color(255, 245, 210)
            self.set_text_color(160, 100, 0)
            status_label = "[REVIEW] PRODUCT VERDICT: NEEDS ENFORCEMENT REVIEW"

        self.set_font("Arial", "B", 11)
        self.cell(0, 10, f"  {status_label}", ln=True, fill=True)
        self.set_text_color(0, 0, 0)
        self.set_font("Arial", "", 9)
        self.multi_cell(0, 5, f"Summary: {summary}")
        self.ln(4)

        # Failure Justifications
        self.set_font("Arial", "B", 10)
        self.cell(0, 6, "Legal Metrology Failure Justifications", ln=True)
        if not justifications:
            self.set_font("Arial", "I", 9)
            self.cell(0, 5, "No statutory violations. Package is fully compliant with PCR 2011.", ln=True)
        else:
            for j in justifications:
                self.set_font("Arial", "B", 8)
                self.set_text_color(180, 20, 20)
                self.cell(0, 5, f"- [{j.get('rule_id', '')} Violation]:", ln=True)
                self.set_font("Arial", "", 8)
                self.set_text_color(40, 40, 40)
                self.multi_cell(0, 4, f"  {j.get('description', '')}")
        self.set_text_color(0, 0, 0)
        self.ln(4)

        # International Comparison Matrix
        self._render_international_comparison(report_data)

        # Output
        self.output(output_path)
        return output_path


def generate_bulk_batch_pdf(batch_data: Dict[str, Any], output_path: str) -> str:
    """
    Generates ONE single consolidated PDF report for an entire bulk batch scan (10+ images).
    Includes Executive Summary, Batch Metrics Table, Cross-Border Regulatory Alignment,
    and individual product label breakdowns.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    batch_id = batch_data.get("batch_id", "BATCH-000")
    org_name = batch_data.get("organization_name", "General Public / Retail Audit")
    total_scanned = batch_data.get("total_scanned", 0)
    passed_count = batch_data.get("passed_count", 0)
    failed_count = batch_data.get("failed_count", 0)
    review_count = batch_data.get("review_count", 0)
    rate = batch_data.get("batch_compliance_rate", "0%")
    batch_status = batch_data.get("overall_batch_status", "APPROVED")
    reports = batch_data.get("reports", [])

    # Header Banner
    pdf.set_font("Arial", "B", 14)
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 14, "  CONSOLIDATED ENTERPRISE BULK AUDIT REPORT", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # Organization & Batch Executive Summary
    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 6, "Organization:", border=0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 6, str(org_name), border=0)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 6, "Batch ID:", border=0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(50, 6, str(batch_id), border=0, ln=True)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 6, "Total Scanned:", border=0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 6, f"{total_scanned} Product Labels", border=0)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 6, "Batch Compliance Rate:", border=0)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(50, 6, str(rate), border=0, ln=True)
    pdf.ln(6)

    # Batch Verdict Status Box
    if batch_status == "APPROVED":
        pdf.set_fill_color(220, 245, 230)
        pdf.set_text_color(0, 120, 50)
        batch_verdict = "[PASS] BATCH AUDIT STATUS: COMPLIANT (ALL PRODUCTS PASSED)"
    else:
        pdf.set_fill_color(255, 225, 225)
        pdf.set_text_color(180, 20, 20)
        batch_verdict = f"[FAIL] BATCH AUDIT STATUS: VIOLATIONS DETECTED ({failed_count} FAILED / {total_scanned} SCANNED)"

    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, f"  {batch_verdict}", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # Summary Metrics Table
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Aggregated Batch Audit Summary Table", ln=True)
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(15, 6, "#", border=1, fill=True)
    pdf.cell(65, 6, "Product Label File", border=1, fill=True)
    pdf.cell(45, 6, "Overall Verdict", border=1, fill=True)
    pdf.cell(25, 6, "Score", border=1, fill=True)
    pdf.cell(40, 6, "Key Failure Justification", border=1, fill=True, ln=True)

    pdf.set_font("Arial", "", 8)
    for idx, r in enumerate(reports):
        fn = r.get("filename", f"Item_{idx+1}.png")
        v_title = r.get("verdict_title", r.get("overall_status", "REVIEW"))
        score = r.get("compliance_score", 0.0)
        justs = r.get("failure_justifications", [])
        just_str = f"{justs[0].get('rule_id', '')}: {justs[0].get('description', '')}" if justs else "Pass"

        pdf.cell(15, 6, f"#{idx+1}", border=1)
        pdf.cell(65, 6, str(fn)[:38], border=1)
        pdf.cell(45, 6, str(v_title)[:26], border=1)
        pdf.cell(25, 6, f"{score:.1f}%", border=1)
        pdf.cell(40, 6, str(just_str)[:24], border=1, ln=True)

    pdf.ln(8)

    # Individual Product Breakdown Pages
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Detailed Individual Product Label Breakdown", ln=True)
    pdf.ln(4)

    for idx, r in enumerate(reports):
        fn = r.get("filename", f"Item_{idx+1}.png")
        v_title = r.get("verdict_title", r.get("overall_status", "REVIEW"))
        justs = r.get("failure_justifications", [])

        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 6, f"Product #{idx+1}: {fn} - [{v_title}]", ln=True)
        pdf.set_font("Arial", "", 9)

        if justs:
            pdf.set_text_color(180, 20, 20)
            for j in justs:
                pdf.multi_cell(0, 4, f"  - {j.get('rule_id', '')}: {j.get('description', '')}")
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.cell(0, 5, "  - All statutory declarations pass PCR 2011 rules.", ln=True)

        pdf.ln(4)

    pdf.output(output_path)
    return output_path
