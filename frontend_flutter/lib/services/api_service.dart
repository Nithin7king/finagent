import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user.dart';

class ApiService {
  static const String _tokenKey = 'finagent_jwt_token';

  // Configurable base URL:
  // Supports --dart-define=API_URL=... build flag
  // On Flutter web/desktop, default to http://localhost:5000/api
  // On Android emulator, 10.0.2.2:5000
  static String get baseUrl {
    const envUrl = String.fromEnvironment('API_URL');
    if (envUrl.isNotEmpty) return envUrl;

    if (kIsWeb) {
      return 'http://localhost:5000/api';
    } else if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:5000/api';
    }
    return 'http://localhost:5000/api';
  }

  /// System health check endpoint
  static Future<bool> checkHealth() async {
    try {
      final url = Uri.parse('$baseUrl/health');
      final response = await http.get(url).timeout(const Duration(seconds: 4));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

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

  static Future<Map<String, String>> _headers() async {
    final headers = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    final token = await getToken();
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  // ─── Auth ───────────────────────────────────────────────────────────────────

  static Future<AuthTokenResponse?> login(String email, String password) async {
    final url = Uri.parse('$baseUrl/auth/login');
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final auth = AuthTokenResponse.fromJson(data);
      await setToken(auth.accessToken);
      return auth;
    }
    return null;
  }

  static Future<AuthTokenResponse?> register({
    required String name,
    required String email,
    required String password,
    double monthlyIncome = 0.0,
    String currency = 'INR',
  }) async {
    final url = Uri.parse('$baseUrl/auth/register');
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'name': name,
        'email': email,
        'password': password,
        'monthly_income': monthlyIncome,
        'currency': currency,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final auth = AuthTokenResponse.fromJson(data);
      await setToken(auth.accessToken);
      return auth;
    }
    return null;
  }

  static Future<UserProfile?> getMe() async {
    final url = Uri.parse('$baseUrl/auth/me');
    final response = await http.get(url, headers: await _headers());

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return UserProfile.fromJson(data);
    }
    return null;
  }

  // ─── Transactions ───────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getTransactions({int perPage = 200}) async {
    final url = Uri.parse('$baseUrl/transactions?per_page=$perPage');
    final response = await http.get(url, headers: await _headers());
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Failed to load transactions (Status: ${response.statusCode})');
  }

  static Future<bool> addTransaction({
    required String description,
    required double amount,
    required String category,
    required String date,
  }) async {
    final url = Uri.parse('$baseUrl/transactions');
    final response = await http.post(
      url,
      headers: await _headers(),
      body: jsonEncode({
        'description': description,
        'amount': amount,
        'category': category,
        'date': date,
      }),
    );
    return response.statusCode == 200 || response.statusCode == 201;
  }

  static Future<bool> updateCategory(String txId, String category) async {
    final url = Uri.parse('$baseUrl/transactions/$txId');
    final response = await http.put(
      url,
      headers: await _headers(),
      body: jsonEncode({'category': category == 'Others' ? 'Other' : category}),
    );
    return response.statusCode == 200;
  }

  // ─── Analytics ──────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getSpendingSummary({int days = 30}) async {
    final url = Uri.parse('$baseUrl/analytics/summary?days=$days');
    final response = await http.get(url, headers: await _headers());
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return {};
  }

  static Future<Map<String, dynamic>> getAnomalies({int days = 30}) async {
    final url = Uri.parse('$baseUrl/analytics/anomalies?days=$days');
    final response = await http.get(url, headers: await _headers());
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return {'anomalies': [], 'count': 0};
  }

  static Future<Map<String, dynamic>> getSubscriptions() async {
    final url = Uri.parse('$baseUrl/analytics/subscriptions');
    final response = await http.get(url, headers: await _headers());
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return {};
  }

  static Future<Map<String, dynamic>> getForecast(int horizonDays) async {
    final url = Uri.parse('$baseUrl/analytics/forecast?horizon_days=$horizonDays');
    final response = await http.get(url, headers: await _headers());
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return {};
  }

  static Future<Map<String, dynamic>> getWhatIfSimulator({
    required String category,
    required double reductionPct,
  }) async {
    final encodedCat = Uri.encodeComponent(category);
    final url = Uri.parse('$baseUrl/analytics/what-if?category=$encodedCat&reduction_pct=$reductionPct&days=30');
    final response = await http.get(url, headers: await _headers());
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return {};
  }

  // ─── Goals ──────────────────────────────────────────────────────────────────

  static Future<List<dynamic>> getGoals() async {
    final url = Uri.parse('$baseUrl/goals');
    final response = await http.get(url, headers: await _headers());
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    return [];
  }

  static Future<bool> createGoal({
    required String name,
    required String description,
    required double targetAmount,
    double currentAmount = 0.0,
    String? targetDate,
  }) async {
    final url = Uri.parse('$baseUrl/goals');
    final response = await http.post(
      url,
      headers: await _headers(),
      body: jsonEncode({
        'name': name,
        'description': description,
        'target_amount': targetAmount,
        'current_amount': currentAmount,
        'target_date': targetDate,
      }),
    );
    return response.statusCode == 200 || response.statusCode == 201;
  }

  static Future<bool> contributeToGoal(String goalId, double amount) async {
    final url = Uri.parse('$baseUrl/goals/$goalId/contribute');
    final response = await http.post(
      url,
      headers: await _headers(),
      body: jsonEncode({'amount': amount}),
    );
    return response.statusCode == 200;
  }

  // ─── Chat ───────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> sendChatMessage(String message, String? sessionId) async {
    final url = Uri.parse('$baseUrl/chat');
    final response = await http.post(
      url,
      headers: await _headers(),
      body: jsonEncode({
        'message': message,
        'session_id': sessionId,
      }),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    throw Exception('Chat request failed: ${response.body}');
  }

  static Future<String> getWeeklyDigest() async {
    final url = Uri.parse('$baseUrl/chat/digest');
    final response = await http.get(url, headers: await _headers());
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['digest'] ?? 'Digest unavailable.';
    }
    return 'Digest unavailable.';
  }

  // ─── CSV Upload (Server ML Pipeline) ────────────────────────────────────────

  static Future<Map<String, dynamic>> uploadCsv(List<int> bytes, String filename) async {
    final url = Uri.parse('$baseUrl/transactions/upload-csv');
    final request = http.MultipartRequest('POST', url);

    final headers = await _headers();
    headers.forEach((k, v) {
      if (k.toLowerCase() != 'content-type') {
        request.headers[k] = v;
      }
    });

    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        bytes,
        filename: filename,
      ),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    final err = jsonDecode(response.body);
    throw Exception(err['detail'] ?? 'CSV upload failed');
  }
}
