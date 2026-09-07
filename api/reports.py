"""
APEX — LabelSure PDF Report Generator Module.
Renders comprehensive, court-admissible Legal Metrology compliance reports with:
- Organization & Inspection Metadata
- Dynamic Product Verdict Banner (GOOD PRODUCT vs BAD PRODUCT)
- Guideline Failure Justifications Section
- Mandatory Declarations & Findings Tables
"""

import os
from fpdf import FPDF
from typing import Dict, Any, List


class LegalMetrologyPdfReport(FPDF):
    def __init__(self, organization_name: str = "General Public / Retail Audit"):
        super().__init__()
        self.organization_name = organization_name

    def header(self):
        self.set_font("Arial", "B", 12)
        self.set_fill_color(22, 30, 46)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, "  LEGAL METROLOGY PACKAGED COMMODITIES COMPLIANCE REPORT", ln=True, align="L", fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()} | Official Legal Metrology Enforcement Record | {self.organization_name}", align="C")

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
        annotated_path = report_data.get("annotated_image_path", "")

        # -------------------------------------------------------------
        # 1. Organization & Metadata Header
        # -------------------------------------------------------------
        self.set_font("Arial", "B", 10)
        self.cell(40, 7, "Organization:", border=0)
        self.set_font("Arial", "", 10)
        self.cell(60, 7, str(org_name), border=0)

        self.set_font("Arial", "B", 10)
        self.cell(40, 7, "Inspection ID:", border=0)
        self.set_font("Arial", "", 10)
        self.cell(50, 7, str(inspection_id), border=0, ln=True)

        self.set_font("Arial", "B", 10)
        self.cell(40, 7, "Product Image:", border=0)
        self.set_font("Arial", "", 10)
        self.cell(60, 7, str(filename), border=0)

        self.set_font("Arial", "B", 10)
        self.cell(40, 7, "Compliance Score:", border=0)
        self.set_font("Arial", "B", 10)
        self.cell(50, 7, f"{score:.1f}%", border=0, ln=True)

        self.ln(4)

        # -------------------------------------------------------------
        # 2. Dynamic Product Verdict Banner
        # -------------------------------------------------------------
        if overall_status == "APPROVED" or "GOOD" in verdict_title.upper():
            self.set_fill_color(220, 245, 230)
            self.set_text_color(0, 120, 50)
            status_label = "🟢 PRODUCT VERDICT: GOOD PRODUCT (COMPLIANT)"
        elif overall_status == "REJECTED" or "BAD" in verdict_title.upper():
            self.set_fill_color(255, 225, 225)
            self.set_text_color(180, 20, 20)
            status_label = "🔴 PRODUCT VERDICT: BAD PRODUCT (NON-COMPLIANT)"
        else:
            self.set_fill_color(255, 245, 210)
            self.set_text_color(160, 100, 0)
            status_label = "🟡 PRODUCT VERDICT: NEEDS ENFORCEMENT REVIEW"

        self.set_font("Arial", "B", 12)
        self.cell(0, 12, f"  {status_label}", ln=True, fill=True)
        self.set_text_color(0, 0, 0)
        self.set_font("Arial", "", 9)
        self.multi_cell(0, 6, f"Summary: {summary}")
        self.ln(6)

        # -------------------------------------------------------------
        # 3. Guideline Failure Justifications Section
        # -------------------------------------------------------------
        self.set_font("Arial", "B", 11)
        self.cell(0, 8, "Legal Metrology Guideline Failure Justifications", ln=True)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

        if not justifications:
            self.set_font("Arial", "I", 9)
            self.cell(0, 6, "No guideline violations detected. Package is fully compliant with PCR 2011.", ln=True)
        else:
            for j in justifications:
                r_id = j.get("rule_id", "")
                desc = j.get("description", "")
                self.set_font("Arial", "B", 9)
                self.set_text_color(180, 20, 20)
                self.cell(0, 6, f"• [{r_id} Failure Justification]:", ln=True)
                self.set_font("Arial", "", 9)
                self.set_text_color(40, 40, 40)
                self.multi_cell(0, 5, f"  {desc}")
                self.ln(2)

        self.set_text_color(0, 0, 0)
        self.ln(6)

        # -------------------------------------------------------------
        # 4. Mandatory Statutory Declarations Table
        # -------------------------------------------------------------
        self.set_font("Arial", "B", 11)
        self.cell(0, 8, "Extracted Statutory Declarations", ln=True)
        
        self.set_font("Arial", "B", 8)
        self.set_fill_color(240, 240, 240)
        self.cell(45, 6, "Declaration Field", border=1, fill=True)
        self.cell(95, 6, "Normalized Value / Extracted Text", border=1, fill=True)
        self.cell(25, 6, "Confidence", border=1, fill=True)
        self.cell(25, 6, "Status", border=1, fill=True, ln=True)

        declarations = report_data.get("declarations", [])
        self.set_font("Arial", "", 8)
        for d in declarations:
            f_type = d.get("type", d.get("field_type", "FIELD"))
            val = d.get("normalized_value", d.get("raw_text", ""))
            conf = d.get("confidence", 0.9)
            st = "PASS" if val else "MISSING"

            self.cell(45, 6, str(f_type)[:24], border=1)
            self.cell(95, 6, str(val)[:58], border=1)
            self.cell(25, 6, f"{int(conf*100)}%", border=1)
            self.cell(25, 6, st, border=1, ln=True)

        self.ln(6)

        # -------------------------------------------------------------
        # 5. Embedded Annotated Image (if exists)
        # -------------------------------------------------------------
        if annotated_path and os.path.isfile(annotated_path):
            try:
                self.add_page()
                self.set_font("Arial", "B", 11)
                self.cell(0, 8, "Annotated Package Label Image (Bounding Box Highlights)", ln=True)
                self.ln(4)
                self.image(annotated_path, x=15, w=180)
            except Exception:
                pass

        self.output(output_path)
        return output_path
