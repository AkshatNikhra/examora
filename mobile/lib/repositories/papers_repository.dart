import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/errors/app_failure.dart';
import '../services/api_client.dart';

class PaperQuestionItem {
  PaperQuestionItem({
    required this.id,
    required this.orderIndex,
    required this.stem,
    required this.options,
    required this.correctIndex,
    this.explanation,
    this.topic,
    required this.variantGroupId,
  });

  final String id;
  final int orderIndex;
  final String stem;
  final List<String> options;
  final int correctIndex;
  final String? explanation;
  final String? topic;
  final String variantGroupId;

  factory PaperQuestionItem.fromJson(Map<String, dynamic> json) {
    final options = (json['options'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toList();
    return PaperQuestionItem(
      id: json['id'] as String,
      orderIndex: json['order_index'] as int? ?? 0,
      stem: json['stem'] as String? ?? '',
      options: options,
      correctIndex: json['correct_index'] as int? ?? 0,
      explanation: json['explanation'] as String?,
      topic: json['topic'] as String?,
      variantGroupId: json['variant_group_id'] as String? ?? '',
    );
  }
}

class PaperDetail {
  PaperDetail({
    required this.id,
    required this.noteId,
    required this.title,
    required this.language,
    required this.status,
    required this.questionCount,
    required this.createdAt,
    required this.questions,
  });

  final String id;
  final String noteId;
  final String title;
  final String language;
  final String status;
  final int questionCount;
  final DateTime createdAt;
  final List<PaperQuestionItem> questions;

  factory PaperDetail.fromJson(Map<String, dynamic> json) {
    final questions = (json['questions'] as List<dynamic>? ?? [])
        .whereType<Map<String, dynamic>>()
        .map(PaperQuestionItem.fromJson)
        .toList();
    return PaperDetail(
      id: json['id'] as String,
      noteId: json['note_id'] as String,
      title: json['title'] as String? ?? 'Practice paper',
      language: json['language'] as String? ?? 'en',
      status: json['status'] as String? ?? 'ready',
      questionCount: json['question_count'] as int? ?? questions.length,
      createdAt: DateTime.parse(json['created_at'] as String),
      questions: questions,
    );
  }
}

class PapersRepository {
  PapersRepository(this._dio);

  final Dio _dio;

  Future<PaperDetail> generatePaper({
    required String noteId,
    required String language,
  }) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/notes/$noteId/generate-paper',
        data: {'language': language},
        options: Options(
          receiveTimeout: const Duration(seconds: 120),
          sendTimeout: const Duration(seconds: 30),
        ),
      );
      final data = response.data;
      if (data == null) {
        throw const ServerFailure('Empty paper response');
      }
      return PaperDetail.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<PaperDetail> getPaper(String paperId) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/papers/$paperId');
      final data = response.data;
      if (data == null) {
        throw const ServerFailure('Empty paper response');
      }
      return PaperDetail.fromJson(data);
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

final papersRepositoryProvider = Provider<PapersRepository>((ref) {
  return PapersRepository(ref.watch(dioProvider));
});
