import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/exams_repository.dart';

class SetupExamScreen extends ConsumerStatefulWidget {
  const SetupExamScreen({super.key, this.allowSkipToHome = false});

  final bool allowSkipToHome;

  @override
  ConsumerState<SetupExamScreen> createState() => _SetupExamScreenState();
}

class _SetupExamScreenState extends ConsumerState<SetupExamScreen> {
  final _controller = TextEditingController();
  bool _saving = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final l10n = AppLocalizations.of(context);
    final name = _controller.text.trim();
    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l10n.setupExamRequired)),
      );
      return;
    }
    setState(() => _saving = true);
    try {
      final exam = await ref.read(examsRepositoryProvider).createExam(name);
      if (!mounted) return;
      context.go('/exams/${exam.id}');
    } catch (error) {
      if (!mounted) return;
      final message = error is AppFailure ? error.message : l10n.genericError;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: Text(l10n.setupExamTitle)),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                l10n.setupExamHeadline,
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                l10n.setupExamSubtitle,
                style: theme.textTheme.bodyLarge?.copyWith(
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: 24),
              TextField(
                controller: _controller,
                textInputAction: TextInputAction.done,
                onSubmitted: (_) => _save(),
                decoration: InputDecoration(
                  labelText: l10n.setupExamFieldLabel,
                  hintText: l10n.setupExamFieldHint,
                  border: const OutlineInputBorder(),
                ),
              ),
              const Spacer(),
              FilledButton(
                onPressed: _saving ? null : _save,
                child: _saving
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Text(l10n.setupExamContinue),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
