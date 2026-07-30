import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:examora/features/auth/presentation/phone_login_screen.dart';
import 'package:examora/l10n/app_localizations.dart';

void main() {
  testWidgets('phone login screen shows sign-in headline', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
          home: PhoneLoginScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Sign in with your phone'), findsOneWidget);
    expect(find.text('Send OTP'), findsOneWidget);
  });
}
