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
  /// **'Note saved. AI processing runs when you create a practice paper.'**
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

  /// Note status: uploaded, waiting for paper creation
  ///
  /// In en, this message translates to:
  /// **'Saved (not processed yet)'**
  String get notesStatusUploaded;

  /// Note status: processing (extract/OCR + AI)
  ///
  /// In en, this message translates to:
  /// **'Processing notes…'**
  String get notesStatusProcessing;

  /// Note status: ready
  ///
  /// In en, this message translates to:
  /// **'Ready'**
  String get notesStatusReady;

  /// Note status: failed
  ///
  /// In en, this message translates to:
  /// **'Failed'**
  String get notesStatusFailed;

  /// Retry note processing button
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get notesRetryProcess;

  /// Internal/admin process label (hidden from student flow)
  ///
  /// In en, this message translates to:
  /// **'Process notes'**
  String get noteStartProcess;

  /// Hint shown on uploaded note before processing
  ///
  /// In en, this message translates to:
  /// **'Uploaded. Create a practice test from this topic to run AI and generate questions.'**
  String get noteProcessHint;

  /// Status hint when note is uploaded but not processed
  ///
  /// In en, this message translates to:
  /// **'Waiting for practice test — AI runs when you create a test from the topic.'**
  String get noteAwaitingProcess;

  /// Note detail screen app bar
  ///
  /// In en, this message translates to:
  /// **'Note details'**
  String get noteDetailTitle;

  /// Raw PDF text section title
  ///
  /// In en, this message translates to:
  /// **'Extracted from PDF'**
  String get noteRawExtractTitle;

  /// Raw PDF text section subtitle
  ///
  /// In en, this message translates to:
  /// **'Exact text pulled from your PDF (before AI cleanup).'**
  String get noteRawExtractSubtitle;

  /// Canonical English section title
  ///
  /// In en, this message translates to:
  /// **'English (AI cleaned)'**
  String get noteCanonicalTitle;

  /// Canonical English section subtitle
  ///
  /// In en, this message translates to:
  /// **'Cleaned/translated study content used for question papers later.'**
  String get noteCanonicalSubtitle;

  /// Shown when extract/canonical text is missing
  ///
  /// In en, this message translates to:
  /// **'Not processed yet. Create a practice test from the topic to run AI.'**
  String get noteContentEmpty;

  /// Generate MCQ paper from ready note
  ///
  /// In en, this message translates to:
  /// **'Create practice paper'**
  String get paperCreateCta;

  /// Shown while MCQ paper is generating
  ///
  /// In en, this message translates to:
  /// **'Generating paper…'**
  String get paperGenerating;

  /// Language chooser dialog title
  ///
  /// In en, this message translates to:
  /// **'Paper language'**
  String get paperLanguageTitle;

  /// Language chooser dialog body
  ///
  /// In en, this message translates to:
  /// **'Choose language for this practice paper. We’ll remember it for next time.'**
  String get paperLanguageSubtitle;

  /// English language option
  ///
  /// In en, this message translates to:
  /// **'English'**
  String get paperLanguageEnglish;

  /// Hindi language option
  ///
  /// In en, this message translates to:
  /// **'Hindi'**
  String get paperLanguageHindi;

  /// Paper detail app bar
  ///
  /// In en, this message translates to:
  /// **'Practice paper'**
  String get paperDetailTitle;

  /// Paper summary line
  ///
  /// In en, this message translates to:
  /// **'{count} questions · {language}'**
  String paperMeta(int count, String language);

  /// Hint on paper detail before Phase 5 attempt UI
  ///
  /// In en, this message translates to:
  /// **'Review questions below. Attempt & score come in the next phase.'**
  String get paperViewHint;

  /// Home button to open papers list
  ///
  /// In en, this message translates to:
  /// **'My practice papers'**
  String get homePapersCta;

  /// Papers / tests list app bar
  ///
  /// In en, this message translates to:
  /// **'My Tests'**
  String get papersListTitle;

  /// Empty tests / topic folders list
  ///
  /// In en, this message translates to:
  /// **'No tests yet. Create a practice test from a topic.'**
  String get papersListEmpty;

  /// Hint above attempt questions
  ///
  /// In en, this message translates to:
  /// **'Select one option for each question, then submit to see your score.'**
  String get attemptHint;

  /// Attempt progress counter
  ///
  /// In en, this message translates to:
  /// **'Answered {answered} of {total}'**
  String attemptProgress(int answered, int total);

  /// Validation when submit with missing answers
  ///
  /// In en, this message translates to:
  /// **'Answer every question before submitting.'**
  String get attemptAnswerAll;

  /// Submit attempt button
  ///
  /// In en, this message translates to:
  /// **'Submit answers'**
  String get attemptSubmit;

  /// Empty paper attempt state
  ///
  /// In en, this message translates to:
  /// **'This paper has no questions.'**
  String get attemptNoQuestions;

  /// Score screen app bar
  ///
  /// In en, this message translates to:
  /// **'Your score'**
  String get attemptScoreTitle;

  /// Big score percent
  ///
  /// In en, this message translates to:
  /// **'{percent}%'**
  String attemptScoreHeadline(int percent);

  /// Score fraction line
  ///
  /// In en, this message translates to:
  /// **'{correct} of {total} correct'**
  String attemptScoreMeta(int correct, int total);

  /// Review section heading
  ///
  /// In en, this message translates to:
  /// **'Review'**
  String get attemptReviewTitle;

  /// Back to papers list
  ///
  /// In en, this message translates to:
  /// **'Papers'**
  String get attemptBackToPapers;

  /// Retry same paper
  ///
  /// In en, this message translates to:
  /// **'Try again'**
  String get attemptRetry;

  /// Generic cancel
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// Setup exam app bar
  ///
  /// In en, this message translates to:
  /// **'Your exam'**
  String get setupExamTitle;

  /// Setup exam headline
  ///
  /// In en, this message translates to:
  /// **'What exam are you preparing for?'**
  String get setupExamHeadline;

  /// Setup exam subtitle
  ///
  /// In en, this message translates to:
  /// **'We’ll create a folder for this exam. You can add more exams later.'**
  String get setupExamSubtitle;

  /// Exam name field label
  ///
  /// In en, this message translates to:
  /// **'Exam name'**
  String get setupExamFieldLabel;

  /// Exam name field hint
  ///
  /// In en, this message translates to:
  /// **'e.g. UPSC Prelims, State PSC'**
  String get setupExamFieldHint;

  /// Validation when exam name empty
  ///
  /// In en, this message translates to:
  /// **'Enter an exam name to continue.'**
  String get setupExamRequired;

  /// Setup continue button
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get setupExamContinue;

  /// Home button to exams
  ///
  /// In en, this message translates to:
  /// **'My exams'**
  String get homeExamsCta;

  /// Exams list app bar
  ///
  /// In en, this message translates to:
  /// **'My Exams'**
  String get examsListTitle;

  /// Empty exams list
  ///
  /// In en, this message translates to:
  /// **'No exams yet. Add the exam you are preparing for.'**
  String get examsListEmpty;

  /// FAB add exam
  ///
  /// In en, this message translates to:
  /// **'Add exam'**
  String get examsAddCta;

  /// Add exam dialog title
  ///
  /// In en, this message translates to:
  /// **'Add exam'**
  String get examsAddTitle;

  /// Confirm add exam
  ///
  /// In en, this message translates to:
  /// **'Add'**
  String get examsAddConfirm;

  /// Exam list subtitle
  ///
  /// In en, this message translates to:
  /// **'{count} topics'**
  String examsBatchCount(int count);

  /// Fallback exam detail title
  ///
  /// In en, this message translates to:
  /// **'Exam'**
  String get examDetailTitle;

  /// Topics section title
  ///
  /// In en, this message translates to:
  /// **'Topics'**
  String get batchListTitle;

  /// Empty topics
  ///
  /// In en, this message translates to:
  /// **'No topics yet. Create one (e.g. Constitution) and upload notes into it.'**
  String get batchListEmpty;

  /// Create topic FAB
  ///
  /// In en, this message translates to:
  /// **'New Topic'**
  String get batchCreateCta;

  /// Create topic dialog title
  ///
  /// In en, this message translates to:
  /// **'New Topic'**
  String get batchCreateTitle;

  /// Confirm create topic
  ///
  /// In en, this message translates to:
  /// **'Create'**
  String get batchCreateConfirm;

  /// Topic name field
  ///
  /// In en, this message translates to:
  /// **'Topic name'**
  String get batchNameLabel;

  /// Topic name hint
  ///
  /// In en, this message translates to:
  /// **'e.g. Polity, Week 1'**
  String get batchNameHint;

  /// Fallback post-test nudge (unused in UI)
  ///
  /// In en, this message translates to:
  /// **'A test was already created from a topic. Prefer creating a new topic for new uploads.'**
  String get batchSuggestNew;

  /// Topic list subtitle
  ///
  /// In en, this message translates to:
  /// **'{notes} notes'**
  String batchMeta(int notes);

  /// Topic has paper label (unused)
  ///
  /// In en, this message translates to:
  /// **'test created'**
  String get batchHasPaper;

  /// Topic no paper label (unused)
  ///
  /// In en, this message translates to:
  /// **'no test yet'**
  String get batchNoPaper;

  /// Fallback topic title
  ///
  /// In en, this message translates to:
  /// **'Topic'**
  String get batchDetailTitle;

  /// Notes section in topic
  ///
  /// In en, this message translates to:
  /// **'Notes'**
  String get batchNotesTitle;

  /// Empty topic notes
  ///
  /// In en, this message translates to:
  /// **'Upload PDF notes into this topic.'**
  String get batchNotesEmpty;

  /// Generate paper from topic
  ///
  /// In en, this message translates to:
  /// **'Create Test'**
  String get batchCreateTestCta;

  /// Hint under create test (unused)
  ///
  /// In en, this message translates to:
  /// **'Processes any unprocessed notes in this topic, then creates a test from all notes.'**
  String get batchCreateTestHint;

  /// Multi-topic select hint on exam detail
  ///
  /// In en, this message translates to:
  /// **'Select topics to combine into one test.'**
  String get topicsSelectHint;

  /// Generate paper from selected topics
  ///
  /// In en, this message translates to:
  /// **'Create Test'**
  String get topicsCreateTestCta;

  /// Generate from N selected topics
  ///
  /// In en, this message translates to:
  /// **'Create Test ({count})'**
  String topicsCreateTestSelected(int count);

  /// Snack when no topics selected
  ///
  /// In en, this message translates to:
  /// **'Select at least one topic'**
  String get topicsSelectNone;

  /// Remaining monthly paper creates under create CTA
  ///
  /// In en, this message translates to:
  /// **'{remaining} of {limit} tests left this month'**
  String paperQuotaRemaining(int remaining, int limit);

  /// Shown when monthly create quota is used up
  ///
  /// In en, this message translates to:
  /// **'No tests left this month. Resets next month.'**
  String get paperQuotaExhausted;

  /// Home stats card label for remaining creates
  ///
  /// In en, this message translates to:
  /// **'Tests Left'**
  String get homeStatTestsLeft;
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
