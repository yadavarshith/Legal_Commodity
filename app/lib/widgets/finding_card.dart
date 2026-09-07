import 'package:flutter/material.dart';
import '../models/inspection_model.dart';
import 'status_badge.dart';

class FindingCard extends StatelessWidget {
  final RuleFinding finding;

  const FindingCard({super.key, required this.finding});

  @override
  Widget build(BuildContext context) {
    final isPass = finding.status.toUpperCase() == 'PASS';

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF161E2E),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isPass ? const Color(0xFF10B981).withValues(alpha: 0.4) : Colors.redAccent.withValues(alpha: 0.6),
          width: 1.2,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: (isPass ? const Color(0xFF10B981) : Colors.redAccent).withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: Icon(
              isPass ? Icons.check_circle_rounded : Icons.gavel_rounded,
              color: isPass ? const Color(0xFF10B981) : Colors.redAccent,
              size: 22,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: const Color(0xFF00E5FF).withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        finding.ruleId,
                        style: const TextStyle(
                          color: Color(0xFF00E5FF),
                          fontWeight: FontWeight.bold,
                          fontSize: 11,
                        ),
                      ),
                    ),
                    StatusBadge(status: finding.status, fontSize: 10),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  finding.description,
                  style: TextStyle(
                    color: isPass ? Colors.white : const Color(0xFFFCA5A5),
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                    height: 1.3,
                  ),
                ),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F172A),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: isPass ? const Color(0xFF10B981).withValues(alpha: 0.2) : Colors.redAccent.withValues(alpha: 0.3),
                    ),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(
                        Icons.balance_rounded,
                        size: 16,
                        color: isPass ? const Color(0xFF10B981) : Colors.redAccent,
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          "Statutory Authority: ${finding.clauseReference} • Severity: ${finding.severity}",
                          style: TextStyle(
                            color: Colors.grey.shade300,
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
