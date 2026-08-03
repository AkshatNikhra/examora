import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/entity_actions.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/exams_repository.dart';
import '../../../repositories/me_repository.dart';
import '../../papers/presentation/papers_list_screen.dart';

final examsListProvider = FutureProvider.autoDispose<List<ExamItem>>((ref) {
  return ref.watch(examsRepositoryProvider).listExams();
});

class ExamsListScreen extends ConsumerWidget {
  const ExamsListScreen({super.key});

  Future<void> _addExam(BuildContext context, WidgetRef ref) async {
    final l10n = AppLocalizations.of(context);
    final controller = TextEditingController();
    final name = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.examsAddTitle),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: InputDecoration(
            labelText: l10n.setupExamFieldLabel,
            hintText: l10n.setupExamFieldHint,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(l10n.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, controller.text.trim()),
            child: Text(l10n.examsAddConfirm),
          ),
        ],
      ),
    );
    if (name == null || name.isEmpty) return;
    try {
      final exam = await ref.read(examsRepositoryProvider).createExam(name);
      ref.invalidate(examsListProvider);
      ref.invalidate(homeSummaryProvider);
      if (context.mounted) context.push('/exams/${exam.id}');
    } catch (error) {
      if (!context.mounted) return;
      final message = error is AppFailure ? error.message : l10n.genericError;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  Future<void> _renameExam(
    BuildContext context,
    WidgetRef ref,
    ExamItem exam,
  ) async {
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
      ref.invalidate(examsListProvider);
      ref.invalidate(homeSummaryProvider);
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.actionSuccessRenamed)),
      );
    } catch (error) {
      if (!context.mounted) return;
      final message = error is AppFailure ? error.message : l10n.genericError;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  Future<void> _deleteExam(
    BuildContext context,
    WidgetRef ref,
    ExamItem exam,
  ) async {
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
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.actionSuccessDeleted)),
      );
    } catch (error) {
      if (!context.mounted) return;
      final message = error is AppFailure ? error.message : l10n.genericError;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final asyncExams = ref.watch(examsListProvider);

    return Scaffold(
      backgroundColor: AppTheme.cream,
      appBar: AppBar(
        title: Text(
          l10n.examsListTitle,
          style: const TextStyle(
            fontSize: 26,
            fontWeight: FontWeight.w800,
          ),
        ),
        titleTextStyle: const TextStyle(
          color: AppTheme.ink,
          fontSize: 26,
          fontWeight: FontWeight.w800,
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _addExam(context, ref),
        icon: const Icon(Icons.add),
        label: Text(l10n.examsAddCta),
      ),
      body: asyncExams.when(
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
        data: (exams) {
          if (exams.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      l10n.examsListEmpty,
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodyLarge?.copyWith(fontSize: 16),
                    ),
                    const SizedBox(height: 16),
                    FilledButton(
                      onPressed: () => context.go('/onboarding/exams'),
                      child: Text(l10n.setupExamContinue),
                    ),
                  ],
                ),
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(examsListProvider);
              await ref.read(examsListProvider.future);
            },
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 88),
              itemCount: exams.length,
              separatorBuilder: (_, _) => const SizedBox(height: 10),
              itemBuilder: (context, index) {
                final exam = exams[index];
                return Material(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 10,
                    ),
                    title: Text(
                      exam.name,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    subtitle: Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text(
                        l10n.examsBatchCount(exam.batchCount),
                        style: const TextStyle(
                          fontSize: 14,
                          color: AppTheme.muted,
                        ),
                      ),
                    ),
                    trailing: PopupMenuButton<String>(
                      onSelected: (value) {
                        if (value == 'rename') {
                          _renameExam(context, ref, exam);
                        } else if (value == 'delete') {
                          _deleteExam(context, ref, exam);
                        }
                      },
                      itemBuilder: (context) => [
                        PopupMenuItem(
                          value: 'rename',
                          child: Text(l10n.rename),
                        ),
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
                    onTap: () => context.push('/exams/${exam.id}'),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
