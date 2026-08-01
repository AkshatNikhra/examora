import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/exams_repository.dart';

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
      if (context.mounted) context.push('/exams/${exam.id}');
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
      appBar: AppBar(title: Text(l10n.examsListTitle)),
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
                      style: theme.textTheme.bodyLarge,
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
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: exams.length,
              separatorBuilder: (_, _) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final exam = exams[index];
                return ListTile(
                  title: Text(exam.name),
                  subtitle: Text(l10n.examsBatchCount(exam.batchCount)),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/exams/${exam.id}'),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
