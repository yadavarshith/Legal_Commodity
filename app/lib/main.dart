import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const LabelSureApp());
}

class LabelSureApp extends StatelessWidget {
  const LabelSureApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'APEX — LabelSure',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF0B0F19),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF00E5FF),
          secondary: Color(0xFF10B981),
          surface: Color(0xFF161E2E),
        ),
      ),
      home: const WebAppHomeScreen(),
    );
  }
}

class WebAppHomeScreen extends StatefulWidget {
  const WebAppHomeScreen({super.key});

  @override
  State<WebAppHomeScreen> createState() => _WebAppHomeScreenState();
}

class _WebAppHomeScreenState extends State<WebAppHomeScreen> {
  late final WebViewController _controller;
  bool _isLoading = true;
  String _serverUrl = 'http://10.0.2.2:8000'; // Default Android Emulator host IP

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageFinished: (url) => setState(() => _isLoading = false),
          onWebResourceError: (error) {
            debugPrint("WebView error: ${error.description}");
          },
        ),
      );

    _loadApp();
  }

  void _loadApp() {
    setState(() => _isLoading = true);
    // Load local bundled web application HTML/CSS/JS assets inside APK
    _controller.loadFlutterAsset('assets/www/index.html');
  }

  void _showSettingsDialog() {
    final controller = TextEditingController(text: _serverUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF161E2E),
        title: const Text("Backend Host Settings", style: TextStyle(color: Colors.white)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Set the backend API host server URL:",
              style: TextStyle(color: Colors.grey, fontSize: 13),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: controller,
              style: const TextStyle(color: Colors.white),
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: "http://10.0.2.2:8000 or http://192.168.x.x:8000",
                hintStyle: TextStyle(color: Colors.grey),
              ),
            ),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              onPressed: () {
                final url = controller.text.trim();
                if (url.isNotEmpty) {
                  setState(() => _serverUrl = url);
                  _controller.loadRequest(Uri.parse(url));
                  Navigator.pop(ctx);
                }
              },
              icon: const Icon(Icons.public, color: Colors.black),
              label: const Text("Connect to Remote Backend Server", style: TextStyle(color: Colors.black)),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF00E5FF),
                minimumSize: const Size(double.infinity, 44),
              ),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: () {
                _loadApp();
                Navigator.pop(ctx);
              },
              icon: const Icon(Icons.phone_android, color: Color(0xFF10B981)),
              label: const Text("Load Bundled Local App", style: TextStyle(color: Colors.white)),
              style: OutlinedButton.styleFrom(
                minimumSize: const Size(double.infinity, 44),
                side: const BorderSide(color: Color(0xFF10B981)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF111827),
        elevation: 0,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: const Color(0xFF00E5FF).withOpacity(0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.verified_rounded, color: Color(0xFF00E5FF), size: 20),
            ),
            const SizedBox(width: 10),
            const Text(
              'APEX — LabelSure',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: Colors.white70),
            onPressed: () => _controller.reload(),
          ),
          IconButton(
            icon: const Icon(Icons.settings_rounded, color: Colors.white70),
            onPressed: _showSettingsDialog,
          ),
        ],
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_isLoading)
            const Center(
              child: CircularProgressIndicator(color: Color(0xFF00E5FF)),
            ),
        ],
      ),
    );
  }
}
