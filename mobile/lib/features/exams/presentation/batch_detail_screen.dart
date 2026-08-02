import 'dart:async';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_theme.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/exams_repository.dart';
import '../../../repositories/notes_repository.dart';
import '../../../repositories/papers_repository.dart';
import 'exam_detail_screen.dart';

final batchDetailProvider =
    FutureProvider.autoDispose.family<BatchItem, String>((ref, batchId) {
  return ref.watch(examsRepositoryProvider).getBatch(batchId);
});

final batchNotesProvider =
    FutureProvider.autoDispose.family<List<NoteItem>, String>((ref, batchId) {
  return ref.watch(examsRepositoryProvider).listBatchNotes(batchId);
});

class BatchDetailScreen extends ConsumerStatefulWidget {
  const BatchDetailScreen({super.key, required this.batchId});

  final String batchId;

  @override
  ConsumerState<BatchDetailScreen> createState() => _BatchDetailScreenState();
}

class _BatchDetailScreenState extends ConsumerState<BatchDetailScreen> {
  bool _uploading = false;
  bool _generating = false;
  double? _progress;
  Timer? _pollTimer;

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  void _syncPolling(List<NoteItem>? items) {
    final needsPoll = items?.any((n) => n.status == 'processing') ?? false;
    if (needsPoll) {
      _pollTimer ??= Timer.periodic(const Duration(seconds: 2), (_) {
        if (!mounted) return;
        ref.invalidate(batchNotesProvider(widget.batchId));
        ref.invalidate(batchDetailProvider(widget.batchId));
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
            batchFolderId: widget.batchId,
            onProgress: (sent, total) {
              if (!mounted || total <= 0) return;
              setState(() => _progress = sent / total);
            },
          );
      ref.invalidate(batchNotesProvider(widget.batchId));
      ref.invalidate(batchDetailProvider(widget.batchId));
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

  Future<String?> _pickLanguage() async {
    final l10n = AppLocalizations.of(context);
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.paperLanguageTitle),
        content: Text(l10n.paperLanguageSubtitle),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, 'en'),
            child: Text(l10n.paperLanguageEnglish),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, 'hi'),
            child: Text(l10n.paperLanguageHindi),
          ),
        ],
      ),
    );
  }

  Future<void> _createTest() async {
    final l10n = AppLocalizations.of(context);
    final language = await _pickLanguage();
    if (language == null || !mounted) return;

    setState(() => _generating = true);
    try {
      final paper = await ref.read(papersRepositoryProvider).generatePaperFromBatch(
            batchId: widget.batchId,
            language: language,
          );
      ref.invalidate(batchDetailProvider(widget.batchId));
      final examId = ref.read(batchDetailProvider(widget.batchId)).valueOrNull?.examId;
      if (examId != null) {
        ref.invalidate(examBatchesProvider(examId));
        ref.invalidate(examUploadHintProvider(examId));
      }
      if (!mounted) return;
      context.push('/papers/${paper.id}');
    } catch (error) {
      if (!mounted) return;
      final message = error is AppFailure ? error.message : l10n.genericError;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    } finally {
      if (mounted) setState(() => _generating = false);
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

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final asyncBatch = ref.watch(batchDetailProvider(widget.batchId));
    final asyncNotes = ref.watch(batchNotesProvider(widget.batchId));
    _syncPolling(asyncNotes.valueOrNull);

    return Scaffold(
      backgroundColor: AppTheme.cream,
      appBar: AppBar(
        title: asyncBatch.maybeWhen(
          data: (b) => Text(
            b.name,
            style: const TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.w800,
            ),
          ),
          orElse: () => Text(
            l10n.batchDetailTitle,
            style: const TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
        titleTextStyle: const TextStyle(
          color: AppTheme.ink,
          fontSize: 26,
          fontWeight: FontWeight.w800,
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _uploading ? null : _pickAndUpload,
        child: _uploading
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : const Icon(Icons.upload_file),
      ),
      body: Column(
        children: [
          if (_progress != null)
            LinearProgressIndicator(value: _progress),
          Expanded(
            child: asyncNotes.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(
                    error is AppFailure ? error.message : l10n.genericError,
                    textAlign: TextAlign.center,
                  ),
                ),
              ),
              data: (notes) {
                return RefreshIndicator(
                  onRefresh: () async {
                    ref.invalidate(batchNotesProvider(widget.batchId));
                    ref.invalidate(batchDetailProvider(widget.batchId));
                    await ref.read(batchNotesProvider(widget.batchId).future);
                  },
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
                    children: [
                      FilledButton.icon(
                        onPressed: _generating || notes.isEmpty
                            ? null
                            : _createTest,
                        icon: _generating
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.ballot_outlined),
                        label: Text(
                          _generating
                              ? l10n.paperGenerating
                              : l10n.batchCreateTestCta,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        l10n.batchNotesTitle,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 8),
                      if (notes.isEmpty)
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 24),
                          child: Text(
                            l10n.batchNotesEmpty,
                            style: theme.textTheme.bodyLarge?.copyWith(
                              color: theme.colorScheme.onSurfaceVariant,
                            ),
                          ),
                        )
                      else
                        ...notes.map(
                          (note) => Card(
                            margin: const EdgeInsets.only(bottom: 8),
                            child: ListTile(
                              title: Text(note.title),
                              subtitle: Text(_statusLabel(l10n, note.status)),
                              trailing: const Icon(Icons.chevron_right),
                              onTap: () => context.push('/notes/${note.id}'),
                            ),
                          ),
                        ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
