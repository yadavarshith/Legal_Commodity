import 'package:flutter/material.dart';

class StatusBadge extends StatelessWidget {
  final String status;
  final double fontSize;

  const StatusBadge({
    super.key,
    required this.status,
    this.fontSize = 12.0,
  });

  @override
  Widget build(BuildContext context) {
    final s = status.toUpperCase();
    final isPass = s == 'PASS' || s == 'COMPLIANT' || s == 'EXTRACTED' || s == 'APPROVED';
    final isWarning = s == 'REVIEW' || s == 'IMPROPER_FORMAT';

    Color bgColor;
    Color textColor;
    IconData icon;

    if (isPass) {
      bgColor = const Color(0xFF064E3B).withValues(alpha: 0.8);
      textColor = const Color(0xFF10B981);
      icon = Icons.check_circle_rounded;
    } else if (isWarning) {
      bgColor = const Color(0xFF78350F).withValues(alpha: 0.8);
      textColor = const Color(0xFFF59E0B);
      icon = Icons.warning_amber_rounded;
    } else {
      bgColor = const Color(0xFF7F1D1D).withValues(alpha: 0.8);
      textColor = const Color(0xFFEF4444);
      icon = Icons.cancel_rounded;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: textColor.withValues(alpha: 0.6)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: fontSize + 2, color: textColor),
          const SizedBox(width: 4),
          Text(
            s,
            style: TextStyle(
              color: textColor,
              fontWeight: FontWeight.bold,
              fontSize: fontSize,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }
}
