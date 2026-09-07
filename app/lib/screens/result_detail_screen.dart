import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import '../models/inspection_model.dart';
import '../services/api_service.dart';
import '../services/pdf_generator_service.dart';
import '../widgets/declaration_tile.dart';
import '../widgets/finding_card.dart';

class ResultDetailScreen extends StatefulWidget {
  final InspectionReport report;

  const ResultDetailScreen({super.key, required this.report});

  @override
  State<ResultDetailScreen> createState() => _ResultDetailScreenState();
}

class _ResultDetailScreenState extends State<ResultDetailScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isGeneratingPdf = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _exportPdf() async {
    setState(() => _isGeneratingPdf = true);
    try {
      await PdfGeneratorService.exportCompliancePdf(
        widget.report,
        organizationName: widget.report.organizationName,
      );
      if (!mounted) return;
      setState(() => _isGeneratingPdf = false);

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text("PDF Report exported successfully!"),
          backgroundColor: Color(0xFF10B981),
          duration: Duration(seconds: 4),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _isGeneratingPdf = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Failed to export PDF: $e")),
      );
    }
  }

  Widget _buildImagePreview() {
    // 1. Annotated Bounding Box Image from server
    if (widget.report.annotatedImageUrl != null && widget.report.annotatedImageUrl!.isNotEmpty) {
      final fullUrl = widget.report.annotatedImageUrl!.startsWith('http')
          ? widget.report.annotatedImageUrl!
          : '${ApiService.baseUrl}${widget.report.annotatedImageUrl!}';
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text(
                "Annotated Label Image (OCR Bounding Box Overlays)",
                style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
              ),
              Text(
                "🟢 Pass  🔴 Fail  🟡 Warn",
                style: TextStyle(color: Colors.grey, fontSize: 10),
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: Image.network(
              fullUrl,
              height: 240,
              width: double.infinity,
              fit: BoxFit.contain,
              errorBuilder: (ctx, err, stack) => _buildLocalFallbackImage(),
            ),
          ),
        ],
      );
    }

    return _buildLocalFallbackImage();
  }

  Widget _buildLocalFallbackImage() {
    if (widget.report.imageBytes != null) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(10),
        child: Image.memory(
          widget.report.imageBytes!,
          height: 200,
          width: double.infinity,
          fit: BoxFit.contain,
        ),
      );
    }

    if (!kIsWeb && widget.report.imagePath.isNotEmpty && File(widget.report.imagePath).existsSync()) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(10),
        child: Image.file(
          File(widget.report.imagePath),
          height: 200,
          width: double.infinity,
          fit: BoxFit.contain,
        ),
      );
    }

    return const SizedBox.shrink();
  }

  @override
  Widget build(BuildContext context) {
    final status = widget.report.overallStatus.toUpperCase();
    final isPass = status == 'PASS' || status == 'APPROVED';
    final isFail = status == 'FAIL' || status == 'REJECTED';

    final bannerBg = isPass
        ? const Color(0xFF064E3B)
        : (isFail ? const Color(0xFF7F1D1D) : const Color(0xFF78350F));
    final bannerColor = isPass
        ? const Color(0xFF10B981)
        : (isFail ? const Color(0xFFEF4444) : const Color(0xFFF59E0B));

    return Scaffold(
      appBar: AppBar(
        title: Text("Inspection: ${widget.report.inspectionId}"),
        actions: [
          IconButton(
            icon: _isGeneratingPdf
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.picture_as_pdf_rounded, color: Color(0xFF00E5FF)),
            onPressed: _isGeneratingPdf ? null : _exportPdf,
            tooltip: "Export PDF Report",
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: const Color(0xFF00E5FF),
          labelColor: const Color(0xFF00E5FF),
          unselectedLabelColor: Colors.grey,
          tabs: [
            Tab(text: "Overview"),
            Tab(text: "Declarations (${widget.report.declarations.length})"),
            Tab(text: "Rules (${widget.report.findings.length})"),
          ],
        ),
      ),
      body: Column(
        children: [
          // Dynamic Product Verdict Banner
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            color: bannerBg,
            child: Row(
              children: [
                Icon(
                  isPass
                      ? Icons.check_circle_rounded
                      : (isFail ? Icons.cancel_rounded : Icons.warning_amber_rounded),
                  color: bannerColor,
                  size: 38,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.report.verdictTitle,
                        style: TextStyle(
                          color: bannerColor,
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        "Score: ${widget.report.complianceScore.round()}% • Org: ${widget.report.organizationName}",
                        style: const TextStyle(color: Colors.white70, fontSize: 11),
                      ),
                    ],
                  ),
                ),
                ElevatedButton.icon(
                  onPressed: _isGeneratingPdf ? null : _exportPdf,
                  icon: const Icon(Icons.download_rounded, size: 16, color: Colors.black),
                  label: const Text("PDF", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 12)),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00E5FF),
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  ),
                ),
              ],
            ),
          ),

          // Main Tab View Content
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                // TAB 1: OVERVIEW & BOUNDING BOX OVERLAY
                ListView(
                  padding: const EdgeInsets.all(14),
                  children: [
                    _buildImagePreview(),
                    const SizedBox(height: 16),

                    // PDF Country Comparison Note Card
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFF161E2E),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: const Color(0xFF3B82F6)),
                      ),
                      child: Row(
                        children: const [
                          Icon(Icons.picture_as_pdf_rounded, color: Color(0xFF3B82F6), size: 22),
                          SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              "International Country Comparison (India vs US FDA vs EU) is generated exclusively inside the PDF report.",
                              style: TextStyle(color: Colors.white70, fontSize: 12),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Failure Justifications Section
                    const Text(
                      "Legal Metrology Failure Justifications",
                      style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    if (widget.report.failureJustifications.isEmpty)
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: const Color(0xFF064E3B).withOpacity(0.3),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: const Color(0xFF10B981)),
                        ),
                        child: Row(
                          children: const [
                            Icon(Icons.verified_rounded, color: Color(0xFF10B981), size: 20),
                            SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                "No statutory violations detected. Package label is fully compliant with Legal Metrology (Packaged Commodities) Rules, 2011.",
                                style: TextStyle(color: Color(0xFF10B981), fontSize: 12),
                              ),
                            ),
                          ],
                        ),
                      )
                    else
                      ...widget.report.failureJustifications.map((j) {
                        return Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: const Color(0xFF7F1D1D).withOpacity(0.3),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: const Color(0xFFEF4444)),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                "Rule Failure: ${j['rule_id'] ?? 'Violation'}",
                                style: const TextStyle(color: Color(0xFFEF4444), fontWeight: FontWeight.bold, fontSize: 12),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                j['description'] ?? j['justification'] ?? '',
                                style: const TextStyle(color: Colors.white, fontSize: 12),
                              ),
                            ],
                          ),
                        );
                      }),
                  ],
                ),

                // TAB 2: EXTRACTED STATUTORY DECLARATIONS
                ListView(
                  padding: const EdgeInsets.all(14),
                  children: [
                    if (widget.report.declarations.isEmpty)
                      const Center(
                        child: Padding(
                          padding: EdgeInsets.all(30),
                          child: Text("No statutory declarations extracted.", style: TextStyle(color: Colors.grey)),
                        ),
                      )
                    else
                      ...widget.report.declarations.map((d) => DeclarationTile(declaration: d)),
                  ],
                ),

                // TAB 3: PCR 2011 RULE FINDINGS
                ListView(
                  padding: const EdgeInsets.all(14),
                  children: widget.report.findings.isEmpty
                      ? [
                          const Center(
                            child: Padding(
                              padding: EdgeInsets.all(30),
                              child: Text("No rule violations found.", style: TextStyle(color: Colors.grey)),
                            ),
                          )
                        ]
                      : widget.report.findings.map((f) => FindingCard(finding: f)).toList(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildJurisdictionRow(String country, String status, String note, Color color) {
    return Padding(
      padding: const EdgeInsets.only(top: 6, bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(
              country,
              style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: color.withOpacity(0.2),
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: color, width: 0.8),
            ),
            child: Text(
              status,
              style: TextStyle(color: color, fontSize: 9, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              note,
              style: const TextStyle(color: Colors.grey, fontSize: 10),
            ),
          ),
        ],
      ),
    );
  }
}
