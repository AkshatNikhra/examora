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

  @override
  String get notesTitle => 'My notes';

  @override
  String get notesEmpty => 'No notes yet. Upload a PDF to get started.';

  @override
  String get notesUploadCta => 'Upload PDF';

  @override
  String get notesUploading => 'Uploading PDF…';

  @override
  String get notesUploadSuccess =>
      'Note saved. AI processing runs when you create a practice paper.';

  @override
  String get notesUploadFailed => 'Upload failed';

  @override
  String get notesPickFailed => 'Could not read the selected file';

  @override
  String get notesStatusUploaded => 'Saved (not processed yet)';

  @override
  String get notesStatusProcessing => 'Processing…';

  @override
  String get notesStatusReady => 'Ready';

  @override
  String get notesStatusFailed => 'Failed';

  @override
  String get notesRetryProcess => 'Retry';

  @override
  String get noteStartProcess => 'Process notes';

  @override
  String get noteProcessHint =>
      'This note is saved only. Tap Process notes to run AI (uses your monthly quota later).';

  @override
  String get noteDetailTitle => 'Note details';

  @override
  String get noteRawExtractTitle => 'Extracted from PDF';

  @override
  String get noteRawExtractSubtitle =>
      'Exact text pulled from your PDF (before AI cleanup).';

  @override
  String get noteCanonicalTitle => 'English (AI cleaned)';

  @override
  String get noteCanonicalSubtitle =>
      'Cleaned/translated study content used for question papers later.';

  @override
  String get noteContentEmpty =>
      'Not processed yet. Create a practice paper to run AI on this note.';
}
