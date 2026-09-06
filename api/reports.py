"""Report generation module."""
from fpdf import FPDF
from schemas.inspection import Inspection

class InspectionReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "APEX — LabelSure Inspection Report", border=True, ln=True, align="C")

    def generate(self, inspection: Inspection):
        self.add_page()
        self.set_font("Arial", "", 10)
        self.cell(0, 10, f"Inspection ID: {inspection.inspection_id}", ln=True)
        self.cell(0, 10, f"Status: {inspection.overall_status}", ln=True)
        self.ln(5)
        self.cell(0, 10, "Findings:", ln=True)
        for f in inspection.findings:
            self.cell(0, 10, f"- {f.rule_id} ({f.status}): {f.description}", ln=True)

        return self.output()
