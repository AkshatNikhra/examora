import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:open_filex/open_filex.dart';

import '../../../core/errors/app_failure.dart';
import '../../../repositories/notes_repository.dart';

/// Downloads the note PDF and opens it in the device’s preferred PDF app.
Future<void> openNoteInPdfApp(
  BuildContext context,
  WidgetRef ref, {
  required String noteId,
  required String title,
}) async {
  final messenger = ScaffoldMessenger.of(context);
  messenger.showSnackBar(
    const SnackBar(
      content: Text('Opening PDF…'),
      duration: Duration(seconds: 2),
    ),
  );
  try {
    final path = await ref.read(notesRepositoryProvider).downloadNotePdfToTemp(
          noteId: noteId,
          title: title,
        );
    final result = await OpenFilex.open(path, type: 'application/pdf');
    if (!context.mounted) return;
    if (result.type != ResultType.done) {
      messenger.showSnackBar(
        SnackBar(
          content: Text(
            result.message.isNotEmpty
                ? result.message
                : 'Could not open PDF. Install a PDF viewer app.',
          ),
        ),
      );
    }
  } catch (error) {
    if (!context.mounted) return;
    final message = error is AppFailure ? error.message : error.toString();
    messenger.showSnackBar(SnackBar(content: Text(message)));
  }
}
