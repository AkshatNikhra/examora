import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';

/// Shared navy brand header for sign-up / sign-in.
class AuthBrandHeader extends StatelessWidget {
  const AuthBrandHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      bottom: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 28, 24, 28),
        child: Column(
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white54, width: 1.5),
              ),
              child: const Icon(
                Icons.school_rounded,
                color: Colors.white,
                size: 34,
              ),
            ),
            const SizedBox(height: 14),
            const Text(
              'Examora',
              style: TextStyle(
                color: Colors.white,
                fontSize: 32,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 10),
            Text(
              'Study smarter. Practice sharper.',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.95),
                fontSize: 16,
                fontWeight: FontWeight.w600,
                height: 1.3,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Notes → Practice Tests → Success',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.75),
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Cream sheet that sits under [AuthBrandHeader] on auth screens.
class AuthFormSheet extends StatelessWidget {
  const AuthFormSheet({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        width: double.infinity,
        decoration: const BoxDecoration(
          color: AppTheme.cream,
          borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
        ),
        child: SafeArea(
          top: false,
          // When the keyboard opens, available height shrinks. Scroll so the
          // form Column + Spacer don't overflow ("Bottom Overflowed by N px").
          child: LayoutBuilder(
            builder: (context, constraints) {
              return SingleChildScrollView(
                keyboardDismissBehavior:
                    ScrollViewKeyboardDismissBehavior.onDrag,
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: constraints.maxHeight),
                  child: IntrinsicHeight(child: child),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}
