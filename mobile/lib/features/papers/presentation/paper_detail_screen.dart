import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/papers_repository.dart';

final paperDetailProvider =
    FutureProvider.autoDispose.family<PaperDetail, String>((ref, paperId) {
  return ref.watch(papersRepositoryProvider).getPaper(paperId);
});

class PaperDetailScreen extends ConsumerStatefulWidget {
  const PaperDetailScreen({super.key, required this.paperId});

  final String paperId;

  @override
  ConsumerState<PaperDetailScreen> createState() => _PaperDetailScreenState();
}

class _PaperDetailScreenState extends ConsumerState<PaperDetailScreen> {
  final Map<String, int> _selected = {};
  bool _submitting = false;

  Future<void> _submit(PaperDetail paper) async {
    final l10n = AppLocalizations.of(context);
    if (_selected.length != paper.questions.length) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.attemptAnswerAll)),
      );
      return;
    }

    setState(() => _submitting = true);
    try {
      final result = await ref.read(papersRepositoryProvider).submitAttempt(
            paperId: widget.paperId,
            selectedByQuestionId: Map<String, int>.from(_selected),
          );
      if (!mounted) return;
      context.pushReplacement(
        '/papers/${widget.paperId}/attempts/${result.id}',
        extra: result,
      );
    } catch (error) {
      if (!mounted) return;
      final message = error is AppFailure ? error.message : l10n.genericError;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final asyncPaper = ref.watch(paperDetailProvider(widget.paperId));

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
          if (paper.questions.isEmpty) {
            return Center(child: Text(l10n.attemptNoQuestions));
          }

          return Column(
            children: [
              Expanded(
                child: ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 16),
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
                              l10n.attemptHint,
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: theme.colorScheme.onSurfaceVariant,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              l10n.attemptProgress(
                                _selected.length,
                                paper.questions.length,
                              ),
                              style: theme.textTheme.labelMedium?.copyWith(
                                color: theme.colorScheme.primary,
                              ),
                            ),
                          ],
                        ),
                      );
                    }

                    final q = paper.questions[index - 1];
                    final selected = _selected[q.id];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(12, 12, 12, 4),
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
                            const SizedBox(height: 4),
                            ...List.generate(q.options.length, (i) {
                              final label = String.fromCharCode(65 + i);
                              final isSelected = selected == i;
                              return ListTile(
                                dense: true,
                                contentPadding: EdgeInsets.zero,
                                leading: Icon(
                                  isSelected
                                      ? Icons.radio_button_checked
                                      : Icons.radio_button_off,
                                  color: isSelected
                                      ? theme.colorScheme.primary
                                      : theme.colorScheme.onSurfaceVariant,
                                ),
                                title: Text('$label. ${q.options[i]}'),
                                onTap: _submitting
                                    ? null
                                    : () => setState(() => _selected[q.id] = i),
                              );
                            }),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
              SafeArea(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                  child: FilledButton(
                    onPressed: _submitting ? null : () => _submit(paper),
                    child: _submitting
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : Text(l10n.attemptSubmit),
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
