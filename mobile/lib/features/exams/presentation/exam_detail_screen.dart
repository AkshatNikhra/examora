import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/create_test_notice.dart';
import '../../../core/widgets/entity_actions.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/exams_repository.dart';
import '../../../repositories/me_repository.dart';
import '../../../repositories/papers_repository.dart';
import 'exams_list_screen.dart';
import '../../papers/presentation/papers_list_screen.dart';

final examDetailProvider =
    FutureProvider.autoDispose.family<ExamItem, String>((ref, examId) {
  return ref.watch(examsRepositoryProvider).getExam(examId);
});

final examBatchesProvider =
    FutureProvider.autoDispose.family<List<BatchItem>, String>((ref, examId) {
  return ref.watch(examsRepositoryProvider).listBatches(examId);
});

final examUploadHintProvider =
    FutureProvider.autoDispose.family<ExamUploadHint, String>((ref, examId) {
  return ref.watch(examsRepositoryProvider).uploadHint(examId);
});

class ExamDetailScreen extends ConsumerStatefulWidget {
  const ExamDetailScreen({super.key, required this.examId});

  final String examId;

  @override
  ConsumerState<ExamDetailScreen> createState() => _ExamDetailScreenState();
}

class _ExamDetailScreenState extends ConsumerState<ExamDetailScreen> {
  final Set<String> _selected = {};
  bool _generating = false;

  static const _titleStyle = TextStyle(
    color: AppTheme.ink,
    fontSize: 26,
    fontWeight: FontWeight.w800,
  );

