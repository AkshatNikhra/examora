import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/errors/app_failure.dart';
import '../services/api_client.dart';

class NoteItem {
  NoteItem({
    required this.id,
    required this.title,
    required this.fileUrl,
    required this.language,
    required this.status,
    required this.createdAt,
  });

  final String id;
  final String title;
  final String fileUrl;
  final String language;
  final String status;
  final DateTime createdAt;

  factory NoteItem.fromJson(Map<String, dynamic> json) {
    return NoteItem(
      id: json['id'] as String,
      title: json['title'] as String,
      fileUrl: json['file_url'] as String,
      language: json['language'] as String? ?? 'en',
      status: json['status'] as String? ?? 'uploaded',
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class NotesRepository {
  NotesRepository(this._dio);

  final Dio _dio;

  Future<List<NoteItem>> listNotes() async {
    try {
      final response = await _dio.get<List<dynamic>>('/notes');
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

  Future<NoteItem> uploadPdf({
    required String filePath,
    required String fileName,
    String? title,
    String language = 'en',
    void Function(int sent, int total)? onProgress,
  }) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          filePath,
          filename: fileName,
        ),
        if (title != null && title.trim().isNotEmpty) 'title': title.trim(),
        'language': language,
      });

      final response = await _dio.post<Map<String, dynamic>>(
        '/notes',
        data: formData,
        onSendProgress: onProgress,
      );
      final data = response.data;
      if (data == null) {
        throw const ServerFailure('Empty upload response');
      }
      return NoteItem.fromJson(data);
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

final notesRepositoryProvider = Provider<NotesRepository>((ref) {
  return NotesRepository(ref.watch(dioProvider));
});
