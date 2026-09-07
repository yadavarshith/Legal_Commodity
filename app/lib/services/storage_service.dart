import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';
import '../models/inspection_model.dart';

class StorageService {
  static final List<InspectionReport> _history = [];
  static bool _initialized = false;

  /// Load persisted reports from local disk memory on startup
  static Future<void> init() async {
    if (_initialized) return;
    _initialized = true;

    try {
      if (kIsWeb) {
        // Web in-memory storage initialized empty
        return;
      }
      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/labelsure_inspections.json');
      if (await file.exists()) {
        final content = await file.readAsString();
        if (content.isNotEmpty) {
          final List<dynamic> jsonList = jsonDecode(content);
          _history.clear();
          for (var item in jsonList) {
            try {
              _history.add(InspectionReport.fromJson(item as Map<String, dynamic>));
            } catch (e) {
              debugPrint('Error parsing report item from local storage: $e');
            }
          }
        }
      }
    } catch (e) {
      debugPrint('StorageService init error: $e');
    }
  }

  /// Persist current in-memory history to local storage disk file
  static Future<void> _persist() async {
    if (kIsWeb) return;
    try {
      final dir = await getApplicationDocumentsDirectory();
      final file = File('${dir.path}/labelsure_inspections.json');
      final jsonList = _history.map((r) => r.toJson()).toList();
      await file.writeAsString(jsonEncode(jsonList));
    } catch (e) {
      debugPrint('StorageService _persist error: $e');
    }
  }

  /// Save a new scanned report to local memory storage
  static Future<void> saveReport(InspectionReport report) async {
    await init();
    _history.removeWhere((r) => r.inspectionId == report.inspectionId);
    _history.insert(0, report);
    await _persist();
  }

  /// Delete a report from local memory storage
  static Future<void> deleteReport(String inspectionId) async {
    await init();
    _history.removeWhere((r) => r.inspectionId == inspectionId);
    await _persist();
  }

  /// Clear all saved reports from memory storage
  static Future<void> clearAll() async {
    await init();
    _history.clear();
    await _persist();
  }

  /// Get all dynamically scanned reports in local memory
  static List<InspectionReport> getReports() {
    return List.unmodifiable(_history);
  }

  /// Retrieve a specific report by ID
  static InspectionReport? getReportById(String id) {
    try {
      return _history.firstWhere((r) => r.inspectionId == id);
    } catch (_) {
      return null;
    }
  }

  /// Dynamic real-time search across all stored reports
  static List<InspectionReport> searchReports(String query) {
    final reports = getReports();
    if (query.trim().isEmpty) return reports;
    final lower = query.trim().toLowerCase();
    return reports.where((r) {
      final matchesId = r.inspectionId.toLowerCase().contains(lower);
      final matchesCat = r.category.toLowerCase().contains(lower);
      final matchesStatus = r.overallStatus.toLowerCase().contains(lower);
      final matchesDecl = r.declarations.any((d) =>
          d.normalizedValue.toLowerCase().contains(lower) ||
          d.rawText.toLowerCase().contains(lower) ||
          d.fieldType.toLowerCase().contains(lower));
      final matchesFinding = r.findings.any((f) =>
          f.description.toLowerCase().contains(lower) ||
          f.ruleId.toLowerCase().contains(lower));
      return matchesId || matchesCat || matchesStatus || matchesDecl || matchesFinding;
    }).toList();
  }

  /// Analytics summary derived purely from user's scanned reports
  static Map<String, dynamic> getDashboardMetrics() {
    final total = _history.length;
    final passed = _history.where((r) {
      final s = r.overallStatus.toUpperCase();
      return s == 'PASS' || s == 'APPROVED';
    }).length;
    final flagged = total - passed;
    final passRate = total > 0 ? (passed / total) * 100 : 100.0;

    return {
      'total_inspections': total,
      'passed_count': passed,
      'flagged_count': flagged,
      'pass_rate': passRate.toStringAsFixed(1),
    };
  }
}
