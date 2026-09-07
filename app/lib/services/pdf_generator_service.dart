import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import '../models/inspection_model.dart';

class PdfGeneratorService {
  /// Generates and triggers cross-platform PDF export/download (Web, Mobile, Desktop)
  static Future<void> exportCompliancePdf(InspectionReport report, {String organizationName = "General Public / Retail Audit"}) async {
    final pdf = pw.Document();

    final isGoodProduct = report.overallStatus == 'APPROVED' || report.overallStatus == 'PASS';
    final isBadProduct = report.overallStatus == 'REJECTED' || report.overallStatus == 'FAIL';

    final verdictColor = isGoodProduct
        ? PdfColors.green700
        : (isBadProduct ? PdfColors.red700 : PdfColors.orange700);

    final verdictBg = isGoodProduct
        ? PdfColors.green50
        : (isBadProduct ? PdfColors.red50 : PdfColors.orange50);

    final verdictText = isGoodProduct
        ? "🟢 PRODUCT VERDICT: GOOD PRODUCT (COMPLIANT)"
        : (isBadProduct ? "🔴 PRODUCT VERDICT: BAD PRODUCT (NON-COMPLIANT)" : "🟡 PRODUCT VERDICT: NEEDS ENFORCEMENT REVIEW");

    // Filter failing rules for explicit failure justifications
    final failingFindings = report.findings.where((f) => f.status == 'FAIL').toList();

    pdf.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(24),
        build: (pw.Context context) {
          return pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              // Header Banner
              pw.Container(
                padding: const pw.EdgeInsets.all(12),
                decoration: const pw.BoxDecoration(color: PdfColors.blueGrey900),
                child: pw.Row(
                  mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                  children: [
                    pw.Column(
                      crossAxisAlignment: pw.CrossAxisAlignment.start,
                      children: [
                        pw.Text(
                          "LEGAL METROLOGY COMPLIANCE INSPECTION REPORT",
                          style: pw.TextStyle(
                            color: PdfColors.white,
                            fontSize: 13,
                            fontWeight: pw.FontWeight.bold,
                          ),
                        ),
                        pw.Text(
                          "Under Legal Metrology (Packaged Commodities) Rules, 2011",
                          style: const pw.TextStyle(color: PdfColors.cyan200, fontSize: 9),
                        ),
                      ],
                    ),
                    pw.Text(
                      organizationName,
                      style: pw.TextStyle(
                        color: PdfColors.amber200,
                        fontSize: 10,
                        fontWeight: pw.FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              pw.SizedBox(height: 12),

              // Metadata Table
              pw.Container(
                padding: const pw.EdgeInsets.all(10),
                decoration: pw.BoxDecoration(
                  border: pw.Border.all(color: PdfColors.grey300),
                  color: PdfColors.grey50,
                ),
                child: pw.Column(
                  children: [
                    pw.Row(
                      mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                      children: [
                        pw.Text("Inspection Case ID: ${report.inspectionId}", style: pw.TextStyle(fontWeight: pw.FontWeight.bold)),
                        pw.Text("Date: ${report.timestamp.toString().substring(0, 16)}"),
                      ],
                    ),
                    pw.SizedBox(height: 4),
                    pw.Row(
                      mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                      children: [
                        pw.Text("Organization: $organizationName"),
                        pw.Text("Compliance Score: ${report.complianceScore.round()}%", style: pw.TextStyle(fontWeight: pw.FontWeight.bold, color: verdictColor)),
                      ],
                    ),
                  ],
                ),
              ),
              pw.SizedBox(height: 12),

              // Product Verdict Banner
              pw.Container(
                padding: const pw.EdgeInsets.all(10),
                decoration: pw.BoxDecoration(
                  color: verdictBg,
                  border: pw.Border.all(color: verdictColor, width: 1.5),
                  borderRadius: const pw.BorderRadius.all(pw.Radius.circular(4)),
                ),
                child: pw.Column(
                  crossAxisAlignment: pw.CrossAxisAlignment.start,
                  children: [
                    pw.Text(
                      verdictText,
                      style: pw.TextStyle(
                        color: verdictColor,
                        fontSize: 12,
                        fontWeight: pw.FontWeight.bold,
                      ),
                    ),
                    pw.SizedBox(height: 4),
                    pw.Text(
                      isGoodProduct
                          ? "Package label satisfies all core statutory Legal Metrology (Packaged Commodities) Rules, 2011 declarations."
                          : "Package label violates mandatory legal metrology provisions. Legal enforcement action recommended under Section 36(1) of LM Act, 2009.",
                      style: const pw.TextStyle(fontSize: 9, color: PdfColors.grey900),
                    ),
                  ],
                ),
              ),
              pw.SizedBox(height: 14),

              // Failure Justification Section
              pw.Text(
                "Legal Metrology Guideline Failure Justifications",
                style: pw.TextStyle(fontSize: 11, fontWeight: pw.FontWeight.bold, color: PdfColors.red900),
              ),
              pw.SizedBox(height: 4),
              if (failingFindings.isEmpty)
                pw.Container(
                  padding: const pw.EdgeInsets.all(8),
                  decoration: const pw.BoxDecoration(color: PdfColors.green50),
                  child: pw.Text("✓ No guideline violations detected. Product is fully compliant.", style: const pw.TextStyle(fontSize: 9, color: PdfColors.green800)),
                )
              else
                pw.Column(
                  children: failingFindings.map((f) {
                    return pw.Container(
                      margin: const pw.EdgeInsets.only(bottom: 6),
                      padding: const pw.EdgeInsets.all(8),
                      decoration: pw.BoxDecoration(
                        border: pw.Border.all(color: PdfColors.red200),
                        color: PdfColors.red50,
                      ),
                      child: pw.Row(
                        crossAxisAlignment: pw.CrossAxisAlignment.start,
                        children: [
                          pw.Text("• [${f.ruleId} Violation]: ", style: pw.TextStyle(fontWeight: pw.FontWeight.bold, fontSize: 9, color: PdfColors.red900)),
                          pw.Expanded(
                            child: pw.Text(
                              "${f.clauseReference} — ${f.description}",
                              style: const pw.TextStyle(fontSize: 9, color: PdfColors.red900),
                            ),
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ),
              pw.SizedBox(height: 14),

              // Mandatory Statutory Declarations Table
              pw.Text("Mandatory Statutory Declarations Extracted", style: pw.TextStyle(fontSize: 10, fontWeight: pw.FontWeight.bold)),
              pw.SizedBox(height: 4),
              pw.TableHelper.fromTextArray(
                headers: ['Statutory Field', 'Extracted Value', 'Confidence', 'Status'],
                data: report.declarations.map((d) {
                  return [
                    d.fieldType,
                    d.normalizedValue.isNotEmpty ? d.normalizedValue : d.rawText,
                    '${(d.confidence * 100).round()}%',
                    d.status,
                  ];
                }).toList(),
                headerStyle: pw.TextStyle(fontWeight: pw.FontWeight.bold, color: PdfColors.white, fontSize: 8),
                headerDecoration: const pw.BoxDecoration(color: PdfColors.blueGrey800),
                cellStyle: const pw.TextStyle(fontSize: 8),
                cellHeight: 18,
              ),
              pw.SizedBox(height: 14),

              // Footer
              pw.Spacer(),
              pw.Divider(),
              pw.Row(
                mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                children: [
                  pw.Text("Generated by APEX LabelSure Scanner for $organizationName", style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey600)),
                  pw.Text("Official Legal Metrology Enforcement Record", style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey600)),
                ],
              ),
            ],
          );
        },
      ),
    );

    final pdfBytes = await pdf.save();

    await Printing.sharePdf(
      bytes: pdfBytes,
      filename: '${report.inspectionId}_Compliance_Report.pdf',
    );
  }
}
