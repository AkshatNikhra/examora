import 'dart:async';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_failure.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/notes_repository.dart';
import 'open_note_pdf.dart';

final notesListProvider = FutureProvider.autoDispose<List<NoteItem>>((ref) {
  return ref.watch(notesRepositoryProvider).listNotes();
});

class NotesListScreen extends ConsumerStatefulWidget {
  const NotesListScreen({super.key});

  @override
  ConsumerState<NotesListScreen> createState() => _NotesListScreenState();
}

class _NotesListScreenState extends ConsumerState<NotesListScreen> {
  bool _uploading = false;
  double? _progress;
  Timer? _pollTimer;

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  void _syncPolling(List<NoteItem>? items) {
    final needsPoll =
        items?.any((n) => n.status == 'processing') ?? false;
    if (needsPoll) {
      _pollTimer ??= Timer.periodic(const Duration(seconds: 2), (_) {
        if (!mounted) return;
        ref.invalidate(notesListProvider);
      });
    } else {
      _pollTimer?.cancel();
      _pollTimer = null;
    }
  }

  Future<void> _pickAndUpload() async {
    final l10n = AppLocalizations.of(context);
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf'],
      withData: false,
    );
    if (result == null || result.files.isEmpty) return;

    final file = result.files.single;
    final path = file.path;
    if (path == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.notesPickFailed)),
      );
      return;
    }

    setState(() {
      _uploading = true;
      _progress = 0;
    });

    try {
      await ref.read(notesRepositoryProvider).uploadPdf(
            filePath: path,
            fileName: file.name,
            title: file.name,
            onProgress: (sent, total) {
              if (!mounted || total <= 0) return;
              setState(() => _progress = sent / total);
            },
          );
      ref.invalidate(notesListProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.notesUploadSuccess)),
      );
    } catch (error) {
      if (!mounted) return;
      final message = error is AppFailure ? error.message : l10n.genericError;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${l10n.notesUploadFailed}: $message')),
      );
    } finally {
      if (mounted) {
        setState(() {
          _uploading = false;
          _progress = null;
        });
      }
    }
  }

  String _statusLabel(AppLocalizations l10n, String status) {
    return switch (status) {
      'processing' => l10n.notesStatusProcessing,
      'ready' => l10n.notesStatusReady,
      'failed' => l10n.notesStatusFailed,
      _ => l10n.notesStatusUploaded,
    };
  }

  Color _statusColor(ColorScheme scheme, String status) {
    return switch (status) {
      'processing' => scheme.tertiary,
      'ready' => scheme.primary,
      'failed' => scheme.error,
      _ => scheme.outline,
    };
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final notes = ref.watch(notesListProvider);
    final theme = Theme.of(context);

    ref.listen(notesListProvider, (_, next) {
      next.whenData(_syncPolling);
    });

    return Scaffold(
      appBar: AppBar(title: Text(l10n.notesTitle)),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _uploading ? null : _pickAndUpload,
        icon: const Icon(Icons.upload_file),
        label: Text(l10n.notesUploadCta),
      ),
      body: SafeArea(
        child: Column(
          children: [
            if (_uploading) ...[
              LinearProgressIndicator(value: _progress),
              Padding(
                padding: const EdgeInsets.all(12),
                child: Text(l10n.notesUploading),
              ),
            ],
            Expanded(
              child: notes.when(
                data: (items) {
                  _syncPolling(items);
                  if (items.isEmpty) {
                    return Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Text(
                          l10n.notesEmpty,
                          textAlign: TextAlign.center,
                          style: theme.textTheme.bodyLarge?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ),
                    );
                  }
                  return RefreshIndicator(
                    onRefresh: () async {
                      ref.invalidate(notesListProvider);
                      await ref.read(notesListProvider.future);
                    },
                    child: ListView.separated(
                      padding: const EdgeInsets.fromLTRB(16, 8, 16, 88),
                      itemCount: items.length,
                      separatorBuilder: (_, _) => const SizedBox(height: 8),
                      itemBuilder: (context, index) {
                        final note = items[index];
                        final statusColor =
                            _statusColor(theme.colorScheme, note.status);
                        return Card(
                          child: ListTile(
                            onTap: () {
                              openNoteInPdfApp(
                                context,
                                ref,
                                noteId: note.id,
                                title: note.title,
                              );
                            },
                            title: Text(note.title),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const SizedBox(height: 4),
                                Text(
                                  '${_statusLabel(l10n, note.status)} · ${note.language}',
                                ),
                                if (note.status == 'failed' &&
                                    (note.errorMessage?.isNotEmpty ?? false))
                                  Padding(
                                    padding: const EdgeInsets.only(top: 4),
                                    child: Text(
                                      note.errorMessage!,
                                      maxLines: 2,
                                      overflow: TextOverflow.ellipsis,
                                      style: theme.textTheme.bodySmall?.copyWith(
                                        color: theme.colorScheme.error,
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                            isThreeLine: note.status == 'failed',
                            trailing: Text(
                              _shortDate(note.createdAt),
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: statusColor,
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                  );
                },
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (error, _) => Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Text(
                      error is AppFailure
                          ? error.message
                          : l10n.genericError,
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _shortDate(DateTime value) {
    final local = value.toLocal();
    return '${local.year}-${local.month.toString().padLeft(2, '0')}-${local.day.toString().padLeft(2, '0')}';
  }
}
