import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/theme/app_theme.dart';
import '../../../l10n/app_localizations.dart';
import 'auth_brand_header.dart';
import 'auth_providers.dart';
import 'otp_screen.dart';

class SignUpScreen extends ConsumerStatefulWidget {
  const SignUpScreen({super.key});

  @override
  ConsumerState<SignUpScreen> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends ConsumerState<SignUpScreen> {
  final _formKey = GlobalKey<FormState>();
  final _phoneController = TextEditingController();
  bool _isLoading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _phoneController.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _phoneController.dispose();
    super.dispose();
  }

  String get _e164Phone {
    final digits = _phoneController.text.replaceAll(RegExp(r'\D'), '');
    return '+91$digits';
  }

  bool get _isPhoneValid {
    final digits = _phoneController.text.replaceAll(RegExp(r'\D'), '');
    return digits.length == 10;
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
          isSignUp: true,
        ),
      );
    } on FirebaseAuthException catch (error) {
      setState(() => _error = error.message ?? l10n.genericError);
    } catch (_) {
      setState(() => _error = l10n.genericError);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.navy,
      body: Column(
        children: [
          const AuthBrandHeader(),
          AuthFormSheet(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(24, 28, 24, 16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                      'Create your account',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.ink,
                      ),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      "We'll send a 6-digit OTP to verify your number",
                      style: TextStyle(color: AppTheme.muted, fontSize: 14),
                    ),
                    const SizedBox(height: 24),
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
                            style: TextStyle(
                              fontWeight: FontWeight.w700,
                              color: AppTheme.ink,
                            ),
                          ),
                        ),
                        prefixIconConstraints: BoxConstraints(minWidth: 0),
                        hintText: '10-digit number',
                      ),
                      validator: (value) {
                        final digits =
                            (value ?? '').replaceAll(RegExp(r'\D'), '');
                        if (digits.length != 10) {
                          return 'Enter a valid 10-digit number';
                        }
                        return null;
                      },
                      onFieldSubmitted: (_) => _sendOtp(),
                    ),
                    if (_error != null) ...[
                      const SizedBox(height: 10),
                      Text(
                        _error!,
                        style: const TextStyle(color: Colors.red),
                      ),
                    ],
                    const SizedBox(height: 16),
                    FilledButton(
                      style: FilledButton.styleFrom(
                        backgroundColor: AppTheme.creamButton,
                        foregroundColor: AppTheme.ink,
                      ),
                      onPressed:
                          (_isLoading || !_isPhoneValid) ? null : _sendOtp,
                      child: _isLoading
                          ? const SizedBox(
                              height: 22,
                              width: 22,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                              ),
                            )
                          : const Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.phone_iphone, size: 18),
                                SizedBox(width: 8),
                                Text('Send OTP'),
                              ],
                            ),
                    ),
                    const SizedBox(height: 16),
                    TextButton(
                      onPressed: () => context.go('/signin'),
                      child: const Text.rich(
                        TextSpan(
                          text: 'Already have an account? ',
                          style: TextStyle(color: AppTheme.muted),
                          children: [
                            TextSpan(
                              text: 'Sign in',
                              style: TextStyle(
                                color: AppTheme.navy,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const Spacer(),
                    const Text(
                      'By continuing you agree to our Terms of Use and Privacy Policy',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 11, color: AppTheme.muted),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
