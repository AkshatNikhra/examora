// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Examora';

  @override
  String get homeHeadline => 'Turn your notes into practice papers';

  @override
  String get homeSubtitle =>
      'Upload study notes and generate MCQ question papers with AI.';

  @override
  String get homeCta => 'Get started';

  @override
  String get backendStatusOk => 'Backend connected';

  @override
  String get backendStatusFail => 'Backend unreachable';

  @override
  String get genericError => 'Something went wrong. Please try again.';

  @override
  String get loginHeadline => 'Sign in with your phone';

  @override
  String get loginSubtitle =>
      'We\'ll send a one-time code to verify your number.';

  @override
  String get phoneLabel => 'Mobile number';

  @override
  String get phoneInvalid => 'Enter a valid 10-digit Indian mobile number';

  @override
  String get sendOtp => 'Send OTP';

  @override
  String get otpTitle => 'Verify OTP';

  @override
  String get otpHeadline => 'Enter verification code';

  @override
  String otpSubtitle(String phone) {
    return 'Code sent to $phone';
  }

  @override
  String get otpLabel => '6-digit OTP';

  @override
  String get otpInvalid => 'Enter the 6-digit code';

  @override
  String get verifyOtp => 'Verify & continue';

  @override
  String get logout => 'Log out';

  @override
  String meStatusOk(String phone) {
    return 'Auth OK — /me: $phone';
  }

  @override
  String get meStatusFail => 'Auth /me failed';

  @override
  String get meStatusLoading => 'Checking /me…';
}
