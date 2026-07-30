import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:examora/features/home/presentation/home_screen.dart';
import 'package:examora/main.dart';

void main() {
  testWidgets('home screen shows Examora title', (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          healthCheckProvider.overrideWith(
            (ref) async => {'status': 'ok'},
          ),
        ],
        child: const ExamoraApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Examora'), findsOneWidget);
    expect(find.textContaining('Turn your notes'), findsOneWidget);
  });
}
