import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/errors/app_failure.dart';
import '../services/api_client.dart';

class MeRepository {
  MeRepository(this._dio);

  final Dio _dio;

  /// Calls authenticated `GET /me` (Firebase Bearer token attached by Dio).
  Future<Map<String, dynamic>> fetchMe() async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/me');
      final data = response.data;
      if (data == null) {
        throw const ServerFailure('Empty /me response');
      }
      return data;
    } on DioException catch (error) {
      final detail = error.response?.data;
      final message = detail is Map && detail['detail'] != null
          ? detail['detail'].toString()
          : (error.message ?? 'Network request failed');
      throw NetworkFailure(message);
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }
}

final meRepositoryProvider = Provider<MeRepository>((ref) {
  return MeRepository(ref.watch(dioProvider));
});
