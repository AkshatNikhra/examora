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
  String get notesStatusProcessing => 'Processing notes…';

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
      'Uploaded. Create a practice test from this topic to run AI and generate questions.';

  @override
  String get noteAwaitingProcess =>
      'Waiting for practice test — AI runs when you create a test from the topic.';

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
      'Not processed yet. Create a practice test from the topic to run AI.';

  @override
  String get paperCreateCta => 'Create practice paper';

  @override
  String get paperGenerating => 'Generating paper…';

  @override
  String get paperLanguageTitle => 'Paper language';

  @override
  String get paperLanguageSubtitle =>
      'Choose language for this practice paper. We’ll remember it for next time.';

  @override
  String get paperLanguageEnglish => 'English';

  @override
  String get paperLanguageHindi => 'Hindi';

  @override
  String get paperDetailTitle => 'Practice paper';

  @override
  String paperMeta(int count, String language) {
    return '$count questions · $language';
  }

  @override
  String get paperViewHint =>
      'Review questions below. Attempt & score come in the next phase.';

  @override
  String get homePapersCta => 'My practice papers';

  @override
  String get papersListTitle => 'My Tests';

  @override
  String get papersListEmpty =>
      'No tests yet. Create a practice test from a topic.';

  @override
  String get attemptHint =>
      'Select one option for each question, then submit to see your score.';

  @override
  String attemptProgress(int answered, int total) {
    return 'Answered $answered of $total';
  }

  @override
  String get attemptAnswerAll => 'Answer every question before submitting.';

  @override
  String get attemptSubmit => 'Submit answers';

  @override
  String get attemptNoQuestions => 'This paper has no questions.';

  @override
  String get attemptScoreTitle => 'Your score';

  @override
  String attemptScoreHeadline(int percent) {
    return '$percent%';
  }

  @override
  String attemptScoreMeta(int correct, int total) {
    return '$correct of $total correct';
  }

  @override
  String get attemptReviewTitle => 'Review';

  @override
  String get attemptBackToPapers => 'Papers';

  @override
  String get attemptRetry => 'Try again';

  @override
  String get cancel => 'Cancel';

  @override
  String get setupExamTitle => 'Your exam';

  @override
  String get setupExamHeadline => 'What exam are you preparing for?';

  @override
  String get setupExamSubtitle =>
      'We’ll create a folder for this exam. You can add more exams later.';

  @override
  String get setupExamFieldLabel => 'Exam name';

  @override
  String get setupExamFieldHint => 'e.g. UPSC Prelims, State PSC';

  @override
  String get setupExamRequired => 'Enter an exam name to continue.';

  @override
  String get setupExamContinue => 'Continue';

  @override
  String get homeExamsCta => 'My exams';

  @override
  String get examsListTitle => 'My Exams';

  @override
  String get examsListEmpty =>
      'No exams yet. Add the exam you are preparing for.';

  @override
  String get examsAddCta => 'Add exam';

  @override
  String get examsAddTitle => 'Add exam';

  @override
  String get examsAddConfirm => 'Add';

  @override
  String examsBatchCount(int count) {
    return '$count topics';
  }

  @override
  String get examDetailTitle => 'Exam';

  @override
  String get batchListTitle => 'Topics';

  @override
  String get batchListEmpty =>
      'No topics yet. Create one (e.g. Constitution) and upload notes into it.';

  @override
  String get batchCreateCta => 'New Topic';

  @override
  String get batchCreateTitle => 'New Topic';

  @override
  String get batchCreateConfirm => 'Create';

  @override
  String get batchNameLabel => 'Topic name';

  @override
  String get batchNameHint => 'e.g. Polity, Week 1';

  @override
  String get batchSuggestNew =>
      'A test was already created from a topic. Prefer creating a new topic for new uploads.';

  @override
  String batchMeta(int notes) {
    return '$notes notes';
  }

  @override
  String get batchHasPaper => 'test created';

  @override
  String get batchNoPaper => 'no test yet';

  @override
  String get batchDetailTitle => 'Topic';

  @override
  String get batchNotesTitle => 'Notes';

  @override
  String get batchNotesEmpty => 'Upload PDF notes into this topic.';

  @override
  String get batchCreateTestCta => 'Create Test';

  @override
  String get batchCreateTestHint =>
      'Processes any unprocessed notes in this topic, then creates a test from all notes.';

  @override
  String get topicsSelectHint => 'Select topics to combine into one test.';

  @override
  String get topicsCreateTestCta => 'Create Test';

  @override
  String topicsCreateTestSelected(int count) {
    return 'Create Test ($count)';
  }

  @override
  String get topicsSelectNone => 'Select at least one topic';
}
