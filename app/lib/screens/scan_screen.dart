import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';
import 'result_detail_screen.dart';

class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> with SingleTickerProviderStateMixin {
  final ImagePicker _picker = ImagePicker();
  XFile? _selectedFile;
  Uint8List? _imageBytes;
  bool _isScanning = false;
  bool _isLiveCameraActive = false;
  String _category = 'all';
  final String _packageType = 'pre-packaged';
  String _importStatus = 'domestic';

  late AnimationController _laserController;
  late Animation<double> _laserAnimation;

  @override
  void initState() {
    super.initState();
    _laserController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    );
    _laserAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(_laserController);
  }

  @override
  void dispose() {
    _laserController.dispose();
    super.dispose();
  }

  Future<void> _startRealtimeCameraScan() async {
    try {
      setState(() => _isLiveCameraActive = true);
      final XFile? image = await _picker.pickImage(
        source: ImageSource.camera,
        imageQuality: 95,
        preferredCameraDevice: CameraDevice.rear,
      );

      if (image != null) {
        final bytes = await image.readAsBytes();
        setState(() {
          _selectedFile = image;
          _imageBytes = bytes;
          _isLiveCameraActive = false;
        });
        // Auto trigger inspection on capture
        _executeScan();
      } else {
        setState(() => _isLiveCameraActive = false);
      }
    } catch (e) {
      setState(() => _isLiveCameraActive = false);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Camera Scanner Error: $e")),
      );
    }
  }

  Future<void> _pickGalleryImage() async {
    try {
      final XFile? image = await _picker.pickImage(source: ImageSource.gallery, imageQuality: 95);
      if (image != null) {
        final bytes = await image.readAsBytes();
        setState(() {
          _selectedFile = image;
          _imageBytes = bytes;
        });
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Failed to select gallery photo: $e")),
      );
    }
  }

  Future<void> _executeScan() async {
    if (_imageBytes == null || _selectedFile == null) return;

    setState(() {
      _isScanning = true;
    });
    _laserController.repeat(reverse: true);

    try {
      final report = await ApiService.scanPackageLabel(
        imageBytes: _imageBytes!,
        filename: _selectedFile!.name,
        localPath: kIsWeb ? '' : _selectedFile!.path,
        category: _category,
        packageType: _packageType,
        importStatus: _importStatus,
      );

      await StorageService.saveReport(report);

      _laserController.stop();
      if (!mounted) return;
      setState(() {
        _isScanning = false;
      });

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => ResultDetailScreen(report: report),
        ),
      );
    } catch (e) {
      _laserController.stop();
      if (!mounted) return;
      setState(() {
        _isScanning = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Scan Error: $e")),
      );
    }
  }

  void _showSettingsDialog() {
    final controller = TextEditingController(text: ApiService.baseUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF161E2E),
        title: const Text("Backend Server Configuration", style: TextStyle(color: Colors.white)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Set your PC's IP address on Wi-Fi (FastAPI OCR server):\n\n"
              "• Physical Phone: http://<YOUR_PC_WIFI_IP>:8000 (e.g., http://192.168.31.112:8000)\n"
              "• Android Emulator: http://10.0.2.2:8000\n"
              "• Web Browser / Local: http://127.0.0.1:8000",
              style: TextStyle(color: Colors.grey, fontSize: 12),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: controller,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: "http://192.168.31.112:8000",
                hintStyle: TextStyle(color: Colors.grey),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text("Cancel")),
          ElevatedButton(
            onPressed: () {
              ApiService.setBaseUrl(controller.text.trim());
              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text("Server URL updated: ${ApiService.baseUrl}")),
              );
            },
            child: const Text("Save"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Real-Time Label Scanner"),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_rounded, color: Colors.grey),
            onPressed: _showSettingsDialog,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Real-Time Camera Viewfinder Container
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF161E2E),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: _isScanning ? const Color(0xFF00E5FF) : const Color(0xFF1F293D),
                  width: 1.5,
                ),
              ),
              child: Column(
                children: [
                  if (_imageBytes != null)
                    Stack(
                      alignment: Alignment.center,
                      children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: Image.memory(
                            _imageBytes!,
                            height: 250,
                            width: double.infinity,
                            fit: BoxFit.contain,
                          ),
                        ),
                        // Viewfinder Framing Reticle Overlay
                        Container(
                          height: 230,
                          width: double.infinity,
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: const Color(0xFF00E5FF).withValues(alpha: 0.5),
                              width: 2,
                            ),
                          ),
                        ),
                        if (_isScanning)
                          AnimatedBuilder(
                            animation: _laserAnimation,
                            builder: (context, child) {
                              return Positioned(
                                top: _laserAnimation.value * 230,
                                left: 0,
                                right: 0,
                                child: Container(
                                  height: 3,
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF00E5FF),
                                    boxShadow: [
                                      BoxShadow(
                                        color: const Color(0xFF00E5FF).withValues(alpha: 0.8),
                                        blurRadius: 10,
                                        spreadRadius: 2,
                                      ),
                                    ],
                                  ),
                                ),
                              );
                            },
                          ),
                      ],
                    )
                  else
                    Container(
                      height: 200,
                      decoration: BoxDecoration(
                        color: const Color(0xFF0F172A),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFF334155)),
                      ),
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                _isLiveCameraActive ? Icons.camera_rounded : Icons.qr_code_scanner_rounded,
                                size: 52,
                                color: const Color(0xFF00E5FF),
                              ),
                              const SizedBox(height: 10),
                              Text(
                                _isLiveCameraActive ? "CAMERA VIEW-FINDER ACTIVE..." : "PLACE PRODUCT LABEL IN FRONT OF CAMERA",
                                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 13),
                              ),
                              const SizedBox(height: 4),
                              const Text("Align Principal Display Panel inside frame", style: TextStyle(color: Colors.grey, fontSize: 11)),
                            ],
                          ),
                          // Target Reticle Corner Brackets
                          Positioned(
                            top: 20,
                            left: 20,
                            child: Container(width: 20, height: 20, decoration: const BoxDecoration(border: Border(top: BorderSide(color: Color(0xFF00E5FF), width: 3), left: BorderSide(color: Color(0xFF00E5FF), width: 3)))),
                          ),
                          Positioned(
                            top: 20,
                            right: 20,
                            child: Container(width: 20, height: 20, decoration: const BoxDecoration(border: Border(top: BorderSide(color: Color(0xFF00E5FF), width: 3), right: BorderSide(color: Color(0xFF00E5FF), width: 3)))),
                          ),
                          Positioned(
                            bottom: 20,
                            left: 20,
                            child: Container(width: 20, height: 20, decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: Color(0xFF00E5FF), width: 3), left: BorderSide(color: Color(0xFF00E5FF), width: 3)))),
                          ),
                          Positioned(
                            bottom: 20,
                            right: 20,
                            child: Container(width: 20, height: 20, decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: Color(0xFF00E5FF), width: 3), right: BorderSide(color: Color(0xFF00E5FF), width: 3)))),
                          ),
                        ],
                      ),
                    ),
                  const SizedBox(height: 14),

                  // Realtime Camera Scan Trigger Button
                  ElevatedButton.icon(
                    onPressed: _isScanning ? null : _startRealtimeCameraScan,
                    icon: const Icon(Icons.videocam_rounded, color: Colors.black),
                    label: const Text(
                      "📷 SCAN LIVE LABEL WITH CAMERA",
                      style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 14),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF00E5FF),
                      minimumSize: const Size(double.infinity, 48),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextButton.icon(
                    onPressed: _pickGalleryImage,
                    icon: const Icon(Icons.photo_library_outlined, color: Color(0xFF10B981), size: 18),
                    label: const Text("Or select existing photo from gallery", style: TextStyle(color: Color(0xFF10B981), fontSize: 12)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 18),

            // Metadata Category Context
            const Text("Audit Context Options", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15)),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(
                color: const Color(0xFF161E2E),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFF1F293D)),
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: _category,
                  isExpanded: true,
                  dropdownColor: const Color(0xFF161E2E),
                  style: const TextStyle(color: Colors.white),
                  items: const [
                    DropdownMenuItem(value: 'all', child: Text('All Commodity Categories')),
                    DropdownMenuItem(value: 'food', child: Text('Food & Agriculture')),
                    DropdownMenuItem(value: 'cosmetics', child: Text('Cosmetics & Personal Care')),
                    DropdownMenuItem(value: 'medical', child: Text('Medical Devices / Pharma')),
                    DropdownMenuItem(value: 'electronics', child: Text('Electronics & Appliances')),
                  ],
                  onChanged: (v) => setState(() => _category = v!),
                ),
              ),
            ),
            const SizedBox(height: 10),

            Row(
              children: [
                Expanded(
                  child: FilterChip(
                    label: const Text("Domestic Product"),
                    selected: _importStatus == 'domestic',
                    onSelected: (selected) => setState(() => _importStatus = 'domestic'),
                    selectedColor: const Color(0xFF00E5FF).withValues(alpha: 0.2),
                    checkmarkColor: const Color(0xFF00E5FF),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: FilterChip(
                    label: const Text("Imported Product"),
                    selected: _importStatus == 'imported',
                    onSelected: (selected) => setState(() => _importStatus = 'imported'),
                    selectedColor: const Color(0xFF10B981).withValues(alpha: 0.2),
                    checkmarkColor: const Color(0xFF10B981),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Execute Inspection Action Button
            if (_imageBytes != null)
              ElevatedButton.icon(
                onPressed: _isScanning ? null : _executeScan,
                icon: _isScanning
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black),
                      )
                    : const Icon(Icons.bolt_rounded, color: Colors.black),
                label: Text(
                  _isScanning ? "EXTRACTING OCR & VALIDATING RULES..." : "⚡ RUN LEGAL METROLOGY INSPECTION",
                  style: const TextStyle(color: Colors.black, fontWeight: FontWeight.bold, fontSize: 15),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF10B981),
                  minimumSize: const Size(double.infinity, 52),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
