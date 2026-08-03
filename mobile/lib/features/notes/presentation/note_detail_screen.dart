import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/widgets/create_test_notice.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/me_repository.dart';
import '../../../repositories/notes_repository.dart';
import '../../../repositories/papers_repository.dart';
import '../../papers/presentation/papers_list_screen.dart';
import 'notes_list_screen.dart';

final noteDetailProvider =
    FutureProvider.autoDispose.family<NoteDetail, String>((ref, noteId) {
  return ref.watch(notesRepositoryProvider).getNote(noteId);
});

class NoteDetailScreen extends ConsumerStatefulWidget {
  const NoteDetailScreen({super.key, required this.noteId});

  final String noteId;

  @override
  ConsumerState<NoteDetailScreen> createState() => _NoteDetailScreenState();
}

class _NoteDetailScreenState extends ConsumerState<NoteDetailScreen> {
  Timer? _pollTimer;
  bool _generating = false;

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  void _syncPolling(NoteDetail? note) {
    final busy = note?.status == 'processing';
    if (busy) {
      _pollTimer ??= Timer.periodic(const Duration(seconds: 2), (_) {
        if (!mounted) return;
        ref.invalidate(noteDetailProvider(widget.noteId));
        ref.invalidate(notesListProvider);
      });
    } else {
      _pollTimer?.cancel();
      _pollTimer = null;
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

  Future<void> _createPaper() async {
    if (_generating) return;
    final l10n = AppLocalizations.of(context);

    setState(() => _generating = true);
    try {
      final proceed = await showCreateTestNoticesIfNeeded(
        context,
        quota: ref.read(homeSummaryProvider).valueOrNull?.paperQuota,
      );
      if (!proceed || !mounted) return;

      final language = await _pickLanguage();
      if (language == null || !mounted) return;

      await ref.read(papersRepositoryProvider).generatePaper(
            noteId: widget.noteId,
            language: language,
          );
      ref.invalidate(homeSummaryProvider);
      ref.invalidate(testTopicFoldersProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.createTestReadyGoToTests)),
      );
      context.go('/app/tests');
    } catch (error) {
      if (!mounted) return;
      final message = error is AppFailure ? error.message : l10n.genericError;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    } finally {
      if (mounted) setState(() => _generating = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final asyncNote = ref.watch(noteDetailProvider(widget.noteId));
    final quota = ref.watch(homeSummaryProvider).valueOrNull?.paperQuota;
    final quotaExhausted = quota?.isExhausted ?? false;

    ref.listen(noteDetailProvider(widget.noteId), (_, next) {
      next.whenData(_syncPolling);
    });

    return Scaffold(
      appBar: AppBar(title: Text(l10n.noteDetailTitle)),
      body: asyncNote.when(
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
        data: (note) {
          _syncPolling(note);
          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(noteDetailProvider(widget.noteId));
              ref.invalidate(homeSummaryProvider);
              await ref.read(noteDetailProvider(widget.noteId).future);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
              children: [
                Text(note.title, style: theme.textTheme.titleLarge),
                const SizedBox(height: 8),
                Text(
                  '${_statusLabel(l10n, note.status)}'
                  '${note.sourceLanguage != null ? ' · detected: ${note.sourceLanguage}' : ''}',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                if (note.status == 'uploaded') ...[
                  const SizedBox(height: 16),
                  Text(
                    l10n.noteAwaitingProcess,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
                if (note.status == 'failed') ...[
                  const SizedBox(height: 12),
                  Text(
                    note.errorMessage ?? l10n.genericError,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.error,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    l10n.noteProcessHint,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
                if (note.status == 'processing') ...[
                  const SizedBox(height: 16),
                  const LinearProgressIndicator(),
                  const SizedBox(height: 8),
                  Text(l10n.notesStatusProcessing),
                ],
                if (note.status == 'ready' ||
                    note.status == 'uploaded' ||
                    note.status == 'failed') ...[
                  const SizedBox(height: 16),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: FilledButton.icon(
                      onPressed:
                          _generating || quotaExhausted ? null : _createPaper,
                      icon: _generating
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.ballot_outlined),
                      label: Text(
                        _generating
                            ? l10n.paperGenerating
                            : l10n.paperCreateCta,
                      ),
                    ),
                  ),
                  if (quota != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      quotaExhausted
                          ? l10n.paperQuotaExhausted(quota.windowDays)
                          : l10n.paperQuotaRemaining(
                              quota.remaining,
                              quota.limit,
                            ),
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: quotaExhausted
                            ? theme.colorScheme.error
                            : theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ],
                const SizedBox(height: 20),
                _TextSection(
                  title: l10n.noteRawExtractTitle,
                  subtitle: l10n.noteRawExtractSubtitle,
                  body: note.rawExtractedText,
                  emptyLabel: l10n.noteContentEmpty,
                ),
                const SizedBox(height: 20),
                _TextSection(
                  title: l10n.noteCanonicalTitle,
                  subtitle: l10n.noteCanonicalSubtitle,
                  body: note.canonicalContentEn,
                  emptyLabel: l10n.noteContentEmpty,
                  emphasize: true,
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  String _statusLabel(AppLocalizations l10n, String status) {
    return switch (status) {
      'processing' => l10n.notesStatusProcessing,
      'ready' => l10n.notesStatusReady,
      'failed' => l10n.notesStatusFailed,
      _ => l10n.notesStatusUploaded,
    };
  }
}

class _TextSection extends StatelessWidget {
  const _TextSection({
    required this.title,
    required this.subtitle,
    required this.body,
    required this.emptyLabel,
    this.emphasize = false,
  });

  final String title;
  final String subtitle;
  final String? body;
  final String emptyLabel;
  final bool emphasize;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final text = (body ?? '').trim();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w600,
            color: emphasize ? theme.colorScheme.primary : null,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          subtitle,
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 8),
        DecoratedBox(
          decoration: BoxDecoration(
            border: Border.all(color: theme.colorScheme.outlineVariant),
            borderRadius: BorderRadius.circular(8),
            color: theme.colorScheme.surfaceContainerLowest,
          ),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: SelectableText(
              text.isEmpty ? emptyLabel : text,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: text.isEmpty
                    ? theme.colorScheme.onSurfaceVariant
                    : theme.colorScheme.onSurface,
                height: 1.4,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
