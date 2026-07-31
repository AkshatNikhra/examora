import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[Locale('en')];

  /// Application title
  ///
  /// In en, this message translates to:
  /// **'Examora'**
  String get appTitle;

  /// Home screen headline
  ///
  /// In en, this message translates to:
  /// **'Turn your notes into practice papers'**
  String get homeHeadline;

  /// Home screen supporting text
  ///
  /// In en, this message translates to:
  /// **'Upload study notes and generate MCQ question papers with AI.'**
  String get homeSubtitle;

  /// Primary home CTA (placeholder for later upload flow)
  ///
  /// In en, this message translates to:
  /// **'Get started'**
  String get homeCta;

  /// Shown when /health succeeds
  ///
  /// In en, this message translates to:
  /// **'Backend connected'**
  String get backendStatusOk;

  /// Shown when /health fails
  ///
  /// In en, this message translates to:
  /// **'Backend unreachable'**
  String get backendStatusFail;

  /// Generic error message
  ///
  /// In en, this message translates to:
  /// **'Something went wrong. Please try again.'**
  String get genericError;

  /// Phone login headline
  ///
  /// In en, this message translates to:
  /// **'Sign in with your phone'**
  String get loginHeadline;

  /// Phone login supporting text
  ///
  /// In en, this message translates to:
  /// **'We\'ll send a one-time code to verify your number.'**
  String get loginSubtitle;

  /// Phone input label
  ///
  /// In en, this message translates to:
  /// **'Mobile number'**
  String get phoneLabel;

  /// Phone validation error
  ///
  /// In en, this message translates to:
  /// **'Enter a valid 10-digit Indian mobile number'**
  String get phoneInvalid;

  /// Send OTP button
  ///
  /// In en, this message translates to:
  /// **'Send OTP'**
  String get sendOtp;

  /// OTP screen app bar
  ///
  /// In en, this message translates to:
  /// **'Verify OTP'**
  String get otpTitle;

  /// OTP screen headline
  ///
  /// In en, this message translates to:
  /// **'Enter verification code'**
  String get otpHeadline;

  /// OTP screen subtitle with phone
  ///
  /// In en, this message translates to:
  /// **'Code sent to {phone}'**
  String otpSubtitle(String phone);

  /// OTP input label
  ///
  /// In en, this message translates to:
  /// **'6-digit OTP'**
  String get otpLabel;

  /// OTP validation error
  ///
  /// In en, this message translates to:
  /// **'Enter the 6-digit code'**
  String get otpInvalid;

  /// Verify OTP button
  ///
  /// In en, this message translates to:
  /// **'Verify & continue'**
  String get verifyOtp;

  /// Logout button
  ///
  /// In en, this message translates to:
  /// **'Log out'**
  String get logout;

  /// Shown when authenticated /me succeeds
  ///
  /// In en, this message translates to:
  /// **'Auth OK — /me: {phone}'**
  String meStatusOk(String phone);

  /// Shown when authenticated /me fails
  ///
  /// In en, this message translates to:
  /// **'Auth /me failed'**
  String get meStatusFail;

  /// Shown while /me is loading
  ///
  /// In en, this message translates to:
  /// **'Checking /me…'**
  String get meStatusLoading;

  /// Notes list screen title
  ///
  /// In en, this message translates to:
  /// **'My notes'**
  String get notesTitle;

  /// Empty notes list message
  ///
  /// In en, this message translates to:
  /// **'No notes yet. Upload a PDF to get started.'**
  String get notesEmpty;

  /// Upload FAB label
  ///
  /// In en, this message translates to:
  /// **'Upload PDF'**
  String get notesUploadCta;

  /// Upload in progress label
  ///
  /// In en, this message translates to:
  /// **'Uploading PDF…'**
  String get notesUploading;

  /// Upload success snackbar
  ///
  /// In en, this message translates to:
  /// **'Note uploaded successfully'**
  String get notesUploadSuccess;

  /// Upload failure snackbar prefix
  ///
  /// In en, this message translates to:
  /// **'Upload failed'**
  String get notesUploadFailed;

  /// File picker path missing
  ///
  /// In en, this message translates to:
  /// **'Could not read the selected file'**
  String get notesPickFailed;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
