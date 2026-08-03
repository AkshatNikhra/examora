import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_theme.dart';
import '../../../features/auth/presentation/auth_providers.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/me_repository.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  bool _savingLanguage = false;

  Future<void> _logout() async {
    await ref.read(authRepositoryProvider).signOut();
    if (mounted) {
      context.go('/signin');
    }
  }

  Future<void> _changeLanguage(UserProfile profile) async {
    final l10n = AppLocalizations.of(context);
    final current = (profile.preferredPaperLanguage ?? 'en').toLowerCase();
    final selected = await showModalBottomSheet<String>(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(8, 12, 8, 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Padding(
                  padding: EdgeInsets.fromLTRB(16, 4, 16, 12),
                  child: Text(
                    'Preferred MCQ language',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
                ListTile(
                  title: Text(l10n.paperLanguageEnglish),
                  trailing: current == 'en'
                      ? const Icon(Icons.check, color: AppTheme.navy)
                      : null,
                  onTap: () => Navigator.pop(context, 'en'),
                ),
                ListTile(
                  title: Text(l10n.paperLanguageHindi),
                  trailing: current == 'hi'
                      ? const Icon(Icons.check, color: AppTheme.navy)
                      : null,
                  onTap: () => Navigator.pop(context, 'hi'),
                ),
              ],
            ),
          ),
        );
      },
    );
    if (selected == null || selected == current || !mounted) return;

    setState(() => _savingLanguage = true);
    try {
      await ref.read(meRepositoryProvider).updatePreferredLanguage(selected);
      ref.invalidate(meProfileProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            selected == 'hi'
                ? 'MCQ language set to Hindi'
                : 'MCQ language set to English',
          ),
        ),
      );
    } catch (error) {
      if (!mounted) return;
      final message = error is AppFailure ? error.message : error.toString();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    } finally {
      if (mounted) setState(() => _savingLanguage = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final me = ref.watch(meProfileProvider);
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      backgroundColor: AppTheme.cream,
      appBar: AppBar(
        title: const Text(
          'Profile',
          style: TextStyle(
            fontSize: 26,
            fontWeight: FontWeight.w800,
          ),
        ),
        titleTextStyle: const TextStyle(
          color: AppTheme.ink,
          fontSize: 26,
          fontWeight: FontWeight.w800,
        ),
      ),
      body: me.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(e.toString(), textAlign: TextAlign.center),
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: _logout,
                  child: const Text('Log out'),
                ),
              ],
            ),
          ),
        ),
        data: (profile) {
          final lang = (profile.preferredPaperLanguage ?? 'en').toLowerCase();
          final langLabel = lang == 'hi'
              ? l10n.paperLanguageHindi
              : l10n.paperLanguageEnglish;
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              CircleAvatar(
                radius: 40,
                backgroundColor: AppTheme.navy.withValues(alpha: 0.12),
                foregroundColor: AppTheme.navy,
                child: Text(
                  _initials(profile.fullName),
                  style: const TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                profile.fullName ?? 'Student',
                style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800),
              ),
              if (profile.accountTypeLabel != null) ...[
                const SizedBox(height: 4),
                Text(
                  profile.accountTypeLabel!,
                  style: const TextStyle(
                    color: AppTheme.muted,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
              const SizedBox(height: 6),
              Text(
                profile.phone,
                style: const TextStyle(
                  color: AppTheme.muted,
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 28),
              const Text(
                'PREFERENCES',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.8,
                  color: AppTheme.muted,
                ),
              ),
              const SizedBox(height: 10),
              Material(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 10,
                  ),
                  title: const Text(
                    'MCQ language',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  subtitle: Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text(
                      langLabel,
                      style: const TextStyle(
                        fontSize: 14,
                        color: AppTheme.muted,
                      ),
                    ),
                  ),
                  trailing: _savingLanguage
                      ? const SizedBox(
                          width: 22,
                          height: 22,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.chevron_right),
                  onTap: _savingLanguage ? null : () => _changeLanguage(profile),
                ),
              ),
              const SizedBox(height: 40),
              FilledButton.icon(
                onPressed: _logout,
                icon: const Icon(Icons.logout),
                label: const Text(
                  'Log out',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  String _initials(String? name) {
    if (name == null || name.trim().isEmpty) return 'EX';
    final parts = name.trim().split(RegExp(r'\s+'));
    if (parts.length == 1) {
      return parts.first.substring(0, 1).toUpperCase();
    }
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
}
