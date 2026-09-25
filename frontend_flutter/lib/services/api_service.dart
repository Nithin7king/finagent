import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';

class ApiResponse {
  final bool isSuccess;
  final int statusCode;
  final dynamic data;
  final String? errorMessage;

  ApiResponse({
    required this.isSuccess,
    required this.statusCode,
    this.data,
    this.errorMessage,
  });
}

class ApiService {
  static const String _tokenKey = 'finagent_token';

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  static Future<void> setToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
  }

  static Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
  }

  static Future<Map<String, String>> _getHeaders([bool isJson = true]) async {
    final token = await getToken();
    final headers = <String, String>{
      'Accept': 'application/json',
    };
    if (isJson) {
      headers['Content-Type'] = 'application/json';
    }
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  static Future<ApiResponse> get(String endpoint, [Map<String, String>? queryParams]) async {
    try {
      var uri = Uri.parse('${ApiConfig.baseUrl}$endpoint');
      if (queryParams != null && queryParams.isNotEmpty) {
        uri = uri.replace(queryParameters: queryParams);
      }
      final headers = await _getHeaders();
      final response = await http.get(uri, headers: headers);
      return _handleResponse(response);
    } catch (e) {
      return ApiResponse(
        isSuccess: false,
        statusCode: 0,
        errorMessage: 'Network error: $e',
      );
    }
  }

  static Future<ApiResponse> post(String endpoint, [dynamic body]) async {
    try {
      final uri = Uri.parse('${ApiConfig.baseUrl}$endpoint');
      final headers = await _getHeaders();
      final encodedBody = body != null ? jsonEncode(body) : null;
      final response = await http.post(uri, headers: headers, body: encodedBody);
      return _handleResponse(response);
    } catch (e) {
      return ApiResponse(
        isSuccess: false,
        statusCode: 0,
        errorMessage: 'Network error: $e',
      );
    }
  }

  static Future<ApiResponse> delete(String endpoint) async {
    try {
      final uri = Uri.parse('${ApiConfig.baseUrl}$endpoint');
      final headers = await _getHeaders();
      final response = await http.delete(uri, headers: headers);
      return _handleResponse(response);
    } catch (e) {
      return ApiResponse(
        isSuccess: false,
        statusCode: 0,
        errorMessage: 'Network error: $e',
      );
    }
  }

  static Future<ApiResponse> uploadPdfStatement(
    Uint8List fileBytes,
    String fileName, {
    String? password,
  }) async {
    try {
      final uri = Uri.parse('${ApiConfig.baseUrl}${ApiConfig.transactionsUpload}');
      final request = http.MultipartRequest('POST', uri);

      final token = await getToken();
      if (token != null && token.isNotEmpty) {
        request.headers['Authorization'] = 'Bearer $token';
      }

      request.files.add(
        http.MultipartFile.fromBytes(
          'file',
          fileBytes,
          filename: fileName,
        ),
      );

      if (password != null && password.isNotEmpty) {
        request.fields['password'] = password;
      }

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      return _handleResponse(response);
    } catch (e) {
      return ApiResponse(
        isSuccess: false,
        statusCode: 0,
        errorMessage: 'Upload failed: $e',
      );
    }
  }

  static ApiResponse _handleResponse(http.Response response) {
    dynamic parsedBody;
    try {
      if (response.body.isNotEmpty) {
        parsedBody = jsonDecode(response.body);
      }
    } catch (_) {
      parsedBody = response.body;
    }

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return ApiResponse(
        isSuccess: true,
        statusCode: response.statusCode,
        data: parsedBody,
      );
    } else {
      String? msg;
      if (parsedBody is Map && parsedBody.containsKey('detail')) {
        msg = parsedBody['detail'].toString();
      } else if (parsedBody is Map && parsedBody.containsKey('message')) {
        msg = parsedBody['message'].toString();
      } else {
        msg = 'Request failed with status ${response.statusCode}';
      }
      return ApiResponse(
        isSuccess: false,
        statusCode: response.statusCode,
        data: parsedBody,
        errorMessage: msg,
      );
    }
  }
}
