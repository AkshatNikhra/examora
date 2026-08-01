import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/errors/app_failure.dart';
import '../../../core/theme/app_theme.dart';
import '../../../l10n/app_localizations.dart';
import '../../../repositories/me_repository.dart';
import 'auth_providers.dart';
import 'otp_screen.dart';

class SignInScreen extends ConsumerStatefulWidget {
  const SignInScreen({super.key});

  @override
  ConsumerState<SignInScreen> createState() => _SignInScreenState();
}

class _SignInScreenState extends ConsumerState<SignInScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  bool _isLoading = false;
  String? _error;

  static const _noAccountMessage =
      'No account with this number. Try creating an account with it.';

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  String get _e164Phone {
    final digits = _phoneController.text.replaceAll(RegExp(r'\D'), '');
    return '+91$digits';
  }

  Future<void> _sendOtp() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });
    final auth = ref.read(authRepositoryProvider);
    final l10n = AppLocalizations.of(context);
    try {
      final hasAccount =
          await ref.read(meRepositoryProvider).phoneHasAccount(_e164Phone);
      if (!hasAccount) {
        if (!mounted) return;
        setState(() {
          _error = _noAccountMessage;
          _isLoading = false;
        });
        return;
      }

      final verificationId = await auth.sendOtp(
        phoneNumber: _e164Phone,
        onAutoVerified: (PhoneAuthCredential credential) async {
          await auth.signInWithCredential(credential);
        },
      );
      if (!mounted) return;
      context.push(
        '/otp',
        extra: OtpRouteArgs(
          verificationId: verificationId,
          phoneNumber: _e164Phone,
          isSignUp: false,
        ),
      );
    } on FirebaseAuthException catch (error) {
      setState(() => _error = error.message ?? l10n.genericError);
    } on AppFailure catch (error) {
      setState(() => _error = error.message);
    } catch (_) {
      setState(() => _error = l10n.genericError);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.cream,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 24, 24, 24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Sign in',
                  style: TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  "We'll send a 6-digit OTP to verify your number",
                  style: TextStyle(color: AppTheme.muted, fontSize: 15),
                ),
                const SizedBox(height: 28),
                const Text(
                  'MOBILE NUMBER',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.8,
                    color: Color(0xFF9A8570),
                  ),
                ),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  inputFormatters: [
                    FilteringTextInputFormatter.digitsOnly,
                    LengthLimitingTextInputFormatter(10),
                  ],
                  decoration: const InputDecoration(
                    prefixIcon: Padding(
                      padding: EdgeInsets.only(left: 12, right: 8),
                      child: Text(
                        'IN +91',
                        style: TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ),
                    prefixIconConstraints: BoxConstraints(minWidth: 0),
                    hintText: '10-digit number',
                  ),
                  validator: (value) {
                    final digits = (value ?? '').replaceAll(RegExp(r'\D'), '');
                    if (digits.length != 10) {
                      return 'Enter a valid 10-digit number';
                    }
                    return null;
                  },
                  onFieldSubmitted: (_) => _sendOtp(),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 10),
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                ],
                const SizedBox(height: 20),
                FilledButton(
                  onPressed: _isLoading ? null : _sendOtp,
                  child: _isLoading
                      ? const SizedBox(
                          height: 22,
                          width: 22,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text('Send OTP'),
                ),
                const Spacer(),
                TextButton(
                  onPressed: () => context.go('/signup'),
                  child: const Text.rich(
                    TextSpan(
                      text: "Don't have an account? ",
                      style: TextStyle(color: AppTheme.muted),
                      children: [
                        TextSpan(
                          text: 'Create account',
                          style: TextStyle(
                            color: AppTheme.navy,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
