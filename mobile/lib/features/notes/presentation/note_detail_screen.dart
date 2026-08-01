import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_failure.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/notes_repository.dart';
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
  bool _starting = false;

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  void _syncPolling(NoteDetail? note) {
    // Only poll while backend is actually processing — not for "uploaded"
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

  Future<void> _startProcess() async {
    final l10n = AppLocalizations.of(context);
    setState(() => _starting = true);
    try {
      await ref.read(notesRepositoryProvider).processNote(widget.noteId);
      ref.invalidate(noteDetailProvider(widget.noteId));
      ref.invalidate(notesListProvider);
    } catch (error) {
      if (!mounted) return;
      final message = error is AppFailure ? error.message : l10n.genericError;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    } finally {
      if (mounted) setState(() => _starting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final asyncNote = ref.watch(noteDetailProvider(widget.noteId));

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
                    l10n.noteProcessHint,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: FilledButton.icon(
                      onPressed: _starting ? null : _startProcess,
                      icon: _starting
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.auto_awesome),
                      label: Text(l10n.noteStartProcess),
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
                  Align(
                    alignment: Alignment.centerLeft,
                    child: FilledButton(
                      onPressed: _starting ? null : _startProcess,
                      child: Text(l10n.notesRetryProcess),
                    ),
                  ),
                ],
                if (note.status == 'processing') ...[
                  const SizedBox(height: 16),
                  const LinearProgressIndicator(),
                  const SizedBox(height: 8),
                  Text(l10n.notesStatusProcessing),
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
