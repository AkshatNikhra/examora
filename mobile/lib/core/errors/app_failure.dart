/// Typed failures for UI and repositories.
sealed class AppFailure implements Exception {
  const AppFailure(this.message);

  final String message;

  @override
  String toString() => message;
}

final class NetworkFailure extends AppFailure {
  const NetworkFailure([super.message = 'Network request failed']);
}

final class ServerFailure extends AppFailure {
  const ServerFailure([super.message = 'Server error']);
}

final class UnexpectedFailure extends AppFailure {
  const UnexpectedFailure([super.message = 'Unexpected error']);
}
