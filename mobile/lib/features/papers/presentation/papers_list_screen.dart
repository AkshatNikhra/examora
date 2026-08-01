import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/papers_repository.dart';

final papersListProvider =
    FutureProvider.autoDispose<List<PaperSummary>>((ref) {
  return ref.watch(papersRepositoryProvider).listPapers();
});

class PapersListScreen extends ConsumerWidget {
  const PapersListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final asyncPapers = ref.watch(papersListProvider);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.papersListTitle)),
      body: asyncPapers.when(
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
        data: (papers) {
          if (papers.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  l10n.papersListEmpty,
                  textAlign: TextAlign.center,
                  style: theme.textTheme.bodyLarge?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(papersListProvider);
              await ref.read(papersListProvider.future);
            },
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(vertical: 8),
              itemCount: papers.length,
              separatorBuilder: (_, _) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final paper = papers[index];
                return ListTile(
                  title: Text(paper.title),
                  subtitle: Text(
                    l10n.paperMeta(
                      paper.questionCount,
                      paper.language.toUpperCase(),
                    ),
                  ),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/papers/${paper.id}'),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
