import 'package:flutter/material.dart';
import '../models/rule_model.dart';

class RulesLibraryScreen extends StatefulWidget {
  const RulesLibraryScreen({super.key});

  @override
  State<RulesLibraryScreen> createState() => _RulesLibraryScreenState();
}

class _RulesLibraryScreenState extends State<RulesLibraryScreen> {
  String _searchQuery = '';

  @override
  Widget build(BuildContext context) {
    final rules = PCRRule.defaultRules.where((r) {
      if (_searchQuery.isEmpty) return true;
      final q = _searchQuery.toLowerCase();
      return r.ruleId.toLowerCase().contains(q) ||
          r.title.toLowerCase().contains(q) ||
          r.clauseReference.toLowerCase().contains(q) ||
          r.requirement.toLowerCase().contains(q);
    }).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text("PCR 2011 Rules Reference Library"),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              onChanged: (q) => setState(() => _searchQuery = q),
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: "Search Rule 6(1) clauses, requirements, penalties...",
                hintStyle: const TextStyle(color: Colors.grey, fontSize: 13),
                prefixIcon: const Icon(Icons.gavel_rounded, color: Color(0xFF00E5FF)),
                filled: true,
                fillColor: const Color(0xFF161E2E),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: Color(0xFF1F293D)),
                ),
              ),
            ),
          ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: rules.length,
              itemBuilder: (context, index) {
                final rule = rules[index];
                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF161E2E),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: const Color(0xFF1F293D)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: const Color(0xFF00E5FF).withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              rule.clauseReference,
                              style: const TextStyle(
                                color: Color(0xFF00E5FF),
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: Colors.red.shade900.withValues(alpha: 0.3),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              rule.severity,
                              style: const TextStyle(color: Colors.redAccent, fontSize: 10, fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        rule.title,
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        rule.requirement,
                        style: TextStyle(color: Colors.grey.shade300, fontSize: 13),
                      ),
                      const SizedBox(height: 10),
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: const Color(0xFF0F172A),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.scale_rounded, color: Color(0xFF10B981), size: 16),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                "Penalty: ${rule.penaltyClause}",
                                style: const TextStyle(color: Color(0xFF10B981), fontSize: 11),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
