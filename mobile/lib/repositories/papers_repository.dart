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
    this.correctIndex,
    this.explanation,
    this.topic,
    required this.variantGroupId,
  });

  final String id;
  final int orderIndex;
  final String stem;
  final List<String> options;
  final int? correctIndex;
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
      correctIndex: json['correct_index'] as int?,
      explanation: json['explanation'] as String?,
      topic: json['topic'] as String?,
      variantGroupId: json['variant_group_id'] as String? ?? '',
    );
  }
}

class PaperSummary {
  PaperSummary({
    required this.id,
    this.noteId,
    this.batchFolderId,
    required this.title,
    required this.language,
    required this.status,
    required this.questionCount,
    required this.createdAt,
  });

  final String id;
  final String? noteId;
  final String? batchFolderId;
  final String title;
  final String language;
  final String status;
  final int questionCount;
  final DateTime createdAt;

  factory PaperSummary.fromJson(Map<String, dynamic> json) {
    return PaperSummary(
      id: json['id'] as String,
      noteId: json['note_id'] as String?,
      batchFolderId: json['batch_folder_id'] as String?,
      title: json['title'] as String? ?? 'Practice paper',
      language: json['language'] as String? ?? 'en',
      status: json['status'] as String? ?? 'ready',
      questionCount: json['question_count'] as int? ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class TestTopicFolder {
  TestTopicFolder({
    required this.topicId,
    required this.topicName,
    required this.latestTestAt,
    required this.testCount,
    required this.tests,
  });

  final String topicId;
  final String topicName;
  final DateTime latestTestAt;
  final int testCount;
  final List<PaperSummary> tests;

  factory TestTopicFolder.fromJson(Map<String, dynamic> json) {
    return TestTopicFolder(
      topicId: json['topic_id'] as String,
      topicName: json['topic_name'] as String? ?? 'Topic',
      latestTestAt: DateTime.parse(json['latest_test_at'] as String),
      testCount: json['test_count'] as int? ?? 0,
      tests: (json['tests'] as List<dynamic>? ?? [])
          .whereType<Map<String, dynamic>>()
          .map(PaperSummary.fromJson)
          .toList(),
    );
  }
}

class PaperDetail {
  PaperDetail({
    required this.id,
    this.noteId,
    this.batchFolderId,
    required this.title,
    required this.language,
    required this.status,
    required this.questionCount,
    required this.createdAt,
    required this.questions,
  });

  final String id;
  final String? noteId;
  final String? batchFolderId;
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
      noteId: json['note_id'] as String?,
      batchFolderId: json['batch_folder_id'] as String?,
      title: json['title'] as String? ?? 'Practice paper',
      language: json['language'] as String? ?? 'en',
      status: json['status'] as String? ?? 'ready',
      questionCount: json['question_count'] as int? ?? questions.length,
      createdAt: DateTime.parse(json['created_at'] as String),
      questions: questions,
    );
  }
}

class AttemptAnswerReview {
  AttemptAnswerReview({
    required this.questionId,
    required this.orderIndex,
    required this.stem,
    required this.options,
    required this.selectedIndex,
    required this.correctIndex,
    required this.isCorrect,
    this.explanation,
    this.topic,
  });

  final String questionId;
  final int orderIndex;
  final String stem;
  final List<String> options;
  final int selectedIndex;
  final int correctIndex;
  final bool isCorrect;
  final String? explanation;
  final String? topic;

  factory AttemptAnswerReview.fromJson(Map<String, dynamic> json) {
    final options = (json['options'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toList();
    return AttemptAnswerReview(
      questionId: json['question_id'] as String,
      orderIndex: json['order_index'] as int? ?? 0,
      stem: json['stem'] as String? ?? '',
      options: options,
      selectedIndex: json['selected_index'] as int? ?? 0,
      correctIndex: json['correct_index'] as int? ?? 0,
      isCorrect: json['is_correct'] as bool? ?? false,
      explanation: json['explanation'] as String?,
      topic: json['topic'] as String?,
    );
  }
}

class AttemptResult {
  AttemptResult({
    required this.id,
    required this.paperId,
    required this.correctCount,
    required this.totalCount,
    required this.scorePercent,
    required this.submittedAt,
    required this.answers,
  });

  final String id;
  final String paperId;
  final int correctCount;
  final int totalCount;
  final int scorePercent;
  final DateTime submittedAt;
  final List<AttemptAnswerReview> answers;

  factory AttemptResult.fromJson(Map<String, dynamic> json) {
    final answers = (json['answers'] as List<dynamic>? ?? [])
        .whereType<Map<String, dynamic>>()
        .map(AttemptAnswerReview.fromJson)
        .toList();
    return AttemptResult(
      id: json['id'] as String,
      paperId: json['paper_id'] as String,
      correctCount: json['correct_count'] as int? ?? 0,
      totalCount: json['total_count'] as int? ?? 0,
      scorePercent: json['score_percent'] as int? ?? 0,
      submittedAt: DateTime.parse(json['submitted_at'] as String),
      answers: answers,
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
          receiveTimeout: const Duration(seconds: 240),
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

  Future<PaperDetail> generatePaperFromBatch({
    required String batchId,
    required String language,
  }) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/batches/$batchId/generate-paper',
        data: {'language': language},
        options: Options(
          receiveTimeout: const Duration(seconds: 240),
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

  Future<PaperDetail> generatePaperFromTopics({
    required String examId,
    required List<String> batchIds,
    required String language,
  }) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/exams/$examId/generate-paper',
        data: {
          'batch_ids': batchIds,
          'language': language,
        },
        options: Options(
          receiveTimeout: const Duration(seconds: 240),
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

  Future<List<PaperSummary>> listPapers() async {
    try {
      final response = await _dio.get<List<dynamic>>('/papers');
      final data = response.data ?? [];
      return data
          .whereType<Map<String, dynamic>>()
          .map(PaperSummary.fromJson)
          .toList();
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<List<TestTopicFolder>> listTestTopicFolders() async {
    try {
      final response = await _dio.get<List<dynamic>>('/papers/topics');
      final data = response.data ?? [];
      return data
          .whereType<Map<String, dynamic>>()
          .map(TestTopicFolder.fromJson)
          .toList();
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

  Future<PaperSummary> renamePaper({
    required String paperId,
    required String title,
  }) async {
    try {
      final response = await _dio.patch<Map<String, dynamic>>(
        '/papers/$paperId',
        data: {'title': title},
      );
      final data = response.data;
      if (data == null) throw const ServerFailure('Empty paper response');
      return PaperSummary.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<AttemptResult> submitAttempt({
    required String paperId,
    required Map<String, int> selectedByQuestionId,
  }) async {
    try {
      final answers = selectedByQuestionId.entries
          .map(
            (e) => {
              'question_id': e.key,
              'selected_index': e.value,
            },
          )
          .toList();
      final response = await _dio.post<Map<String, dynamic>>(
        '/papers/$paperId/attempts',
        data: {'answers': answers},
      );
      final data = response.data;
      if (data == null) {
        throw const ServerFailure('Empty attempt response');
      }
      return AttemptResult.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<AttemptResult> getAttempt({
    required String paperId,
    required String attemptId,
  }) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/papers/$paperId/attempts/$attemptId',
      );
      final data = response.data;
      if (data == null) {
        throw const ServerFailure('Empty attempt response');
      }
      return AttemptResult.fromJson(data);
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
