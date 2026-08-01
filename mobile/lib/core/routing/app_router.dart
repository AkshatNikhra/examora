import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/presentation/auth_providers.dart';
import '../../features/auth/presentation/otp_screen.dart';
import '../../features/auth/presentation/phone_login_screen.dart';
import '../../features/home/presentation/home_screen.dart';
import '../../features/notes/presentation/note_detail_screen.dart';
import '../../features/notes/presentation/notes_list_screen.dart';
import '../../features/papers/presentation/paper_detail_screen.dart';
import 'go_router_refresh.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final authRepository = ref.watch(authRepositoryProvider);

  return GoRouter(
    initialLocation: '/',
    refreshListenable: GoRouterRefreshStream(authRepository.authStateChanges()),
    errorBuilder: (context, state) => Scaffold(
      appBar: AppBar(title: const Text('Not found')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            'No page for ${state.uri}',
            textAlign: TextAlign.center,
          ),
        ),
      ),
    ),
    redirect: (BuildContext context, GoRouterState state) {
      final User? user = authRepository.currentUser;
      final bool loggedIn = user != null;
      final String location = state.matchedLocation;
      final bool onAuthRoute =
          location == '/login' || location == '/otp';

      if (!loggedIn && !onAuthRoute) {
        return '/login';
      }
      if (loggedIn && onAuthRoute) {
        return '/';
      }
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (context, state) => const PhoneLoginScreen(),
      ),
      GoRoute(
        path: '/otp',
        name: 'otp',
        builder: (context, state) {
          final args = state.extra;
          if (args is! OtpRouteArgs) {
            return const PhoneLoginScreen();
          }
          return OtpScreen(args: args);
        },
      ),
      GoRoute(
        path: '/',
        name: 'home',
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: '/notes',
        name: 'notes',
        builder: (context, state) => const NotesListScreen(),
      ),
      GoRoute(
        path: '/notes/:noteId',
        name: 'noteDetail',
        builder: (context, state) {
          final noteId = state.pathParameters['noteId'] ?? '';
          return NoteDetailScreen(noteId: noteId);
        },
      ),
      GoRoute(
        path: '/papers/:paperId',
        name: 'paperDetail',
        builder: (context, state) {
          final paperId = state.pathParameters['paperId'] ?? '';
          return PaperDetailScreen(paperId: paperId);
        },
      ),
    ],
  );
});
