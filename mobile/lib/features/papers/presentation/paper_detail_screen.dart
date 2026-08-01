import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_failure.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/papers_repository.dart';

final paperDetailProvider =
    FutureProvider.autoDispose.family<PaperDetail, String>((ref, paperId) {
  return ref.watch(papersRepositoryProvider).getPaper(paperId);
});

class PaperDetailScreen extends ConsumerWidget {
  const PaperDetailScreen({super.key, required this.paperId});

  final String paperId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final asyncPaper = ref.watch(paperDetailProvider(paperId));

    return Scaffold(
      appBar: AppBar(title: Text(l10n.paperDetailTitle)),
      body: asyncPaper.when(
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
        data: (paper) {
          return ListView.builder(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
            itemCount: paper.questions.length + 1,
            itemBuilder: (context, index) {
              if (index == 0) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(paper.title, style: theme.textTheme.titleLarge),
                      const SizedBox(height: 4),
                      Text(
                        l10n.paperMeta(
                          paper.questionCount,
                          paper.language.toUpperCase(),
                        ),
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        l10n.paperViewHint,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                );
              }
              final q = paper.questions[index - 1];
              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Q${q.orderIndex + 1}. ${q.stem}',
                        style: theme.textTheme.titleSmall,
                      ),
                      if (q.topic != null && q.topic!.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          q.topic!,
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: theme.colorScheme.primary,
                          ),
                        ),
                      ],
                      const SizedBox(height: 8),
                      ...List.generate(q.options.length, (i) {
                        final label = String.fromCharCode(65 + i);
                        final isCorrect = i == q.correctIndex;
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 4),
                          child: Text(
                            '$label. ${q.options[i]}',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              fontWeight:
                                  isCorrect ? FontWeight.w600 : FontWeight.normal,
                              color: isCorrect
                                  ? theme.colorScheme.primary
                                  : null,
                            ),
                          ),
                        );
                      }),
                      if (q.explanation != null &&
                          q.explanation!.trim().isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Text(
                          q.explanation!,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
