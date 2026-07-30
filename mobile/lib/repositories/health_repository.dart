import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/errors/app_failure.dart';
import '../services/api_client.dart';

class HealthRepository {
  HealthRepository(this._dio);

  final Dio _dio;

  Future<Map<String, dynamic>> check() async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/health');
      final data = response.data;
      if (data == null) {
        throw const ServerFailure('Empty health response');
      }
      return data;
    } on DioException catch (error) {
      throw NetworkFailure(error.message ?? 'Network request failed');
    } catch (error) {
      throw UnexpectedFailure(error.toString());
    }
  }
}

final healthRepositoryProvider = Provider<HealthRepository>((ref) {
  return HealthRepository(ref.watch(dioProvider));
});
