/// App-wide constants.
abstract final class AppConstants {
  /// Default local backend for Android emulator.
  /// Physical device: use your machine LAN IP instead.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );
}