  Future<void> _createBatch() async {
    final l10n = AppLocalizations.of(context);
    final controller = TextEditingController();
    final name = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.batchCreateTitle),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: InputDecoration(
            labelText: l10n.batchNameLabel,
            hintText: l10n.batchNameHint,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(l10n.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, controller.text.trim()),
            child: Text(l10n.batchCreateConfirm),
          ),
        ],
      ),
    );
    if (name == null || name.isEmpty) return;
    try {
      final batch = await ref.read(examsRepositoryProvider).createBatch(
            examId: widget.examId,
            name: name,
          );
      ref.invalidate(examBatchesProvider(widget.examId));
      ref.invalidate(examsListProvider);
      ref.invalidate(examUploadHintProvider(widget.examId));
      if (mounted) context.push('/batches/${batch.id}');
    } catch (error) {
      if (!mounted) return;
      final message = error is AppFailure ? error.message : l10n.genericError;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
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

  Future<void> _createTestFromSelected() async {
    if (_generating) return;
    final l10n = AppLocalizations.of(context);
    if (_selected.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.topicsSelectNone)),
      );
      return;
    }

    setState(() => _generating = true);
    try {
      final proceed = await showCreateTestNoticesIfNeeded(
        context,
        quota: ref.read(homeSummaryProvider).valueOrNull?.paperQuota,
      );
      if (!proceed || !mounted) return;

      final language = await _pickLanguage();
      if (language == null || !mounted) return;

      await ref.read(papersRepositoryProvider).generatePaperFromTopics(
            examId: widget.examId,
            batchIds: _selected.toList(),
            language: language,
          );
      ref.invalidate(examBatchesProvider(widget.examId));
      ref.invalidate(examUploadHintProvider(widget.examId));
      ref.invalidate(homeSummaryProvider);
      ref.invalidate(testTopicFoldersProvider);
      if (!mounted) return;
      setState(() => _selected.clear());
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

  Future<void> _renameExam(ExamItem exam) async {
    final l10n = AppLocalizations.of(context);
    final name = await showRenameDialog(
      context,
      title: l10n.renameExamTitle,
      label: l10n.setupExamFieldLabel,
      initialValue: exam.name,
    );
    if (name == null) return;
    try {
      await ref.read(examsRepositoryProvider).renameExam(
            examId: exam.id,
            name: name,
          );
      ref.invalidate(examDetailProvider(widget.examId));
      ref.invalidate(examsListProvider);
      ref.invalidate(homeSummaryProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.actionSuccessRenamed)),
      );
    } catch (error) {
      if (!mounted) return;
      final message = error is AppFailure ? error.message : l10n.genericError;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  Future<void> _deleteExam(ExamItem exam) async {
    final l10n = AppLocalizations.of(context);
    if (!exam.canDelete) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.cannotDeleteWithReady)),
      );
      return;
    }
    final confirmed = await showConfirmDeleteDialog(
      context,
      title: l10n.deleteExamTitle,
      message: exam.batchCount == 0
          ? l10n.deleteExamEmptyMessage
          : l10n.deleteExamMessage,
    );
    if (!confirmed) return;
    try {
      await ref.read(examsRepositoryProvider).deleteExam(exam.id);
      ref.invalidate(examsListProvider);
      ref.invalidate(homeSummaryProvider);
      ref.invalidate(testTopicFoldersProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.actionSuccessDeleted)),
      );
      context.go('/app/exams');
    } catch (error) {
      if (!mounted) return;
      final message = error is AppFailure ? error.message : l10n.genericError;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  Future<void> _renameBatch(BatchItem batch) async {
    final l10n = AppLocalizations.of(context);
    final name = await showRenameDialog(
      context,
      title: l10n.renameTopicTitle,
      label: l10n.batchNameLabel,
      initialValue: batch.name,
    );
    if (name == null) return;
    try {
      await ref.read(examsRepositoryProvider).renameBatch(
            batchId: batch.id,
            name: name,
          );
      ref.invalidate(examBatchesProvider(widget.examId));
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.actionSuccessRenamed)),
      );
    } catch (error) {
      if (!mounted) return;
      final message = error is AppFailure ? error.message : l10n.genericError;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  Future<void> _deleteBatch(BatchItem batch) async {
    final l10n = AppLocalizations.of(context);
    if (!batch.canDelete) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.cannotDeleteWithReady)),
      );
      return;
    }
    final confirmed = await showConfirmDeleteDialog(
      context,
      title: l10n.deleteTopicTitle,
      message: l10n.deleteTopicMessage,
    );
    if (!confirmed) return;
    try {
      await ref.read(examsRepositoryProvider).deleteBatch(batch.id);
      _selected.remove(batch.id);
      ref.invalidate(examBatchesProvider(widget.examId));
      ref.invalidate(examDetailProvider(widget.examId));
      ref.invalidate(examsListProvider);
      ref.invalidate(examUploadHintProvider(widget.examId));
      ref.invalidate(homeSummaryProvider);
      ref.invalidate(testTopicFoldersProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.actionSuccessDeleted)),
      );
    } catch (error) {
      if (!mounted) return;
      final message = error is AppFailure ? error.message : l10n.genericError;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  void _toggle(String id) {
    setState(() {
      if (_selected.contains(id)) {
        _selected.remove(id);
      } else {
        _selected.add(id);
      }
    });
  }

  void _toggleTopic(BatchItem batch) {
    if (batch.noteCount <= 0) {
      final l10n = AppLocalizations.of(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.topicsSelectEmptyTopic)),
      );
      return;
    }
    _toggle(batch.id);
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final asyncExam = ref.watch(examDetailProvider(widget.examId));
    final asyncBatches = ref.watch(examBatchesProvider(widget.examId));
    final quota = ref.watch(homeSummaryProvider).valueOrNull?.paperQuota;
    final quotaExhausted = quota?.isExhausted ?? false;
    final selectedCount = _selected.length;

    return Scaffold(
      backgroundColor: AppTheme.cream,
      appBar: AppBar(
        title: asyncExam.maybeWhen(
          data: (e) => Text(e.name, style: _titleStyle),
          orElse: () => Text(l10n.examDetailTitle, style: _titleStyle),
        ),
        titleTextStyle: _titleStyle,
        actions: [
          asyncExam.maybeWhen(
            data: (exam) => PopupMenuButton<String>(
              onSelected: (value) {
                if (value == 'rename') {
                  _renameExam(exam);
                } else if (value == 'delete') {
                  _deleteExam(exam);
                }
              },
              itemBuilder: (context) => [
                PopupMenuItem(value: 'rename', child: Text(l10n.rename)),
                PopupMenuItem(
                  value: 'delete',
                  enabled: exam.canDelete,
                  child: Text(
                    l10n.delete,
                    style: TextStyle(
                      color: exam.canDelete
                          ? theme.colorScheme.error
                          : theme.disabledColor,
                    ),
                  ),
                ),
              ],
            ),
            orElse: () => const SizedBox.shrink(),
          ),
        ],
      ),
      floatingActionButton: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (selectedCount > 0)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  FloatingActionButton.extended(
                    heroTag: 'create_test',
                    onPressed: _generating || quotaExhausted
                        ? null
                        : _createTestFromSelected,
                    icon: _generating
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.ballot_outlined),
                    label: Text(
                      _generating
                          ? l10n.paperGenerating
                          : l10n.topicsCreateTestSelected(selectedCount),
                    ),
                  ),
                  if (quota != null) ...[
                    const SizedBox(height: 6),
                    Material(
                      color: Colors.transparent,
                      child: Text(
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
                    ),
                  ],
                ],
              ),
            ),
          FloatingActionButton.extended(
            heroTag: 'new_topic',
            onPressed: _createBatch,
            icon: const Icon(Icons.create_new_folder_outlined),
            label: Text(l10n.batchCreateCta),
          ),
        ],
      ),
      body: asyncBatches.when(
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
        data: (batches) {
          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(examBatchesProvider(widget.examId));
              ref.invalidate(examUploadHintProvider(widget.examId));
              ref.invalidate(examDetailProvider(widget.examId));
              await ref.read(examBatchesProvider(widget.examId).future);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 140),
              children: [
                Text(
                  l10n.batchListTitle,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                if (batches.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    l10n.topicsSelectHint,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
                const SizedBox(height: 8),
                if (batches.isEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 24),
                    child: Text(
                      l10n.batchListEmpty,
                      style: theme.textTheme.bodyLarge?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  )
                else
                  ...batches.map(
                    (batch) {
                      final selected = _selected.contains(batch.id);
                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          leading: Checkbox(
                            value: selected,
                            onChanged: batch.noteCount <= 0
                                ? null
                                : (_) => _toggleTopic(batch),
                          ),
                          title: Text(
                            batch.name,
                            style: const TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          subtitle: Text(l10n.batchMeta(batch.noteCount)),
                          trailing: PopupMenuButton<String>(
                            onSelected: (value) {
                              if (value == 'rename') {
                                _renameBatch(batch);
                              } else if (value == 'delete') {
                                _deleteBatch(batch);
                              }
                            },
                            itemBuilder: (context) => [
                              PopupMenuItem(
                                value: 'rename',
                                child: Text(l10n.rename),
                              ),
                              PopupMenuItem(
                                value: 'delete',
                                enabled: batch.canDelete,
                                child: Text(
                                  l10n.delete,
                                  style: TextStyle(
                                    color: batch.canDelete
                                        ? theme.colorScheme.error
                                        : theme.disabledColor,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          onTap: () => context.push('/batches/${batch.id}'),
                          onLongPress: () => _toggleTopic(batch),
                        ),
                      );
                    },
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}
