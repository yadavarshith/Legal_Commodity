import 'dart:typed_data';

class StatutoryDeclaration {
  final String fieldType; // e.g., PRODUCT_NAME, MRP, NET_QUANTITY
  final String rawText;
  final String normalizedValue;
  final double confidence;
  final String status; // EXTRACTED, MISSING, IMPROPER_FORMAT
  final List<double>? bbox;

  StatutoryDeclaration({
    required this.fieldType,
    required this.rawText,
    required this.normalizedValue,
    required this.confidence,
    required this.status,
    this.bbox,
  });

  factory StatutoryDeclaration.fromJson(Map<String, dynamic> json) {
    return StatutoryDeclaration(
      fieldType: json['type'] ?? json['field_type'] ?? 'UNKNOWN',
      rawText: json['raw_text'] ?? '',
      normalizedValue: json['normalized_value'] ?? json['value'] ?? '',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.85,
      status: json['status'] ?? 'EXTRACTED',
      bbox: (json['bbox'] as List?)?.map((e) => (e as num).toDouble()).toList(),
    );
  }

  Map<String, dynamic> toJson() => {
        'type': fieldType,
        'raw_text': rawText,
        'normalized_value': normalizedValue,
        'confidence': confidence,
        'status': status,
        'bbox': bbox,
      };

  String get displayName {
    switch (fieldType.toUpperCase()) {
      case 'PRODUCT_NAME':
        return '📦 Product Generic Name';
      case 'MANUFACTURER':
        return '🏭 Name & Address of Manufacturer / Packer';
      case 'NET_QUANTITY':
        return '⚖️ Net Quantity & Standard Unit';
      case 'MRP':
      case 'MAXIMUM_RETAIL_PRICE':
        return '💰 Maximum Retail Price (MRP incl. taxes)';
      case 'MANUFACTURE_OR_PACK_DATE':
      case 'MFG_DATE':
        return '📅 Month & Year of Manufacture / Packing';
      case 'BEST_BEFORE_OR_USE_BY':
      case 'EXPIRY_DATE':
        return '⏳ Expiry / Best Before Period';
      case 'CONSUMER_CARE':
        return '📞 Consumer Care Cell Contact & Email';
      case 'COUNTRY_OF_ORIGIN':
        return '🌍 Country of Origin (Imports)';
      case 'UNIT_SALE_PRICE':
        return '🏷️ Unit Sale Price (USP)';
      default:
        return fieldType;
    }
  }
}

class RuleFinding {
  final String ruleId; // e.g. Rule 6(1)(a)
  final String clauseReference;
  final String status; // PASS, FAIL, NON_COMPLIANT, MISSING
  final String severity; // CRITICAL, HIGH, MEDIUM, LOW
  final String description;
  final double confidence;

  RuleFinding({
    required this.ruleId,
    required this.clauseReference,
    required this.status,
    required this.severity,
    required this.description,
    required this.confidence,
  });

  factory RuleFinding.fromJson(Map<String, dynamic> json) {
    return RuleFinding(
      ruleId: json['rule_id'] ?? 'RULE-6',
      clauseReference: json['clause_reference'] ?? 'PCR Rule 6(1)',
      status: json['status'] ?? 'PASS',
      severity: json['severity'] ?? 'HIGH',
      description: json['description'] ?? '',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.90,
    );
  }

  Map<String, dynamic> toJson() => {
        'rule_id': ruleId,
        'clause_reference': clauseReference,
        'status': status,
        'severity': severity,
        'description': description,
        'confidence': confidence,
      };
}

class InspectionReport {
  final String inspectionId;
  final String organizationName;
  final DateTime timestamp;
  final String imagePath;
  final Uint8List? imageBytes;
  final String? imageUrl;
  final String? annotatedImageUrl;
  final String category;
  final String packageType;
  final String importStatus;
  final String overallStatus; // APPROVED, REJECTED, REVIEW
  final String verdictTitle;
  final String verdictBadge;
  final String verdictSummary;
  final List<Map<String, dynamic>> failureJustifications;
  final List<Map<String, dynamic>> annotatedBboxes;
  final List<StatutoryDeclaration> declarations;
  final List<RuleFinding> findings;
  final List<Map<String, dynamic>> rawOcrBlocks;
  final double complianceScore; // 0 to 100%
  final String? inspectorNotes;

