import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/inspection_model.dart';

class ApiService {
  static String baseUrl = 'http://127.0.0.1:8000'; // Default host

  static void setBaseUrl(String url) {
    if (url.endsWith('/')) {
      baseUrl = url.substring(0, url.length - 1);
    } else {
      baseUrl = url;
    }
  }

  /// Sends uploaded image to backend /upload-and-scan endpoint.
  /// Works across both Mobile (Android/iOS) and Web (Chrome) platforms.
  /// Never returns fake or static fallback data. Surfacing explicit exceptions on failure.
  static Future<InspectionReport> scanPackageLabel({
    required Uint8List imageBytes,
    required String filename,
    String localPath = '',
    String category = 'all',
    String packageType = 'pre-packaged',
    String importStatus = 'domestic',
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

    final streamedResponse = await request.send().timeout(
      const Duration(seconds: 25),
      onTimeout: () {
        throw Exception("Server timeout (25s) while running OCR & Rule Engine at $baseUrl");
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
}
