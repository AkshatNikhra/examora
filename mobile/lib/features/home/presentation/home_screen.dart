import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_theme.dart';
import '../../../repositories/me_repository.dart';

final homeSummaryProvider = FutureProvider.autoDispose<HomeSummary>((ref) {
  return ref.watch(meRepositoryProvider).fetchHomeSummary();
});

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  Timer? _greetingTimer;

  @override
  void initState() {
    super.initState();
    // Rebuild periodically so greeting tracks local time of day.
    _greetingTimer = Timer.periodic(const Duration(minutes: 1), (_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _greetingTimer?.cancel();
    super.dispose();
  }

  String _greeting() {
    final hour = DateTime.now().toLocal().hour;
    if (hour >= 5 && hour < 12) return 'Good morning';
    if (hour >= 12 && hour < 17) return 'Good afternoon';
    return 'Good evening';
  }

  String _initials(String? name) {
    if (name == null || name.trim().isEmpty) return 'EX';
    final parts = name.trim().split(RegExp(r'\s+'));
    if (parts.length == 1) return parts.first.substring(0, 1).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }

  String _relative(DateTime at) {
    final diff = DateTime.now().toLocal().difference(at.toLocal());
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays == 1) return 'Yesterday';
    if (diff.inDays < 7) return '${diff.inDays} days ago';
    return DateFormat.MMMd().format(at.toLocal());
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(homeSummaryProvider);

    return Scaffold(
      backgroundColor: AppTheme.cream,
      body: SafeArea(
        child: async.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text(
                error is AppFailure ? error.message : error.toString(),
                textAlign: TextAlign.center,
              ),
            ),
          ),
          data: (summary) {
            final name = summary.fullName ?? 'Student';
            return RefreshIndicator(
              onRefresh: () async {
                ref.invalidate(homeSummaryProvider);
                await ref.read(homeSummaryProvider.future);
              },
              child: ListView(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              _greeting(),
                              style: const TextStyle(
                                color: AppTheme.muted,
                                fontSize: 14,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              name,
                              style: const TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ],
                        ),
                      ),
                      GestureDetector(
                        onTap: () => context.go('/app/profile'),
                        child: CircleAvatar(
                          backgroundColor: const Color(0xFFD9D2F3),
                          foregroundColor: AppTheme.navy,
                          child: Text(
                            _initials(name),
                            style: const TextStyle(fontWeight: FontWeight.w800),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 18),
                  Row(
                    children: [
                      Expanded(
                        child: _StatCard(
                          icon: Icons.school_outlined,
                          value: '${summary.examsCount}',
                          label: 'Exams',
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: _StatCard(
                          icon: Icons.assignment_outlined,
                          value: summary.testsTaken == 0
                              ? '—'
                              : '${summary.testsTaken}',
                          label: 'Tests Taken',
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: _StatCard(
                          icon: Icons.auto_awesome,
                          value: (summary.testsTaken == 0 ||
                                  summary.avgScorePercent == null)
                              ? '—'
                              : '${summary.avgScorePercent}%',
                          label: 'Avg Score',
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'YOUR EXAMS',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.8,
                      color: AppTheme.muted,
                    ),
                  ),
                  const SizedBox(height: 10),
                  ...summary.exams.map(
                    (exam) => Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: _ExamTile(
                        badge: exam.badge ?? 'EX',
                        title: exam.name,
                        subtitle:
                            '${exam.batchCount} topic${exam.batchCount == 1 ? '' : 's'}',
                        onTap: () => context.push('/exams/${exam.id}'),
                      ),
                    ),
                  ),
                  OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(
                        color: AppTheme.border,
                        style: BorderStyle.solid,
                      ),
                      foregroundColor: AppTheme.muted,
                      minimumSize: const Size.fromHeight(52),
                    ),
                    onPressed: () => context.go('/app/exams'),
                    icon: const Icon(Icons.add),
                    label: const Text('Add another exam'),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'RECENT ACTIVITY',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.8,
                      color: AppTheme.muted,
                    ),
                  ),
                  const SizedBox(height: 10),
                  if (summary.recentActivity.isEmpty)
                    const Text(
                      'No activity yet. Upload notes or take a test.',
                      style: TextStyle(color: AppTheme.muted),
                    )
                  else
                    ...summary.recentActivity.map(
                      (a) => ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: CircleAvatar(
                          backgroundColor: AppTheme.border,
                          child: Icon(
                            a.kind == 'upload'
                                ? Icons.upload_file
                                : Icons.assignment_turned_in_outlined,
                            color: AppTheme.navy,
                            size: 20,
                          ),
                        ),
                        title: Text(
                          a.title,
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                        trailing: Text(
                          _relative(a.at),
                          style: const TextStyle(
                            color: AppTheme.muted,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.icon,
    required this.value,
    required this.label,
  });

  final IconData icon;
  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: AppTheme.navy, size: 20),
          const SizedBox(height: 10),
          Text(
            value,
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
          ),
          Text(
            label,
            style: const TextStyle(color: AppTheme.muted, fontSize: 12),
          ),
        ],
      ),
    );
  }
}

class _ExamTile extends StatelessWidget {
  const _ExamTile({
    required this.badge,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final String badge;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppTheme.border),
          ),
          child: Row(
            children: [
              CircleAvatar(
                backgroundColor: AppTheme.navy.withValues(alpha: 0.1),
                foregroundColor: AppTheme.navy,
                child: Text(
                  badge.length > 4 ? badge.substring(0, 4) : badge,
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                    Text(
                      subtitle,
                      style: const TextStyle(
                        color: AppTheme.muted,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: AppTheme.muted),
            ],
          ),
        ),
      ),
    );
  }
}
