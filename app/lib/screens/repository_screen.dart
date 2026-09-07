import 'package:flutter/material.dart';
import '../services/storage_service.dart';
import '../services/pdf_generator_service.dart';
import '../widgets/status_badge.dart';
import 'result_detail_screen.dart';

class RepositoryScreen extends StatefulWidget {
  final String initialQuery;

  const RepositoryScreen({
    super.key,
    this.initialQuery = '',
  });

  @override
  State<RepositoryScreen> createState() => _RepositoryScreenState();
}

class _RepositoryScreenState extends State<RepositoryScreen> {
  late TextEditingController _searchController;
  String _activeCategoryFilter = 'ALL';

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController(text: widget.initialQuery);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final queryText = _searchController.text;
    var rawReports = StorageService.searchReports(queryText);

    // Apply category / status chip filter
    if (_activeCategoryFilter != 'ALL') {
      if (_activeCategoryFilter == 'PASS') {
        rawReports = rawReports.where((r) {
          final s = r.overallStatus.toUpperCase();
          return s == 'PASS' || s == 'APPROVED';
        }).toList();
      } else if (_activeCategoryFilter == 'REVIEW') {
        rawReports = rawReports.where((r) => r.overallStatus.toUpperCase() == 'REVIEW').toList();
      } else {
        rawReports = rawReports.where((r) => r.category.toUpperCase().contains(_activeCategoryFilter)).toList();
      }
    }

    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.folder_special_rounded, color: Color(0xFF00E5FF), size: 22),
            SizedBox(width: 10),
            Text("Local Memory Repository", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          ],
        ),
        actions: [
          if (StorageService.getReports().isNotEmpty)
            IconButton(
              icon: const Icon(Icons.delete_sweep_rounded, color: Colors.grey),
              tooltip: "Clear Memory Repository",
              onPressed: () async {
                final confirm = await showDialog<bool>(
                  context: context,
                  builder: (ctx) => AlertDialog(
                    backgroundColor: const Color(0xFF161E2E),
                    title: const Text("Clear Saved Reports?", style: TextStyle(color: Colors.white)),
                    content: const Text("Are you sure you want to delete all saved reports from local memory storage?"),
                    actions: [
                      TextButton(
                        child: const Text("Cancel"),
                        onPressed: () => Navigator.pop(ctx, false),
                      ),
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
                        child: const Text("Clear All"),
                        onPressed: () => Navigator.pop(ctx, true),
                      ),
                    ],
                  ),
                );
                if (confirm == true) {
                  await StorageService.clearAll();
                  setState(() {});
                }
              },
            ),
        ],
      ),
      body: Column(
        children: [
          // Search & Filter Bar Box
          Container(
            padding: const EdgeInsets.all(16),
            decoration: const BoxDecoration(
              color: Color(0xFF111827),
              border: Border(bottom: BorderSide(color: Color(0xFF1F293D))),
            ),
            child: Column(
              children: [
                TextField(
                  controller: _searchController,
                  onChanged: (q) => setState(() {}),
                  style: const TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    hintText: "Search local memory reports by Product Name, Case ID, Category...",
                    hintStyle: const TextStyle(color: Colors.grey, fontSize: 13),
                    prefixIcon: const Icon(Icons.search_rounded, color: Color(0xFF00E5FF)),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear_rounded, color: Colors.grey),
                            onPressed: () {
                              _searchController.clear();
                              setState(() {});
                            },
                          )
                        : null,
                    filled: true,
                    fillColor: const Color(0xFF161E2E),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: const BorderSide(color: Color(0xFF1F293D)),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: const BorderSide(color: Color(0xFF00E5FF)),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                
                // Quick Filter Chips
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _buildFilterChip('ALL', 'All Scans (${StorageService.getReports().length})'),
                      const SizedBox(width: 8),
                      _buildFilterChip('PASS', 'Compliant (Pass)'),
                      const SizedBox(width: 8),
                      _buildFilterChip('REVIEW', 'Violations (Flagged)'),
                      const SizedBox(width: 8),
                      _buildFilterChip('FOOD', 'Food Products'),
                      const SizedBox(width: 8),
                      _buildFilterChip('COSMETICS', 'Cosmetics'),
                      const SizedBox(width: 8),
                      _buildFilterChip('IMPORTED', 'Imported'),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Repository Records List
          Expanded(
            child: rawReports.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.folder_off_outlined, size: 56, color: Colors.grey),
                          const SizedBox(height: 14),
                          Text(
                            _searchController.text.isEmpty && _activeCategoryFilter == 'ALL'
                                ? "No saved inspection reports in local memory yet."
                                : "No reports match your active search filters.",
                            style: const TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.w500),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 6),
                          Text(
                            _searchController.text.isEmpty && _activeCategoryFilter == 'ALL'
                                ? "Scan a package label using 'Scan Label' tab to dynamically populate your memory repository."
                                : "Try clearing your search query or selecting 'All Scans'.",
                            style: TextStyle(color: Colors.grey.shade500, fontSize: 12),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 14),
                          if (_searchController.text.isNotEmpty || _activeCategoryFilter != 'ALL')
                            ElevatedButton.icon(
                              onPressed: () {
                                _searchController.clear();
                                setState(() => _activeCategoryFilter = 'ALL');
                              },
                              icon: const Icon(Icons.refresh_rounded, size: 16),
                              label: const Text("Reset Search Filters"),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xFF161E2E),
                                foregroundColor: const Color(0xFF00E5FF),
                              ),
                            ),
                        ],
                      ),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: rawReports.length,
                    itemBuilder: (context, index) {
                      final report = rawReports[index];
                      final prodNameDecl = report.declarations.firstWhere(
                        (d) => d.fieldType == 'PRODUCT_NAME',
                        orElse: () => report.declarations.isNotEmpty ? report.declarations.first : report.declarations.first,
                      );
                      final displayName = prodNameDecl.normalizedValue.isNotEmpty
                          ? prodNameDecl.normalizedValue
                          : report.inspectionId;

                      final failCount = report.findings.where((f) => f.status.toUpperCase() == 'FAIL').length;

                      return Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(
                          color: const Color(0xFF161E2E),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: const Color(0xFF1F293D)),
                        ),
                        child: Material(
                          color: Colors.transparent,
                          borderRadius: BorderRadius.circular(14),
                          child: ListTile(
                            contentPadding: const EdgeInsets.all(12),
                            leading: Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: _isPassStatus(report.overallStatus)
                                    ? const Color(0xFF10B981).withValues(alpha: 0.15)
                                    : Colors.redAccent.withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Icon(
                                _isPassStatus(report.overallStatus)
                                    ? Icons.verified_rounded
                                    : Icons.gavel_rounded,
                                color: _isPassStatus(report.overallStatus)
                                    ? const Color(0xFF10B981)
                                    : Colors.redAccent,
                                size: 26,
                              ),
                            ),
                            title: Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    displayName,
                                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                                StatusBadge(status: report.overallStatus),
                              ],
                            ),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const SizedBox(height: 6),
                                Text(
                                  "Case: ${report.inspectionId} • Category: ${report.category}",
                                  style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
                                ),
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    Icon(Icons.list_alt_rounded, size: 14, color: Colors.grey.shade400),
                                    const SizedBox(width: 4),
                                    Text(
                                      "${report.declarations.length} Declarations",
                                      style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
                                    ),
                                    const SizedBox(width: 12),
                                    Icon(Icons.shield_outlined, size: 14, color: const Color(0xFF00E5FF)),
                                    const SizedBox(width: 4),
                                    Text(
                                      "Score: ${report.complianceScore.round()}%",
                                      style: const TextStyle(color: Color(0xFF00E5FF), fontSize: 12, fontWeight: FontWeight.bold),
                                    ),
                                    if (failCount > 0) ...[
                                      const SizedBox(width: 12),
                                      Icon(Icons.warning_amber_rounded, size: 14, color: Colors.redAccent),
                                      const SizedBox(width: 4),
                                      Text(
                                        "$failCount Flagged",
                                        style: const TextStyle(color: Colors.redAccent, fontSize: 12, fontWeight: FontWeight.bold),
                                      ),
                                    ]
                                  ],
                                ),
                              ],
                            ),
                            trailing: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                IconButton(
                                  icon: const Icon(Icons.picture_as_pdf_rounded, color: Color(0xFF00E5FF)),
                                  tooltip: "Download PDF Report",
                                  onPressed: () async {
                                    await PdfGeneratorService.exportCompliancePdf(report);
                                  },
                                ),
                                PopupMenuButton<String>(
                                  icon: const Icon(Icons.more_vert_rounded, color: Colors.grey),
                                  onSelected: (val) async {
                                    if (val == 'delete') {
                                      await StorageService.deleteReport(report.inspectionId);
                                      setState(() {});
                                    }
                                  },
                                  itemBuilder: (ctx) => [
                                    const PopupMenuItem(
                                      value: 'delete',
                                      child: Row(
                                        children: [
                                          Icon(Icons.delete_outline_rounded, color: Colors.redAccent, size: 18),
                                          SizedBox(width: 8),
                                          Text("Delete Report", style: TextStyle(color: Colors.redAccent)),
                                        ],
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            onTap: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => ResultDetailScreen(report: report),
                                ),
                              );
                            },
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  static bool _isPassStatus(String status) {
    final s = status.toUpperCase();
    return s == 'PASS' || s == 'APPROVED';
  }

  Widget _buildFilterChip(String value, String label) {
    final isSelected = _activeCategoryFilter == value;
    return ChoiceChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (selected) {
        if (selected) {
          setState(() => _activeCategoryFilter = value);
        }
      },
      selectedColor: const Color(0xFF00E5FF).withValues(alpha: 0.25),
      backgroundColor: const Color(0xFF161E2E),
      labelStyle: TextStyle(
        color: isSelected ? const Color(0xFF00E5FF) : Colors.grey.shade400,
        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
        fontSize: 12,
      ),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(
          color: isSelected ? const Color(0xFF00E5FF) : const Color(0xFF1F293D),
        ),
      ),
    );
  }
}
