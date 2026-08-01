import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_theme.dart';
import '../../../repositories/me_repository.dart';

class OnboardingExamsScreen extends ConsumerStatefulWidget {
  const OnboardingExamsScreen({super.key});

  @override
  ConsumerState<OnboardingExamsScreen> createState() =>
      _OnboardingExamsScreenState();
}

class _OnboardingExamsScreenState extends ConsumerState<OnboardingExamsScreen> {
  final _searchController = TextEditingController();
  List<ExamCatalogEntry> _items = [];
  final Set<String> _selectedIds = {};
  bool _loading = true;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _load({String? query}) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final items =
          await ref.read(meRepositoryProvider).listCatalog(query: query);
      if (!mounted) return;
      setState(() {
        _items = items;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = error is AppFailure ? error.message : error.toString();
      });
    }
  }

  Future<void> _addCustom() async {
    final query = _searchController.text.trim();
    if (query.isEmpty) return;
    final exists = _items.any(
      (e) => e.name.toLowerCase() == query.toLowerCase(),
    );
    if (exists) return;
    try {
      final created =
          await ref.read(meRepositoryProvider).addCatalogExam(query);
      if (!mounted) return;
      setState(() {
        _items = [created, ..._items];
        _selectedIds.add(created.id);
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Added “${created.name}” to exam list')),
      );
    } catch (error) {
      if (!mounted) return;
      final message = error is AppFailure ? error.message : error.toString();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  Future<void> _continue() async {
    if (_selectedIds.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Select at least one exam')),
      );
      return;
    }
    setState(() => _saving = true);
    try {
      await ref.read(meRepositoryProvider).saveOnboardingExams(
            catalogIds: _selectedIds.toList(),
            customNames: const [],
          );
      if (!mounted) return;
      context.go('/app/home');
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
    final query = _searchController.text.trim();
    final exactMatch = _items.any(
      (e) => e.name.toLowerCase() == query.toLowerCase(),
    );
    final showAdd = query.isNotEmpty && !exactMatch && !_loading;

    return Scaffold(
      backgroundColor: AppTheme.cream,
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 20, 24, 0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'STEP 2 OF 2',
                    style: TextStyle(
                      color: Color(0xFFE07A3D),
                      fontWeight: FontWeight.w800,
                      fontSize: 12,
                      letterSpacing: 1,
                    ),
                  ),
                  const SizedBox(height: 10),
                  const Text(
                    'Which exam are you preparing for?',
                    style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Select one or more. You can add more later.',
                    style: TextStyle(color: AppTheme.muted),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _searchController,
                    decoration: InputDecoration(
                      hintText: 'Search exams',
                      prefixIcon: const Icon(Icons.search),
                      suffixIcon: IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          _load();
                        },
                      ),
                    ),
                    onChanged: (v) => _load(query: v),
                  ),
                ],
              ),
            ),
            if (showAdd)
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 12, 24, 0),
                child: OutlinedButton.icon(
                  onPressed: _addCustom,
                  icon: const Icon(Icons.add),
                  label: Text('Add “$query” to exam list'),
                ),
              ),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : _error != null
                      ? Center(child: Text(_error!))
                      : ListView.separated(
                          padding: const EdgeInsets.fromLTRB(24, 16, 24, 24),
                          itemCount: _items.length,
                          separatorBuilder: (_, _) => const SizedBox(height: 10),
                          itemBuilder: (context, index) {
                            final item = _items[index];
                            final selected = _selectedIds.contains(item.id);
                            return InkWell(
                              onTap: () {
                                setState(() {
                                  if (selected) {
                                    _selectedIds.remove(item.id);
                                  } else {
                                    _selectedIds.add(item.id);
                                  }
                                });
                              },
                              borderRadius: BorderRadius.circular(16),
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 16,
                                  vertical: 16,
                                ),
                                decoration: BoxDecoration(
                                  color: selected
                                      ? AppTheme.navy.withValues(alpha: 0.08)
                                      : Colors.white,
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(
                                    color: selected
                                        ? AppTheme.navy
                                        : AppTheme.border,
                                    width: selected ? 1.5 : 1,
                                  ),
                                ),
                                child: Row(
                                  children: [
                                    Expanded(
                                      child: Text(
                                        item.name,
                                        style: TextStyle(
                                          fontWeight: FontWeight.w700,
                                          color: selected
                                              ? AppTheme.navy
                                              : AppTheme.ink,
                                        ),
                                      ),
                                    ),
                                    if (selected)
                                      const Icon(
                                        Icons.check_circle,
                                        color: AppTheme.navy,
                                      ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 16),
              child: FilledButton(
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
                    : Text(
                        _selectedIds.isEmpty
                            ? 'Continue'
                            : 'Continue with ${_selectedIds.length} exam${_selectedIds.length == 1 ? '' : 's'}',
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
