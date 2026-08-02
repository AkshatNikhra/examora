import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_theme.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/papers_repository.dart';
import 'papers_list_screen.dart';

/// Tests inside one topic folder. Tap a test to open it.
class TopicTestsScreen extends ConsumerWidget {
  const TopicTestsScreen({
    super.key,
    required this.topicId,
    this.initialFolder,
  });

  final String topicId;
  final TestTopicFolder? initialFolder;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final asyncFolders = ref.watch(testTopicFoldersProvider);

    final folder = asyncFolders.maybeWhen(
      data: (folders) {
        for (final f in folders) {
          if (f.topicId == topicId) return f;
        }
        return initialFolder;
      },
      orElse: () => initialFolder,
    );

    final title = folder?.topicName ?? 'Tests';
    final tests = folder?.tests ?? const <PaperSummary>[];

    return Scaffold(
      backgroundColor: AppTheme.cream,
      appBar: AppBar(
        title: Text(
          title,
          style: const TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w800,
          ),
        ),
        titleTextStyle: const TextStyle(
          color: AppTheme.ink,
          fontSize: 22,
          fontWeight: FontWeight.w800,
        ),
      ),
      body: asyncFolders.when(
        loading: () => folder == null
            ? const Center(child: CircularProgressIndicator())
            : _TestsList(tests: tests, l10n: l10n),
        error: (error, _) => folder == null
            ? Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(
                    error is AppFailure ? error.message : l10n.genericError,
                    textAlign: TextAlign.center,
                  ),
                ),
              )
            : _TestsList(tests: tests, l10n: l10n),
        data: (_) {
          if (tests.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  l10n.papersListEmpty,
                  textAlign: TextAlign.center,
                  style: theme.textTheme.bodyLarge?.copyWith(
                    fontSize: 16,
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(testTopicFoldersProvider);
              await ref.read(testTopicFoldersProvider.future);
            },
            child: _TestsList(tests: tests, l10n: l10n),
          );
        },
      ),
    );
  }
}

class _TestsList extends StatelessWidget {
  const _TestsList({required this.tests, required this.l10n});

  final List<PaperSummary> tests;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      itemCount: tests.length,
      separatorBuilder: (_, _) => const SizedBox(height: 10),
      itemBuilder: (context, index) {
        final paper = tests[index];
        return Material(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 16,
              vertical: 10,
            ),
            leading: CircleAvatar(
              backgroundColor: AppTheme.navy.withValues(alpha: 0.1),
              foregroundColor: AppTheme.navy,
              child: const Icon(Icons.ballot_outlined, size: 22),
            ),
            title: Text(
              paper.title,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
              ),
            ),
            subtitle: Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                l10n.paperMeta(
                  paper.questionCount,
                  paper.language.toUpperCase(),
                ),
                style: const TextStyle(
                  fontSize: 14,
                  color: AppTheme.muted,
                ),
              ),
            ),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => context.push('/papers/${paper.id}'),
          ),
        );
      },
    );
  }
}
