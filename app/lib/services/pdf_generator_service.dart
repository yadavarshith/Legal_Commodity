import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import '../models/inspection_model.dart';

class PdfGeneratorService {
  /// Generates and triggers cross-platform PDF export/download (Web, Mobile, Desktop)
  static Future<void> exportCompliancePdf(InspectionReport report) async {
    final pdf = pw.Document();

    pdf.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.a4,
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
                      report.overallStatus,
                      style: pw.TextStyle(
                        color: report.overallStatus == 'PASS' ? PdfColors.green300 : PdfColors.orange300,
                        fontSize: 14,
                        fontWeight: pw.FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              pw.SizedBox(height: 14),

              // Metadata Table
              pw.Container(
                padding: const pw.EdgeInsets.all(10),
                decoration: pw.BoxDecoration(
                  border: pw.Border.all(color: PdfColors.grey400),
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
                        pw.Text("Category: ${report.category}"),
                        pw.Text("Compliance Score: ${report.complianceScore.round()}%"),
                      ],
                    ),
                  ],
                ),
              ),
              pw.SizedBox(height: 16),

              // Mandatory Statutory Declarations Table
              pw.Text("Mandatory Statutory Declarations Extracted", style: pw.TextStyle(fontSize: 11, fontWeight: pw.FontWeight.bold)),
              pw.SizedBox(height: 6),
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
                headerStyle: pw.TextStyle(fontWeight: pw.FontWeight.bold, color: PdfColors.white),
                headerDecoration: const pw.BoxDecoration(color: PdfColors.blueGrey700),
                cellHeight: 20,
              ),
              pw.SizedBox(height: 16),

              // PCR 2011 Rule Findings Table
              pw.Text("PCR 2011 Rule Compliance & Violation Findings", style: pw.TextStyle(fontSize: 11, fontWeight: pw.FontWeight.bold)),
              pw.SizedBox(height: 6),
              pw.TableHelper.fromTextArray(
                headers: ['Rule ID', 'Clause Reference', 'Finding Description', 'Status'],
                data: report.findings.map((f) {
                  return [
                    f.ruleId,
                    f.clauseReference,
                    f.description,
                    f.status,
                  ];
                }).toList(),
                headerStyle: pw.TextStyle(fontWeight: pw.FontWeight.bold, color: PdfColors.white),
                headerDecoration: const pw.BoxDecoration(color: PdfColors.blueGrey700),
                cellHeight: 20,
              ),
              pw.SizedBox(height: 20),

              // Legal Footer
              pw.Divider(),
              pw.Row(
                mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                children: [
                  pw.Text("Generated by APEX LabelSure Mobile Compliance Scanner", style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey600)),
                  pw.Text("Official Legal Metrology Enforcement Record", style: const pw.TextStyle(fontSize: 8, color: PdfColors.grey600)),
                ],
              ),
            ],
          );
        },
      ),
    );

    final pdfBytes = await pdf.save();

    // Printing.sharePdf handles PDF export/download seamlessly on ALL platforms (Web, Android, iOS, Windows)
    await Printing.sharePdf(
      bytes: pdfBytes,
      filename: '${report.inspectionId}_Compliance_Report.pdf',
    );
  }
}
