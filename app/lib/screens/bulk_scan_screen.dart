import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../models/inspection_model.dart';
import '../services/api_service.dart';
import '../services/pdf_generator_service.dart';
import '../services/storage_service.dart';
import 'result_detail_screen.dart';

class BulkScanScreen extends StatefulWidget {
  const BulkScanScreen({super.key});

  @override
  State<BulkScanScreen> createState() => _BulkScanScreenState();
}

class _BulkScanScreenState extends State<BulkScanScreen> {
  final TextEditingController _orgController = TextEditingController(text: "Legal Metrology Enforcement Dept.");
  final ImagePicker _picker = ImagePicker();

  List<XFile> _selectedFiles = [];
  bool _isProcessing = false;
  int _processedCount = 0;
  String _statusMessage = "";

  Map<String, dynamic>? _batchResult;
  List<InspectionReport> _batchReports = [];

  Future<void> _pickMultipleImages() async {
    try {
      final List<XFile> images = await _picker.pickMultiImage(imageQuality: 85);
      if (images.isNotEmpty) {
        setState(() {
          _selectedFiles = images;
          _batchResult = null;
          _batchReports = [];
          _statusMessage = "Selected ${images.length} label images for bulk audit.";
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Error selecting images: $e")),
      );
    }
  }

  Future<void> _startBulkBatchScan() async {
    final orgName = _orgController.text.trim();
    if (orgName.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please enter an Organization Name prior to bulk scan.")),
      );
      return;
    }

    if (_selectedFiles.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text("Please select package label images to scan.")),
      );
      return;
    }

    setState(() {
      _isProcessing = true;
      _processedCount = 0;
      _statusMessage = "Reading ${_selectedFiles.length} images...";
    });

