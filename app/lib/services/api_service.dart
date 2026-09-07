import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/inspection_model.dart';

import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static String baseUrl = 'http://127.0.0.1:8000'; // Default host

  /// Load persisted server IP address from SharedPreferences on app launch
  static Future<void> loadSavedBaseUrl() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final savedUrl = prefs.getString('labelsure_server_url');
      if (savedUrl != null && savedUrl.isNotEmpty) {
        baseUrl = savedUrl;
      }
    } catch (e) {
      debugPrint("Error loading saved server URL: $e");
    }
  }

  /// Update and save server IP address persistently across app restarts
  static Future<void> setBaseUrl(String url) async {
    if (url.endsWith('/')) {
      baseUrl = url.substring(0, url.length - 1);
    } else {
      baseUrl = url;
    }
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('labelsure_server_url', baseUrl);
    } catch (e) {
      debugPrint("Error saving server URL: $e");
    }
  }

  /// Sends uploaded image to backend /upload-and-scan endpoint.
  static Future<InspectionReport> scanPackageLabel({
    required Uint8List imageBytes,
    required String filename,
    String localPath = '',
    String category = 'all',
    String packageType = 'pre-packaged',
    String importStatus = 'domestic',
    String organizationName = 'General Public / Retail Audit',
  }) async {
    final uri = Uri.parse('$baseUrl/upload-and-scan');
    final request = http.MultipartRequest('POST', uri);

    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        imageBytes,
        filename: filename,
      ),
    );

    request.fields['category'] = category;
    request.fields['package_type'] = packageType;
    request.fields['import_status'] = importStatus;
    request.fields['organization_name'] = organizationName;

    final streamedResponse = await request.send().timeout(
      const Duration(seconds: 40),
      onTimeout: () {
        throw Exception("Server timeout while running OCR & Rule Engine at $baseUrl");
      },
    );

    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      final Map<String, dynamic> json = jsonDecode(response.body);
      return InspectionReport.fromJson(
        json,
        localPath: localPath,
        localBytes: imageBytes,
      );
    } else {
      throw Exception("Backend server returned HTTP ${response.statusCode}: ${response.body}");
    }
  }

  /// Bulk Upload Module:
  /// Sends 10+ package label images with Organization Name to /upload-bulk.
  static Future<Map<String, dynamic>> scanPackageLabelsBulk({
    required List<Uint8List> imagesBytes,
    required List<String> filenames,
    required String organizationName,
    String category = 'all',
    String packageType = 'pre-packaged',
    String importStatus = 'domestic',
  }) async {
    final uri = Uri.parse('$baseUrl/upload-bulk');
    final request = http.MultipartRequest('POST', uri);

    for (int i = 0; i < imagesBytes.length; i++) {
      request.files.add(
        http.MultipartFile.fromBytes(
          'files',
          imagesBytes[i],
          filename: filenames[i],
        ),
      );
    }

    request.fields['organization_name'] = organizationName;
    request.fields['category'] = category;
    request.fields['package_type'] = packageType;
    request.fields['import_status'] = importStatus;

    final streamedResponse = await request.send().timeout(
      Duration(seconds: 30 + (imagesBytes.length * 15)),
      onTimeout: () {
        throw Exception("Bulk upload timeout while processing ${imagesBytes.length} images.");
      },
    );

    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      final Map<String, dynamic> json = jsonDecode(response.body);
      final List rawReports = json['reports'] ?? [];

      List<InspectionReport> parsedReports = [];
      for (int i = 0; i < rawReports.length; i++) {
        final r = rawReports[i];
        final bytes = i < imagesBytes.length ? imagesBytes[i] : null;
        parsedReports.add(InspectionReport.fromJson(r, localBytes: bytes));
      }

      return {
        "batch_id": json["batch_id"],
        "organization_name": json["organization_name"],
        "total_scanned": json["total_scanned"],
        "passed_count": json["passed_count"],
        "failed_count": json["failed_count"],
        "review_count": json["review_count"],
        "overall_batch_status": json["overall_batch_status"],
        "batch_compliance_rate": json["batch_compliance_rate"],
        "reports": parsedReports,
      };
    } else {
      throw Exception("Bulk upload failed with HTTP ${response.statusCode}: ${response.body}");
    }
  }
}
