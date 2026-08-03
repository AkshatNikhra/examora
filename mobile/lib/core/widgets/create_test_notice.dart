import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../l10n/app_localizations.dart';
import '../../repositories/me_repository.dart';

const _prefsKeyHideCreateTestTimeNotice = 'hide_create_test_time_notice';
const _prefsKeyHideCreateTestQuotaNotice = 'hide_create_test_quota_notice';

Future<bool> _showNoticeDialog({
  required BuildContext context,
  required String title,
  required String body,
  required String prefsKey,
}) async {
  final prefs = await SharedPreferences.getInstance();
  if (prefs.getBool(prefsKey) == true) {
    return true;
  }
  if (!context.mounted) return false;

  final l10n = AppLocalizations.of(context);
  var dontShowAgain = false;

  final continued = await showDialog<bool>(
    context: context,
    barrierDismissible: false,
    builder: (context) {
      return StatefulBuilder(
        builder: (context, setLocal) {
          return AlertDialog(
            title: Text(title),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(body),
                const SizedBox(height: 16),
                CheckboxListTile(
                  contentPadding: EdgeInsets.zero,
                  controlAffinity: ListTileControlAffinity.leading,
                  value: dontShowAgain,
                  title: Text(l10n.createTestNoticeDontShowAgain),
                  onChanged: (value) {
                    setLocal(() => dontShowAgain = value ?? false);
                  },
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, true),
                child: Text(l10n.createTestNoticeClose),
              ),
            ],
          );
        },
      );
    },
  );

  if (continued == true && dontShowAgain) {
    await prefs.setBool(prefsKey, true);
  }
  return continued == true;
}

/// Time + quota notices before MCQ generation (each has its own Don't show again).
/// Returns `true` if the create flow should continue.
Future<bool> showCreateTestNoticesIfNeeded(
  BuildContext context, {
  required PaperQuota? quota,
}) async {
  final l10n = AppLocalizations.of(context);

  final timeOk = await _showNoticeDialog(
    context: context,
    title: l10n.createTestNoticeTitle,
    body: l10n.createTestNoticeBody,
    prefsKey: _prefsKeyHideCreateTestTimeNotice,
  );
  if (!timeOk || !context.mounted) return false;

  if (quota == null) return true;

  final afterThis = (quota.remaining - 1).clamp(0, quota.limit);
  final quotaOk = await _showNoticeDialog(
    context: context,
    title: l10n.createTestQuotaNoticeTitle,
    body: l10n.createTestQuotaNoticeBody(
      quota.limit,
      afterThis,
      quota.windowDays,
    ),
    prefsKey: _prefsKeyHideCreateTestQuotaNotice,
  );
  return quotaOk;
}
