import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';

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
    this.errorMessage,
    this.hasCanonical = false,
    this.sourceLanguage,
  });

  final String id;
  final String title;
  final String fileUrl;
  final String language;
  final String status;
  final DateTime createdAt;
  final String? errorMessage;
  final bool hasCanonical;
  final String? sourceLanguage;

  factory NoteItem.fromJson(Map<String, dynamic> json) {
    return NoteItem(
      id: json['id'] as String,
      title: json['title'] as String,
      fileUrl: json['file_url'] as String,
      language: json['language'] as String? ?? 'en',
      status: json['status'] as String? ?? 'uploaded',
      createdAt: DateTime.parse(json['created_at'] as String),
      errorMessage: json['error_message'] as String?,
      hasCanonical: json['has_canonical'] as bool? ?? false,
      sourceLanguage: json['source_language'] as String?,
    );
  }
}

class NoteDetail extends NoteItem {
  NoteDetail({
    required super.id,
    required super.title,
    required super.fileUrl,
    required super.language,
    required super.status,
    required super.createdAt,
    super.errorMessage,
    super.hasCanonical,
    super.sourceLanguage,
    this.rawExtractedText,
    this.canonicalContentEn,
  });

  final String? rawExtractedText;
  final String? canonicalContentEn;

  factory NoteDetail.fromJson(Map<String, dynamic> json) {
    final base = NoteItem.fromJson(json);
    return NoteDetail(
      id: base.id,
      title: base.title,
      fileUrl: base.fileUrl,
      language: base.language,
      status: base.status,
      createdAt: base.createdAt,
      errorMessage: base.errorMessage,
      hasCanonical: base.hasCanonical,
      sourceLanguage: base.sourceLanguage,
      rawExtractedText: json['raw_extracted_text'] as String?,
      canonicalContentEn: json['canonical_content_en'] as String?,
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

  Future<NoteDetail> getNote(String noteId) async {
    try {
      final response = await _dio.get<Map<String, dynamic>>('/notes/$noteId');
      final data = response.data;
      if (data == null) {
        throw const ServerFailure('Empty note response');
      }
      return NoteDetail.fromJson(data);
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
    String? batchFolderId,
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
        if (batchFolderId != null && batchFolderId.isNotEmpty)
          'batch_folder_id': batchFolderId,
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

  Future<NoteItem> processNote(String noteId) async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/notes/$noteId/process',
      );
      final data = response.data;
      if (data == null) {
        throw const ServerFailure('Empty process response');
      }
      return NoteItem.fromJson(data);
    } on DioException catch (error) {
      throw NetworkFailure(_dioMessage(error));
    } catch (error) {
      if (error is AppFailure) rethrow;
      throw UnexpectedFailure(error.toString());
    }
  }

  /// Downloads PDF bytes (auth) to a local temp file and returns the path.
  Future<String> downloadNotePdfToTemp({
    required String noteId,
    required String title,
  }) async {
    try {
      final response = await _dio.get<List<int>>(
        '/notes/$noteId/file',
        options: Options(
          responseType: ResponseType.bytes,
          receiveTimeout: const Duration(seconds: 120),
        ),
      );
      final bytes = response.data;
      if (bytes == null || bytes.isEmpty) {
        throw const ServerFailure('Empty PDF download');
      }

      final dir = await getTemporaryDirectory();
      final safe = title
          .replaceAll(RegExp(r'[^\w\s\.-]'), '')
          .trim()
          .replaceAll(RegExp(r'\s+'), '_');
      final name = (safe.isEmpty ? 'note' : safe);
      final fileName = name.toLowerCase().endsWith('.pdf') ? name : '$name.pdf';
      final file = File('${dir.path}/$fileName');
      await file.writeAsBytes(bytes, flush: true);
      return file.path;
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
