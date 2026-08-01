import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_theme.dart';
import '../../../features/auth/presentation/auth_providers.dart';
import '../../../repositories/me_repository.dart';

/// Decides signup vs onboarding vs app after auth state is known.
class AuthGate extends ConsumerWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authStateProvider);
    return auth.when(
      loading: () => const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      ),
      error: (_, _) => const Scaffold(
        body: Center(child: Text('Something went wrong')),
      ),
      data: (user) {
        if (user == null) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (context.mounted) context.go('/signin');
          });
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        final me = ref.watch(meProfileProvider);
        return me.when(
          loading: () => const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          ),
          error: (e, _) => Scaffold(
            body: Center(child: Text(e.toString())),
          ),
          data: (profile) {
            WidgetsBinding.instance.addPostFrameCallback((_) {
              if (!context.mounted) return;
              if (!profile.onboardingCompleted) {
                if (profile.fullName == null || profile.fullName!.isEmpty) {
                  context.go('/onboarding/profile');
                } else {
                  context.go('/onboarding/exams');
                }
              } else {
                context.go('/app/home');
              }
            });
            return const Scaffold(
              backgroundColor: AppTheme.cream,
              body: Center(child: CircularProgressIndicator()),
            );
          },
        );
      },
    );
  }
}
