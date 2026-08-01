import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../features/auth/presentation/auth_providers.dart';
import '../../../features/exams/presentation/exams_list_screen.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/health_repository.dart';
import '../../../repositories/me_repository.dart';

final healthCheckProvider = FutureProvider.autoDispose<Map<String, dynamic>>((
  ref,
) {
  return ref.watch(healthRepositoryProvider).check();
});

/// Phase 1 test: calls authenticated GET /me with Firebase ID token.
final meCheckProvider = FutureProvider.autoDispose<Map<String, dynamic>>((
  ref,
) {
  return ref.watch(meRepositoryProvider).fetchMe();
});

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final health = ref.watch(healthCheckProvider);
    final me = ref.watch(meCheckProvider);
    final exams = ref.watch(examsListProvider);
    final authUser = ref.watch(authStateProvider).valueOrNull;
    final theme = Theme.of(context);

    // First-time setup: no exams yet → send to exam name screen.
    exams.whenData((list) {
      if (list.isEmpty) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (context.mounted &&
              GoRouterState.of(context).matchedLocation == '/') {
            context.go('/setup');
          }
        });
      }
    });

    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.appTitle),
        actions: [
          IconButton(
            tooltip: l10n.logout,
            onPressed: () async {
              await ref.read(authRepositoryProvider).signOut();
            },
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                l10n.homeHeadline,
                style: theme.textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                l10n.homeSubtitle,
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
              if (authUser?.phoneNumber != null) ...[
                const SizedBox(height: 8),
                Text(
                  authUser!.phoneNumber!,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.primary,
                  ),
                ),
              ],
              const SizedBox(height: 24),
              health.when(
                data: (_) => _StatusChip(
                  label: l10n.backendStatusOk,
                  color: theme.colorScheme.primary,
                ),
                loading: () => const LinearProgressIndicator(),
                error: (error, _) => _StatusChip(
                  label: error is AppFailure
                      ? '${l10n.backendStatusFail}: ${error.message}'
                      : l10n.backendStatusFail,
                  color: theme.colorScheme.error,
                ),
              ),
              const SizedBox(height: 12),
              me.when(
                data: (data) => _StatusChip(
                  label: l10n.meStatusOk(
                    data['phone']?.toString() ?? authUser?.phoneNumber ?? '—',
                  ),
                  color: theme.colorScheme.primary,
                ),
                loading: () => _StatusChip(
                  label: l10n.meStatusLoading,
                  color: theme.colorScheme.onSurfaceVariant,
                ),
                error: (error, _) => _StatusChip(
                  label: error is AppFailure
                      ? '${l10n.meStatusFail}: ${error.message}'
                      : l10n.meStatusFail,
                  color: theme.colorScheme.error,
                ),
              ),
              const Spacer(),
              FilledButton(
                onPressed: () => context.push('/exams'),
                child: Text(l10n.homeExamsCta),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () => context.push('/papers'),
                child: Text(l10n.homePapersCta),
              ),
              const SizedBox(height: 12),
              TextButton(
                onPressed: () => context.push('/notes'),
                child: Text(l10n.homeCta),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: color),
      ),
    );
  }
}
