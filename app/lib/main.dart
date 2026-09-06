import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(title: 'LabelSure Inspector', home: const InspectionScreen());
  }
}

class InspectionScreen extends StatefulWidget {
  const InspectionScreen({super.key});

  @override
  State<InspectionScreen> createState() => _InspectionScreenState();
}

class _InspectionScreenState extends State<InspectionScreen> {
  final ImagePicker _picker = ImagePicker();
  XFile? _frontImage;
  XFile? _backImage;
  String _result = "Press submit to inspect";

  Future<void> _pickImage(bool front) async {
    final XFile? image = await _picker.pickImage(source: ImageSource.camera);
    if (image != null) {
      setState(() {
        if (front) _frontImage = image; else _backImage = image;
      });
    }
  }

  Future<void> _submit() async {
    setState(() => _result = "Inspecting...");

    // Note: use 10.0.2.2 for Android emulator
    final url = Uri.parse('http://10.0.2.2:8000/inspections');
    try {
      final response = await http.post(
        url,
        headers: {'X-API-Key': 'dev-key', 'Content-Type': 'application/json'},
      );
      if (response.statusCode == 200) {
        setState(() => _result = "Result: ${response.body}");
      } else {
        setState(() => _result = "Error: ${response.statusCode} - ${response.body}");
      }
    } catch (e) {
      setState(() => _result = "Exception: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("LabelSure")),
      body: Column(
        children: [
          ElevatedButton(onPressed: () => _pickImage(true), child: Text(_frontImage == null ? "Capture Front" : "Front Captured")),
          ElevatedButton(onPressed: () => _pickImage(false), child: Text(_backImage == null ? "Capture Back" : "Back Captured")),
          ElevatedButton(onPressed: _submit, child: const Text("Submit Inspection")),
          Expanded(child: SingleChildScrollView(child: Text(_result))),
        ],
      ),
    );
  }
}
