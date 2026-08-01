import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/errors/app_failure.dart';
import '../services/api_client.dart';

class UserProfile {
  UserProfile({
    required this.id,
    required this.phone,
    this.fullName,
    this.dateOfBirth,
    this.preferredPaperLanguage,
    this.onboardingCompleted = false,
  });

  final String id;
  final String phone;
  final String? fullName;
  final String? dateOfBirth;
  final String? preferredPaperLanguage;
  final bool onboardingCompleted;

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] as String,
      phone: json['phone'] as String? ?? '',
      fullName: json['full_name'] as String?,
      dateOfBirth: json['date_of_birth'] as String?,
      preferredPaperLanguage: json['preferred_paper_language'] as String?,
      onboardingCompleted: json['onboarding_completed'] as bool? ?? false,
    );
  }
}

class ExamCatalogEntry {
  ExamCatalogEntry({
    required this.id,
    required this.name,
    required this.badge,
    this.isPopular = false,
  });

  final String id;
  final String name;
  final String badge;
  final bool isPopular;

  factory ExamCatalogEntry.fromJson(Map<String, dynamic> json) {
    return ExamCatalogEntry(
      id: json['id'] as String,
      name: json['name'] as String? ?? '',
      badge: json['badge'] as String? ?? '',
      isPopular: json['is_popular'] as bool? ?? false,
    );
  }
}

class HomeExamCard {
  HomeExamCard({
    required this.id,
    required this.name,
    this.badge,
    this.batchCount = 0,
  });

  final String id;
  final String name;
  final String? badge;
  final int batchCount;

  factory HomeExamCard.fromJson(Map<String, dynamic> json) {
    return HomeExamCard(
      id: json['id'] as String,
      name: json['name'] as String? ?? '',
      badge: json['badge'] as String?,
      batchCount: json['batch_count'] as int? ?? 0,
    );
  }
}

class HomeActivity {
  HomeActivity({
    required this.kind,
    required this.title,
    required this.at,
    this.subtitle,
  });

  final String kind;
  final String title;
  final String? subtitle;
  final DateTime at;

  factory HomeActivity.fromJson(Map<String, dynamic> json) {
    return HomeActivity(
      kind: json['kind'] as String? ?? '',
      title: json['title'] as String? ?? '',
      subtitle: json['subtitle'] as String?,
      at: DateTime.parse(json['at'] as String),
    );
  }
}

class HomeSummary {
  HomeSummary({
    this.fullName,
    this.examsCount = 0,
    this.testsTaken = 0,
    this.avgScorePercent,
    this.exams = const [],
    this.recentActivity = const [],
  });

  final String? fullName;
  final int examsCount;
  final int testsTaken;
  final int? avgScorePercent;
  final List<HomeExamCard> exams;
  final List<HomeActivity> recentActivity;

  factory HomeSummary.fromJson(Map<String, dynamic> json) {
    return HomeSummary(
      fullName: json['full_name'] as String?,
      examsCount: json['exams_count'] as int? ?? 0,
      testsTaken: json['tests_taken'] as int? ?? 0,
      avgScorePercent: json['avg_score_percent'] as int?,
      exams: (json['exams'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(HomeExamCard.fromJson)
          .toList(),
      recentActivity: (json['recent_activity'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(HomeActivity.fromJson)
          .toList(),
    );
  }
}

class MeRepository {
  MeRepository(this._dio);

  final Dio _dio;

  Future<UserProfile> fetchMe() async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/me');
      final data = response.data;
      if (data == null) throw const ServerFailure('Empty /me response');
      return UserProfile.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<UserProfile> saveOnboardingProfile({
    required String fullName,
    required String dateOfBirth,
    required String preferredPaperLanguage,
  }) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/me/onboarding/profile',
        data: {
          'full_name': fullName,
          'date_of_birth': dateOfBirth,
          'preferred_paper_language': preferredPaperLanguage,
        },
      );
      final data = response.data;
      if (data == null) throw const ServerFailure('Empty profile response');
      return UserProfile.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<UserProfile> saveOnboardingExams({
    required List<String> catalogIds,
    required List<String> customNames,
  }) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/me/onboarding/exams',
        data: {
          'catalog_ids': catalogIds,
          'custom_names': customNames,
        },
      );
      final data = response.data;
      if (data == null) throw const ServerFailure('Empty exams response');
      return UserProfile.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<List<ExamCatalogEntry>> listCatalog({String? query}) async {
    try {
      final response = await _dio.get<List<dynamic>>(
        '/exam-catalog',
        queryParameters: {
          if (query != null && query.trim().isNotEmpty) 'q': query.trim(),
        },
      );
      final data = response.data ?? [];
      return data
          .whereType<Map<String, dynamic>>()
          .map(ExamCatalogEntry.fromJson)
          .toList();
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<ExamCatalogEntry> addCatalogExam(String name) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/exam-catalog',
        data: {'name': name},
      );
      final data = response.data;
      if (data == null) throw const ServerFailure('Empty catalog response');
      return ExamCatalogEntry.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<HomeSummary> fetchHomeSummary() async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/me/summary');
      final data = response.data;
      if (data == null) throw const ServerFailure('Empty summary response');
      return HomeSummary.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  String _dioMessage(DioException error) {
    final detail = error.response?.data;
    if (detail is Map && detail['detail'] != null) {
      return detail['detail'].toString();
    }
    return error.message ?? 'Network request failed';
  }
}

final meRepositoryProvider = Provider<MeRepository>((ref) {
  return MeRepository(ref.watch(dioProvider));
});

final meProfileProvider = FutureProvider.autoDispose<UserProfile>((ref) {
  return ref.watch(meRepositoryProvider).fetchMe();
});
