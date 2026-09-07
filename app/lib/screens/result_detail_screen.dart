import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import '../models/inspection_model.dart';
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
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _exportPdf() async {
    setState(() => _isGeneratingPdf = true);
    try {
      await PdfGeneratorService.exportCompliancePdf(widget.report);
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
    if (widget.report.imageBytes != null) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(10),
        child: Image.memory(
          widget.report.imageBytes!,
          height: 180,
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
          height: 180,
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
            Tab(text: "Declarations (${widget.report.declarations.length})"),
            Tab(text: "Rules (${widget.report.findings.length})"),
          ],
        ),
      ),
      body: Column(
        children: [
          // Banner Overview
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            color: isPass ? const Color(0xFF064E3B) : const Color(0xFF7F1D1D),
            child: Row(
              children: [
                Icon(
                  isPass ? Icons.check_circle_rounded : Icons.warning_amber_rounded,
                  color: isPass ? const Color(0xFF10B981) : Colors.redAccent,
                  size: 36,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        isPass ? "COMPLIANT WITH PCR 2011" : "FLAGGED FOR ENFORCEMENT REVIEW",
                        style: TextStyle(
                          color: isPass ? const Color(0xFF10B981) : Colors.redAccent,
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        "Compliance Score: ${widget.report.complianceScore.round()}% • Category: ${widget.report.category}",
                        style: const TextStyle(color: Colors.white70, fontSize: 12),
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
                // TAB 1: EXTRACTED STATUTORY DECLARATIONS
                ListView(
                  padding: const EdgeInsets.all(14),
                  children: [
                    _buildImagePreview(),
                    const SizedBox(height: 14),
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

                // TAB 2: PCR 2011 RULE FINDINGS
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
}