    try {
      List<Uint8List> bytesList = [];
      List<String> filenames = [];

      for (int i = 0; i < _selectedFiles.length; i++) {
        setState(() {
          _statusMessage = "Preparing image ${i + 1} of ${_selectedFiles.length}...";
        });
        final bytes = await _selectedFiles[i].readAsBytes();
        bytesList.add(bytes);
        filenames.add(_selectedFiles[i].name);
      }

      setState(() {
        _statusMessage = "Running OCR & Rule Engine across ${bytesList.length} images...";
      });

      final result = await ApiService.scanPackageLabelsBulk(
        imagesBytes: bytesList,
        filenames: filenames,
        organizationName: orgName,
      );

      final List<InspectionReport> reports = result['reports'] ?? [];
      for (final r in reports) {
        await StorageService.saveReport(r);
      }

      setState(() {
        _isProcessing = false;
        _batchResult = result;
        _batchReports = reports;
        _statusMessage = "Batch scan completed successfully!";
      });
    } catch (e) {
      setState(() {
        _isProcessing = false;
        _statusMessage = "Bulk scan error: $e";
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Bulk Audit Error: $e")),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final totalScanned = _batchResult?['total_scanned'] ?? 0;
    final passedCount = _batchResult?['passed_count'] ?? 0;
    final failedCount = _batchResult?['failed_count'] ?? 0;
    final reviewCount = _batchResult?['review_count'] ?? 0;
    final rate = _batchResult?['batch_compliance_rate'] ?? '0%';

    return Scaffold(
      appBar: AppBar(
        title: const Text("Bulk Batch Audit Module"),
        actions: [
          IconButton(
            icon: const Icon(Icons.help_outline_rounded, color: Color(0xFF00E5FF)),
            onPressed: () {
              showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  backgroundColor: const Color(0xFF161E2E),
                  title: const Text("Bulk Upload Guidance", style: TextStyle(color: Colors.white)),
                  content: const Text(
                    "• Step 1: Specify your Organization / Authority Name.\n"
                    "• Step 2: Select 10+ label images from gallery.\n"
                    "• Step 3: Run Bulk Audit for aggregated compliance metrics and failure justifications.\n"
                    "• Step 4: Export individual or batch PDF inspection reports.",
                    style: TextStyle(color: Colors.grey, fontSize: 13),
                  ),
                  actions: [
                    TextButton(
                      onPressed: () => Navigator.pop(ctx),
                      child: const Text("OK"),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Module Banner Header
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF1E1B4B), Color(0xFF311B92)],
                ),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF6366F1).withOpacity(0.4)),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF6366F1).withOpacity(0.2),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.collections_rounded, color: Color(0xFF818CF8), size: 28),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        Text(
                          "Enterprise Bulk Audit & Batch Scanner",
                          style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        SizedBox(height: 2),
                        Text(
                          "Process 10+ package label images simultaneously with Organization-level compliance reporting.",
                          style: TextStyle(color: Color(0xFFC7D2FE), fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Step 1: Organization Name Input
            const Text(
              "Step 1: Organization / Authority Name",
              style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _orgController,
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                filled: true,
                fillColor: const Color(0xFF161E2E),
                hintText: "e.g., Acme Foods Pvt. Ltd. or District Legal Metrology Inspectorate",
                hintStyle: TextStyle(color: Colors.grey.shade600),
                prefixIcon: const Icon(Icons.business_rounded, color: Color(0xFF00E5FF)),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Step 2: Multi-Image Picker Button
            const Text(
              "Step 2: Select Package Label Images (10+ Supported)",
              style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: _isProcessing ? null : _pickMultipleImages,
                    icon: const Icon(Icons.photo_library_rounded),
                    label: Text(_selectedFiles.isEmpty ? "Select Images (Batch)" : "Change Selected (${_selectedFiles.length})"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1F2937),
                      foregroundColor: const Color(0xFF00E5FF),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      side: const BorderSide(color: Color(0xFF00E5FF)),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                ElevatedButton.icon(
                  onPressed: (_isProcessing || _selectedFiles.isEmpty) ? null : _startBulkBatchScan,
                  icon: const Icon(Icons.play_arrow_rounded),
                  label: const Text("Start Bulk Audit"),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF10B981),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Status / Progress Message
            if (_statusMessage.isNotEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF161E2E),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Row(
                  children: [
                    if (_isProcessing)
                      const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF00E5FF)),
                      )
                    else
                      const Icon(Icons.info_outline_rounded, color: Color(0xFF00E5FF), size: 18),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        _statusMessage,
                        style: const TextStyle(color: Colors.white, fontSize: 12),
                      ),
                    ),
                  ],
                ),
              ),

            const SizedBox(height: 24),

            // Step 3: Aggregated Organization Batch Dashboard (Results)
            if (_batchResult != null) ...[
              // Consolidated Bulk PDF Export Banner
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF1E293B),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFF00E5FF)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "Batch ID: ${_batchResult!['batch_id']}",
                            style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            "Organization: ${_batchResult!['organization_name'] ?? _orgController.text}",
                            style: const TextStyle(color: Colors.grey, fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                    ElevatedButton.icon(
                      onPressed: () {
                        if (_batchReports.isNotEmpty) {
                          PdfGeneratorService.exportCompliancePdf(
                            _batchReports.first,
                            organizationName: _orgController.text.trim(),
                          );
                        }
                      },
                      icon: const Icon(Icons.picture_as_pdf_rounded, color: Colors.black, size: 18),
                      label: const Text("Export Consolidated Bulk PDF", style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 11)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF00E5FF),
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Summary Metric Cards Grid
              Row(
                children: [
                  Expanded(
                    child: _buildMetricCard(
                      label: "Total Scanned",
                      value: "$totalScanned",
                      color: const Color(0xFF3B82F6),
                      icon: Icons.inventory_2_rounded,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _buildMetricCard(
                      label: "Good (Passed)",
                      value: "$passedCount",
                      color: const Color(0xFF10B981),
                      icon: Icons.check_circle_rounded,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _buildMetricCard(
                      label: "Bad (Failed)",
                      value: "$failedCount",
                      color: const Color(0xFFEF4444),
                      icon: Icons.cancel_rounded,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: _buildMetricCard(
                      label: "Review Req.",
                      value: "$reviewCount",
                      color: const Color(0xFFF59E0B),
                      icon: Icons.warning_amber_rounded,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Table / List of Scanned Products in Batch
              const Text(
                "Scanned Product Label Reports in Batch",
                style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 10),

              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: _batchReports.length,
                itemBuilder: (context, idx) {
                  final r = _batchReports[idx];
                  final isPass = r.overallStatus == 'APPROVED' || r.overallStatus == 'PASS';
                  final isFail = r.overallStatus == 'REJECTED' || r.overallStatus == 'FAIL';

                  final badgeColor = isPass
                      ? const Color(0xFF10B981)
                      : (isFail ? const Color(0xFFEF4444) : const Color(0xFFF59E0B));

                  return Card(
                    color: const Color(0xFF161E2E),
                    margin: const EdgeInsets.only(bottom: 10),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: badgeColor.withOpacity(0.2),
                        child: Text(
                          "#${idx + 1}",
                          style: TextStyle(color: badgeColor, fontWeight: FontWeight.bold),
                        ),
                      ),
                      title: Text(
                        r.verdictTitle,
                        style: TextStyle(color: badgeColor, fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                      subtitle: Text(
                        "Case: ${r.inspectionId} | Score: ${r.complianceScore.round()}%\n"
                        "${r.failureJustifications.isNotEmpty ? 'Violations: ${r.failureJustifications.length} rules' : 'Fully Compliant'}",
                        style: const TextStyle(color: Colors.grey, fontSize: 11),
                      ),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.picture_as_pdf_rounded, color: Color(0xFF00E5FF)),
                            tooltip: "Export PDF Report",
                            onPressed: () {
                              PdfGeneratorService.exportCompliancePdf(
                                r,
                                organizationName: _orgController.text.trim(),
                              );
                            },
                          ),
                          IconButton(
                            icon: const Icon(Icons.chevron_right_rounded, color: Colors.white),
                            onPressed: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => ResultDetailScreen(report: r),
                                ),
                              );
                            },
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCard({
    required String label,
    required String value,
    required Color color,
    required IconData icon,
  }) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xFF161E2E),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(color: color, fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: const TextStyle(color: Colors.grey, fontSize: 9),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
