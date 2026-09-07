import 'package:flutter/material.dart';
import '../services/storage_service.dart';
import '../widgets/status_badge.dart';
import 'result_detail_screen.dart';

class DashboardScreen extends StatelessWidget {
  final VoidCallback onStartScan;
  final VoidCallback onViewRepository;

  const DashboardScreen({
    super.key,
    required this.onStartScan,
    required this.onViewRepository,
  });

  @override
  Widget build(BuildContext context) {
    final metrics = StorageService.getDashboardMetrics();
    final recentReports = StorageService.getReports().toList();

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: const Color(0xFF00E5FF).withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.shield_outlined, color: Color(0xFF00E5FF), size: 22),
            ),
            const SizedBox(width: 10),
            const Text(
              'Enforcement Dashboard',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
          ],
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Banner & Quick Action
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF1E293B), Color(0xFF0F172A)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFF00E5FF).withValues(alpha: 0.4)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.verified_rounded, color: Color(0xFF00E5FF), size: 22),
                      SizedBox(width: 8),
                      Text(
                        "Legal Metrology (PCR 2011) System",
                        style: TextStyle(color: Color(0xFF00E5FF), fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    "Automated Label Compliance Scanner",
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    "Scan commodity labels to detect mandatory declarations, MRP violations, net quantity standard units & font legibility.",
                    style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
                  ),
                  const SizedBox(height: 14),
                  ElevatedButton.icon(
                    onPressed: onStartScan,
                    icon: const Icon(Icons.camera_alt_rounded, color: Colors.black),
                    label: const Text(
                      "⚡ SCAN NEW PACKAGE LABEL",
                      style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF00E5FF),
                      minimumSize: const Size(double.infinity, 44),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Statistics Grid
            const Text(
              "Inspection Analytics & Summary",
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: _buildMetricCard(
                    title: "Total Audited",
                    value: "${metrics['total_inspections']}",
                    icon: Icons.assignment_rounded,
                    color: const Color(0xFF00E5FF),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _buildMetricCard(
                    title: "Compliance Rate",
                    value: "${metrics['pass_rate']}%",
                    icon: Icons.fact_check_rounded,
                    color: const Color(0xFF10B981),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: _buildMetricCard(
                    title: "Compliant (Pass)",
                    value: "${metrics['passed_count']}",
                    icon: Icons.check_circle_outline_rounded,
                    color: const Color(0xFF10B981),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _buildMetricCard(
                    title: "Violations Flagged",
                    value: "${metrics['flagged_count']}",
                    icon: Icons.warning_amber_rounded,
                    color: Colors.redAccent,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Recent Inspection History Feed Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  "Recent Scanned Products",
                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                ),
                TextButton.icon(
                  onPressed: onViewRepository,
                  icon: const Icon(Icons.arrow_forward_rounded, size: 16, color: Color(0xFF00E5FF)),
                  label: const Text("View All", style: TextStyle(color: Color(0xFF00E5FF), fontWeight: FontWeight.bold)),
                ),
              ],
            ),
            const SizedBox(height: 8),

            if (recentReports.isEmpty)
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFF161E2E),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF1F293D)),
                ),
                child: const Center(
                  child: Column(
                    children: [
                      Icon(Icons.inventory_2_outlined, color: Colors.grey, size: 36),
                      SizedBox(height: 8),
                      Text("No inspection records in repository yet.", style: TextStyle(color: Colors.grey)),
                      SizedBox(height: 4),
                      Text("Click 'Scan New Package Label' to start auditing.", style: TextStyle(color: Colors.grey, fontSize: 11)),
                    ],
                  ),
                ),
              )
            else
              ...recentReports.map((report) {
                final prodDecl = report.declarations.firstWhere(
                  (d) => d.fieldType == 'PRODUCT_NAME',
                  orElse: () => report.declarations.isNotEmpty ? report.declarations.first : report.declarations.first,
                );
                final prodName = prodDecl.normalizedValue.isNotEmpty
                    ? prodDecl.normalizedValue
                    : report.inspectionId;

                final isCompliant = _isPassStatus(report.overallStatus);

                return Container(
                  margin: const EdgeInsets.only(bottom: 10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF161E2E),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF1F293D)),
                  ),
                  child: ListTile(
                    contentPadding: const EdgeInsets.all(12),
                    leading: Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: isCompliant
                            ? const Color(0xFF10B981).withValues(alpha: 0.15)
                            : Colors.redAccent.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Icon(
                        isCompliant
                            ? Icons.verified_rounded
                            : Icons.warning_amber_rounded,
                        color: isCompliant
                            ? const Color(0xFF10B981)
                            : Colors.redAccent,
                        size: 24,
                      ),
                    ),
                    title: Text(
                      prodName,
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    subtitle: Text(
                      "ID: ${report.inspectionId} • Category: ${report.category} • Score: ${report.complianceScore.round()}%",
                      style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
                    ),
                    trailing: StatusBadge(status: report.overallStatus),
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => ResultDetailScreen(report: report),
                        ),
                      );
                    },
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  static bool _isPassStatus(String status) {
    final s = status.toUpperCase();
    return s == 'PASS' || s == 'APPROVED';
  }

  Widget _buildMetricCard({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF161E2E),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF1F293D)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: TextStyle(color: Colors.grey.shade400, fontSize: 11)),
              Icon(icon, color: color, size: 18),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 20),
          ),
        ],
      ),
    );
  }
}