  InspectionReport({
    required this.inspectionId,
    this.organizationName = "General Public / Retail Audit",
    required this.timestamp,
    required this.imagePath,
    this.imageBytes,
    this.imageUrl,
    this.annotatedImageUrl,
    required this.category,
    required this.packageType,
    required this.importStatus,
    required this.overallStatus,
    required this.verdictTitle,
    required this.verdictBadge,
    required this.verdictSummary,
    required this.failureJustifications,
    required this.annotatedBboxes,
    required this.declarations,
    required this.findings,
    required this.rawOcrBlocks,
    required this.complianceScore,
    this.inspectorNotes,
  });

  factory InspectionReport.fromJson(
    Map<String, dynamic> json, {
    String localPath = '',
    Uint8List? localBytes,
  }) {
    final decls = (json['declarations'] as List? ?? [])
        .map((d) => StatutoryDeclaration.fromJson(d))
        .toList();
    final fds = (json['findings'] as List? ?? [])
        .map((f) => RuleFinding.fromJson(f))
        .toList();
    final ocr = (json['ocr_results'] as List? ?? []).cast<Map<String, dynamic>>();

    final passCount = fds.where((f) => f.status.toUpperCase() == 'PASS').length;
    final score = (json['compliance_score'] as num?)?.toDouble() ??
        (fds.isNotEmpty ? (passCount / fds.length) * 100 : 85.0);

    final status = json['overall_status'] ?? 'REVIEW';
    final title = json['verdict_title'] ??
        (status == 'APPROVED'
            ? 'GOOD PRODUCT (COMPLIANT)'
            : (status == 'REJECTED' ? 'BAD PRODUCT (NON-COMPLIANT)' : 'NEEDS ENFORCEMENT REVIEW'));

    return InspectionReport(
      inspectionId: json['inspection_id'] ?? 'INS-${DateTime.now().millisecondsSinceEpoch}',
      organizationName: json['organization_name'] ?? 'General Public / Retail Audit',
      timestamp: DateTime.now(),
      imagePath: localPath,
      imageBytes: localBytes,
      imageUrl: json['image_url'],
      annotatedImageUrl: json['annotated_image_url'],
      category: json['context']?['category'] ?? 'all',
      packageType: json['context']?['package_type'] ?? 'pre-packaged',
      importStatus: json['context']?['import_status'] ?? 'domestic',
      overallStatus: status,
      verdictTitle: title,
      verdictBadge: json['verdict_badge'] ?? (status == 'APPROVED' ? 'PASS' : (status == 'REJECTED' ? 'FAIL' : 'REVIEW')),
      verdictSummary: json['verdict_summary'] ?? '',
      failureJustifications: (json['failure_justifications'] as List? ?? []).cast<Map<String, dynamic>>(),
      annotatedBboxes: (json['annotated_bboxes'] as List? ?? []).cast<Map<String, dynamic>>(),
      declarations: decls,
      findings: fds,
      rawOcrBlocks: ocr,
      complianceScore: score,
    );
  }

  Map<String, dynamic> toJson() => {
        'inspection_id': inspectionId,
        'organization_name': organizationName,
        'timestamp': timestamp.toIso8601String(),
        'image_path': imagePath,
        'image_url': imageUrl,
        'annotated_image_url': annotatedImageUrl,
        'category': category,
        'package_type': packageType,
        'import_status': importStatus,
        'overall_status': overallStatus,
        'verdict_title': verdictTitle,
        'verdict_badge': verdictBadge,
        'verdict_summary': verdictSummary,
        'failure_justifications': failureJustifications,
        'annotated_bboxes': annotatedBboxes,
        'declarations': declarations.map((d) => d.toJson()).toList(),
        'findings': findings.map((f) => f.toJson()).toList(),
        'raw_ocr_blocks': rawOcrBlocks,
        'compliance_score': complianceScore,
        'inspector_notes': inspectorNotes,
      };
}
