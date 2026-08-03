import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/errors/app_failure.dart';
import '../services/api_client.dart';
import 'notes_repository.dart';

class ExamItem {
  ExamItem({
    required this.id,
    required this.name,
    required this.createdAt,
    this.batchCount = 0,
    this.canDelete = true,
  });

  final String id;
  final String name;
  final DateTime createdAt;
  final int batchCount;
  final bool canDelete;

  factory ExamItem.fromJson(Map<String, dynamic> json) {
    return ExamItem(
      id: json['id'] as String,
      name: json['name'] as String? ?? '',
      createdAt: DateTime.parse(json['created_at'] as String),
      batchCount: json['batch_count'] as int? ?? 0,
      canDelete: json['can_delete'] as bool? ?? true,
    );
  }
}

class BatchItem {
  BatchItem({
    required this.id,
    required this.examId,
    required this.name,
    required this.createdAt,
    this.noteCount = 0,
    this.hasPaper = false,
    this.canDelete = true,
  });

  final String id;
  final String examId;
  final String name;
  final DateTime createdAt;
  final int noteCount;
  final bool hasPaper;
  final bool canDelete;

  factory BatchItem.fromJson(Map<String, dynamic> json) {
    return BatchItem(
      id: json['id'] as String,
      examId: json['exam_id'] as String,
      name: json['name'] as String? ?? '',
      createdAt: DateTime.parse(json['created_at'] as String),
      noteCount: json['note_count'] as int? ?? 0,
      hasPaper: json['has_paper'] as bool? ?? false,
      canDelete: json['can_delete'] as bool? ?? true,
    );
  }
}

class ExamUploadHint {
  ExamUploadHint({
    required this.suggestNewBatch,
    this.reason,
    this.batchesWithPapers = const [],
  });

  final bool suggestNewBatch;
  final String? reason;
  final List<String> batchesWithPapers;

  factory ExamUploadHint.fromJson(Map<String, dynamic> json) {
    final ids = (json['batches_with_papers'] as List<dynamic>? ?? [])
        .map((e) => e.toString())
        .toList();
    return ExamUploadHint(
      suggestNewBatch: json['suggest_new_batch'] as bool? ?? false,
      reason: json['reason'] as String?,
      batchesWithPapers: ids,
    );
  }
}

class ExamsRepository {
  ExamsRepository(this._dio);

  final Dio _dio;

  Future<List<ExamItem>> listExams() async {
    try {
      final response = await _dio.get<List<dynamic>>('/exams');
      final data = response.data ?? [];
      return data
          .whereType<Map<String, dynamic>>()
          .map(ExamItem.fromJson)
          .toList();
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<ExamItem> createExam(String name) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/exams',
        data: {'name': name},
      );
      final data = response.data;
      if (data == null) throw const ServerFailure('Empty exam response');
      return ExamItem.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<ExamItem> renameExam({
    required String examId,
    required String name,
  }) async {
    try {
      final response = await _dio.patch<Map<String, dynamic>>(
        '/exams/$examId',
        data: {'name': name},
      );
      final data = response.data;
      if (data == null) throw const ServerFailure('Empty exam response');
      return ExamItem.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<void> deleteExam(String examId) async {
    try {
      await _dio.delete<void>('/exams/$examId');
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<ExamItem> getExam(String examId) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/exams/$examId');
      final data = response.data;
      if (data == null) throw const ServerFailure('Empty exam response');
      return ExamItem.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<List<BatchItem>> listBatches(String examId) async {
    try {
      final response = await _dio.get<List<dynamic>>('/exams/$examId/batches');
      final data = response.data ?? [];
      return data
          .whereType<Map<String, dynamic>>()
          .map(BatchItem.fromJson)
          .toList();
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<BatchItem> createBatch({
    required String examId,
    required String name,
  }) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/exams/$examId/batches',
        data: {'name': name},
      );
      final data = response.data;
      if (data == null) throw const ServerFailure('Empty batch response');
      return BatchItem.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<BatchItem> renameBatch({
    required String batchId,
    required String name,
  }) async {
    try {
      final response = await _dio.patch<Map<String, dynamic>>(
        '/batches/$batchId',
        data: {'name': name},
      );
      final data = response.data;
      if (data == null) throw const ServerFailure('Empty batch response');
      return BatchItem.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<void> deleteBatch(String batchId) async {
    try {
      await _dio.delete<void>('/batches/$batchId');
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<BatchItem> getBatch(String batchId) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/batches/$batchId');
      final data = response.data;
      if (data == null) throw const ServerFailure('Empty batch response');
      return BatchItem.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<List<NoteItem>> listBatchNotes(String batchId) async {
    try {
      final response = await _dio.get<List<dynamic>>('/batches/$batchId/notes');
      final data = response.data ?? [];
      return data
          .whereType<Map<String, dynamic>>()
          .map(NoteItem.fromJson)
          .toList();
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  Future<ExamUploadHint> uploadHint(String examId) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '/exams/$examId/upload-hint',
      );
      final data = response.data;
      if (data == null) throw const ServerFailure('Empty hint response');
      return ExamUploadHint.fromJson(data);
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

final examsRepositoryProvider = Provider<ExamsRepository>((ref) {
  return ExamsRepository(ref.watch(dioProvider));
});
