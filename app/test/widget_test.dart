import 'package:flutter_test/flutter_test.dart';
import 'package:labelsure/main.dart';

void main() {
  testWidgets('LabelSure app smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const LabelSureApp());
    expect(find.text('APEX — LabelSure'), findsOneWidget);
  });
}
