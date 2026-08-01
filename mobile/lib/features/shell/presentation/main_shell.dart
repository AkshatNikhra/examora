import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_theme.dart';

class MainShell extends StatelessWidget {
  const MainShell({super.key, required this.child});

  final Widget child;

  static const _tabs = <({String path, String label, IconData icon, IconData selected})>[
    (
      path: '/app/home',
      label: 'Home',
      icon: Icons.home_outlined,
      selected: Icons.home,
    ),
    (
      path: '/app/exams',
      label: 'Exams',
      icon: Icons.school_outlined,
      selected: Icons.school,
    ),
    (
      path: '/app/tests',
      label: 'Tests',
      icon: Icons.assignment_outlined,
      selected: Icons.assignment,
    ),
    (
      path: '/app/profile',
      label: 'Profile',
      icon: Icons.person_outline,
      selected: Icons.person,
    ),
  ];

  int _indexFor(String location) {
    final i = _tabs.indexWhere((t) => location.startsWith(t.path));
    return i < 0 ? 0 : i;
  }

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).uri.path;
    final currentIndex = _indexFor(location);

    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.white,
        indicatorColor: AppTheme.navy.withValues(alpha: 0.12),
        selectedIndex: currentIndex,
        onDestinationSelected: (index) {
          final target = _tabs[index].path;
          if (location != target) {
            context.go(target);
          }
        },
        destinations: [
          for (final tab in _tabs)
            NavigationDestination(
              icon: Icon(tab.icon, color: AppTheme.muted),
              selectedIcon: Icon(tab.selected, color: AppTheme.navy),
              label: tab.label,
            ),
        ],
      ),
    );
  }
}
