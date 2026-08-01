import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/presentation/auth_gate.dart';
import '../../features/auth/presentation/auth_providers.dart';
import '../../features/auth/presentation/otp_screen.dart';
import '../../features/auth/presentation/sign_in_screen.dart';
import '../../features/auth/presentation/sign_up_screen.dart';
import '../../features/exams/presentation/batch_detail_screen.dart';
import '../../features/exams/presentation/exam_detail_screen.dart';
import '../../features/exams/presentation/exams_list_screen.dart';
import '../../features/home/presentation/home_screen.dart';
import '../../features/notes/presentation/note_detail_screen.dart';
import '../../features/notes/presentation/notes_list_screen.dart';
import '../../features/onboarding/presentation/onboarding_exams_screen.dart';
import '../../features/onboarding/presentation/onboarding_profile_screen.dart';
import '../../features/papers/presentation/attempt_score_screen.dart';
import '../../features/papers/presentation/paper_detail_screen.dart';
import '../../features/papers/presentation/papers_list_screen.dart';
import '../../features/profile/presentation/profile_screen.dart';
import '../../features/shell/presentation/main_shell.dart';
import '../../repositories/papers_repository.dart';
import 'go_router_refresh.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>();
final _shellNavigatorKey = GlobalKey<NavigatorState>();

final appRouterProvider = Provider<GoRouter>((ref) {
  final authRepository = ref.watch(authRepositoryProvider);

  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: '/',
    refreshListenable: GoRouterRefreshStream(authRepository.authStateChanges()),
    errorBuilder: (context, state) => Scaffold(
      appBar: AppBar(title: const Text('Not found')),
      body: Center(child: Text('No page for ${state.uri}')),
    ),
    redirect: (BuildContext context, GoRouterState state) {
      final User? user = authRepository.currentUser;
      final bool loggedIn = user != null;
      final String location = state.matchedLocation;
      final bool onAuthRoute = location == '/signup' ||
          location == '/signin' ||
          location == '/login' ||
          location == '/otp';
      final bool onOnboarding = location.startsWith('/onboarding');

      if (!loggedIn && !onAuthRoute) {
        return '/signin';
      }
      if (loggedIn && onAuthRoute) {
        return '/';
      }
      if (!loggedIn && onOnboarding) {
        return '/signin';
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/',
        name: 'gate',
        builder: (context, state) => const AuthGate(),
      ),
      GoRoute(
        path: '/signup',
        name: 'signup',
        builder: (context, state) => const SignUpScreen(),
      ),
      GoRoute(
        path: '/signin',
        name: 'signin',
        builder: (context, state) => const SignInScreen(),
      ),
      GoRoute(
        path: '/login',
        redirect: (context, state) => '/signin',
      ),
      GoRoute(
        path: '/otp',
        name: 'otp',
        builder: (context, state) {
          final args = state.extra;
          if (args is! OtpRouteArgs) {
            return const SignInScreen();
          }
          return OtpScreen(args: args);
        },
      ),
      GoRoute(
        path: '/onboarding/profile',
        name: 'onboardingProfile',
        builder: (context, state) => const OnboardingProfileScreen(),
      ),
      GoRoute(
        path: '/onboarding/exams',
        name: 'onboardingExams',
        builder: (context, state) => const OnboardingExamsScreen(),
      ),
      ShellRoute(
        navigatorKey: _shellNavigatorKey,
        builder: (context, state, child) => MainShell(child: child),
        routes: [
          GoRoute(
            path: '/app/home',
            name: 'home',
            builder: (context, state) => const HomeScreen(),
          ),
          GoRoute(
            path: '/app/exams',
            name: 'exams',
            builder: (context, state) => const ExamsListScreen(),
          ),
          GoRoute(
            path: '/app/tests',
            name: 'tests',
            builder: (context, state) => const PapersListScreen(),
          ),
          GoRoute(
            path: '/app/profile',
            name: 'profile',
            builder: (context, state) => const ProfileScreen(),
          ),
        ],
      ),
      GoRoute(
        path: '/exams/:examId',
        name: 'examDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) {
          final examId = state.pathParameters['examId'] ?? '';
          return ExamDetailScreen(examId: examId);
        },
      ),
      GoRoute(
        path: '/batches/:batchId',
        name: 'batchDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) {
          final batchId = state.pathParameters['batchId'] ?? '';
          return BatchDetailScreen(batchId: batchId);
        },
      ),
      GoRoute(
        path: '/notes',
        name: 'notes',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const NotesListScreen(),
      ),
      GoRoute(
        path: '/notes/:noteId',
        name: 'noteDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) {
          final noteId = state.pathParameters['noteId'] ?? '';
          return NoteDetailScreen(noteId: noteId);
        },
      ),
      GoRoute(
        path: '/papers',
        name: 'papers',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) => const PapersListScreen(),
      ),
      GoRoute(
        path: '/papers/:paperId',
        name: 'paperDetail',
        parentNavigatorKey: _rootNavigatorKey,
        builder: (context, state) {
          final paperId = state.pathParameters['paperId'] ?? '';
          return PaperDetailScreen(paperId: paperId);
        },
        routes: [
          GoRoute(
            path: 'attempts/:attemptId',
            name: 'attemptScore',
            parentNavigatorKey: _rootNavigatorKey,
            builder: (context, state) {
              final paperId = state.pathParameters['paperId'] ?? '';
              final attemptId = state.pathParameters['attemptId'] ?? '';
              final extra = state.extra;
              return AttemptScoreScreen(
                paperId: paperId,
                attemptId: attemptId,
                initialResult: extra is AttemptResult ? extra : null,
              );
            },
          ),
        ],
      ),
      GoRoute(
        path: '/setup',
        redirect: (context, state) => '/onboarding/profile',
      ),
    ],
  );
});
