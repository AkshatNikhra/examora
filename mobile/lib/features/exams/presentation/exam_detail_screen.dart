import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/exams_repository.dart';
import 'exams_list_screen.dart';

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

class ExamDetailScreen extends ConsumerWidget {
  const ExamDetailScreen({super.key, required this.examId});

  final String examId;

  Future<void> _createBatch(BuildContext context, WidgetRef ref) async {
    final l10n = AppLocalizations.of(context);
    final hint = ref.read(examUploadHintProvider(examId)).valueOrNull;
    final controller = TextEditingController();
    final name = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.batchCreateTitle),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (hint?.suggestNewBatch == true && hint?.reason != null) ...[
              Text(
                hint!.reason!,
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: 12),
            ],
            TextField(
              controller: controller,
              autofocus: true,
              decoration: InputDecoration(
                labelText: l10n.batchNameLabel,
                hintText: l10n.batchNameHint,
              ),
            ),
          ],
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
            examId: examId,
            name: name,
          );
      ref.invalidate(examBatchesProvider(examId));
      ref.invalidate(examsListProvider);
      ref.invalidate(examUploadHintProvider(examId));
      if (context.mounted) context.push('/batches/${batch.id}');
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
    final asyncExam = ref.watch(examDetailProvider(examId));
    final asyncBatches = ref.watch(examBatchesProvider(examId));
    final asyncHint = ref.watch(examUploadHintProvider(examId));

    return Scaffold(
      appBar: AppBar(
        title: asyncExam.maybeWhen(
          data: (e) => Text(e.name),
          orElse: () => Text(l10n.examDetailTitle),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _createBatch(context, ref),
        icon: const Icon(Icons.create_new_folder_outlined),
        label: Text(l10n.batchCreateCta),
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
              ref.invalidate(examBatchesProvider(examId));
              ref.invalidate(examUploadHintProvider(examId));
              await ref.read(examBatchesProvider(examId).future);
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 88),
              children: [
                asyncHint.maybeWhen(
                  data: (hint) {
                    if (!hint.suggestNewBatch) return const SizedBox.shrink();
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Text(
                          hint.reason ?? l10n.batchSuggestNew,
                          style: theme.textTheme.bodyMedium,
                        ),
                      ),
                    );
                  },
                  orElse: () => const SizedBox.shrink(),
                ),
                Text(
                  l10n.batchListTitle,
                  style: theme.textTheme.titleMedium,
                ),
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
                    (batch) => Card(
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        title: Text(batch.name),
                        subtitle: Text(
                          l10n.batchMeta(
                            batch.noteCount,
                            batch.hasPaper
                                ? l10n.batchHasPaper
                                : l10n.batchNoPaper,
                          ),
                        ),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => context.push('/batches/${batch.id}'),
                      ),
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}
