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
}
