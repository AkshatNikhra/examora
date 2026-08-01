import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_theme.dart';
import '../../../repositories/me_repository.dart';

class OnboardingProfileScreen extends ConsumerStatefulWidget {
  const OnboardingProfileScreen({super.key});

  @override
  ConsumerState<OnboardingProfileScreen> createState() =>
      _OnboardingProfileScreenState();
}

class _OnboardingProfileScreenState
    extends ConsumerState<OnboardingProfileScreen> {
  final _nameController = TextEditingController();
  DateTime? _dob;
  String _language = 'en';
  bool _saving = false;

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _pickDob() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime(now.year - 18),
      firstDate: DateTime(1950),
      lastDate: now,
    );
    if (picked != null) setState(() => _dob = picked);
  }

  String get _dobIso {
    final d = _dob!;
    return '${d.year.toString().padLeft(4, '0')}-'
        '${d.month.toString().padLeft(2, '0')}-'
        '${d.day.toString().padLeft(2, '0')}';
  }

  Future<void> _continue() async {
    final name = _nameController.text.trim();
    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter your full name')),
      );
      return;
    }
    if (_dob == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Select your date of birth')),
      );
      return;
    }
    setState(() => _saving = true);
    try {
      await ref.read(meRepositoryProvider).saveOnboardingProfile(
            fullName: name,
            dateOfBirth: _dobIso,
            preferredPaperLanguage: _language,
          );
      if (!mounted) return;
      context.go('/onboarding/exams');
    } catch (error) {
      if (!mounted) return;
      final message = error is AppFailure ? error.message : error.toString();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.cream,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 20, 24, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'STEP 1 OF 2',
                style: TextStyle(
                  color: Color(0xFFE07A3D),
                  fontWeight: FontWeight.w800,
                  fontSize: 12,
                  letterSpacing: 1,
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                'Tell us about you',
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 8),
              const Text(
                'We’ll personalise your practice experience.',
                style: TextStyle(color: AppTheme.muted),
              ),
              const SizedBox(height: 28),
              TextField(
                controller: _nameController,
                textCapitalization: TextCapitalization.words,
                decoration: const InputDecoration(
                  labelText: 'Full name',
                  hintText: 'e.g. Rahul Kumar',
                ),
              ),
              const SizedBox(height: 14),
              InkWell(
                onTap: _pickDob,
                borderRadius: BorderRadius.circular(14),
                child: InputDecorator(
                  decoration: const InputDecoration(
                    labelText: 'Date of birth',
                  ),
                  child: Text(
                    _dob == null
                        ? 'Select date'
                        : '${_dob!.day}/${_dob!.month}/${_dob!.year}',
                    style: TextStyle(
                      color: _dob == null ? AppTheme.muted : AppTheme.ink,
                      fontSize: 16,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 18),
              const Text(
                'Preferred language for MCQs',
                style: TextStyle(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: _LangChip(
                      label: 'English',
                      selected: _language == 'en',
                      onTap: () => setState(() => _language = 'en'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _LangChip(
                      label: 'Hindi',
                      selected: _language == 'hi',
                      onTap: () => setState(() => _language = 'hi'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              const Text(
                'You can change this later from Settings.',
                style: TextStyle(color: AppTheme.muted, fontSize: 13),
              ),
              const Spacer(),
              FilledButton(
                onPressed: _saving ? null : _continue,
                child: _saving
                    ? const SizedBox(
                        height: 22,
                        width: 22,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text('Continue'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _LangChip extends StatelessWidget {
  const _LangChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          color: selected ? AppTheme.navy.withValues(alpha: 0.08) : Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: selected ? AppTheme.navy : AppTheme.border,
            width: selected ? 1.5 : 1,
          ),
        ),
        alignment: Alignment.center,
        child: Text(
          label,
          style: TextStyle(
            fontWeight: FontWeight.w700,
            color: selected ? AppTheme.navy : AppTheme.ink,
          ),
        ),
      ),
    );
  }
}
