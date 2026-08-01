import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/papers_repository.dart';

final attemptResultProvider = FutureProvider.autoDispose
    .family<AttemptResult, ({String paperId, String attemptId})>((ref, ids) {
  return ref.watch(papersRepositoryProvider).getAttempt(
        paperId: ids.paperId,
        attemptId: ids.attemptId,
      );
});

class AttemptScoreScreen extends ConsumerWidget {
  const AttemptScoreScreen({
    super.key,
    required this.paperId,
    required this.attemptId,
    this.initialResult,
  });

  final String paperId;
  final String attemptId;
  final AttemptResult? initialResult;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);

    if (initialResult != null) {
      return _ScoreScaffold(result: initialResult!);
    }

    final asyncResult = ref.watch(
      attemptResultProvider((paperId: paperId, attemptId: attemptId)),
    );

    return asyncResult.when(
      loading: () => Scaffold(
        appBar: AppBar(title: Text(l10n.attemptScoreTitle)),
        body: const Center(child: CircularProgressIndicator()),
      ),
      error: (error, _) => Scaffold(
        appBar: AppBar(title: Text(l10n.attemptScoreTitle)),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(
              error is AppFailure ? error.message : l10n.genericError,
              textAlign: TextAlign.center,
            ),
          ),
        ),
      ),
      data: (result) => _ScoreScaffold(result: result),
    );
  }
}

class _ScoreScaffold extends StatelessWidget {
  const _ScoreScaffold({required this.result});

  final AttemptResult result;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.attemptScoreTitle)),
      body: ListView.builder(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
        itemCount: result.answers.length + 1,
        itemBuilder: (context, index) {
          if (index == 0) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    l10n.attemptScoreHeadline(result.scorePercent),
                    style: theme.textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    l10n.attemptScoreMeta(
                      result.correctCount,
                      result.totalCount,
                    ),
                    style: theme.textTheme.bodyLarge?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => context.go('/papers'),
                          child: Text(l10n.attemptBackToPapers),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: FilledButton(
                          onPressed: () => context.pushReplacement(
                            '/papers/${result.paperId}',
                          ),
                          child: Text(l10n.attemptRetry),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Text(
                    l10n.attemptReviewTitle,
                    style: theme.textTheme.titleMedium,
                  ),
                ],
              ),
            );
          }

          final a = result.answers[index - 1];
          final color =
              a.isCorrect ? theme.colorScheme.primary : theme.colorScheme.error;
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        a.isCorrect ? Icons.check_circle : Icons.cancel,
                        color: color,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'Q${a.orderIndex + 1}. ${a.stem}',
                          style: theme.textTheme.titleSmall,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  ...List.generate(a.options.length, (i) {
                    final label = String.fromCharCode(65 + i);
                    final isSelected = i == a.selectedIndex;
                    final isCorrect = i == a.correctIndex;
                    TextStyle? style = theme.textTheme.bodyMedium;
                    if (isCorrect) {
                      style = style?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: theme.colorScheme.primary,
                      );
                    } else if (isSelected && !a.isCorrect) {
                      style = style?.copyWith(
                        color: theme.colorScheme.error,
                      );
                    }
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 4),
                      child: Text('$label. ${a.options[i]}', style: style),
                    );
                  }),
                  if (a.explanation != null &&
                      a.explanation!.trim().isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      a.explanation!,
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
      ),
    );
  }
}
