import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import '../config/api_config.dart';
import '../models/user_model.dart';
import '../models/transaction_model.dart';
import '../models/subscription_model.dart';
import '../models/goal_model.dart';
import '../models/chat_model.dart';
import '../models/forecast_model.dart';
import '../services/api_service.dart';

class FinProvider extends ChangeNotifier {
  UserProfile? _user;
  KycData? _kycData;
  List<Transaction> _transactions = [];
  List<Goal> _goals = [];
  List<Subscription> _subscriptions = [];
  CreepAnalysis? _creepAnalysis;
  List<ChatMessage> _chatHistory = [];
  DashboardSummary _summary = DashboardSummary();
  List<ForecastPoint> _forecast = [];
  List<Anomaly> _activeAnomalies = [];
  final Map<String, GoalRecommendationData> _goalRecommendations = {};
  final Map<String, bool> _loadingGoalRecs = {};

  bool _isLoading = false;
  bool _isInitialized = false;
  bool _isChatLoading = false;
  String? _sessionId;

  // Getters
  UserProfile? get user => _user;
  KycData? get kycData => _kycData;
  List<Transaction> get transactions => _transactions;
  List<Goal> get goals => _goals;
  List<Subscription> get subscriptions => _subscriptions;
  CreepAnalysis? get creepAnalysis => _creepAnalysis;
  List<ChatMessage> get chatHistory => _chatHistory;
  DashboardSummary get summary => _summary;
  List<ForecastPoint> get forecast => _forecast;
  List<Anomaly> get activeAnomalies => _activeAnomalies;
  GoalRecommendationData? getGoalRecommendation(String goalId) => _goalRecommendations[goalId];
  bool isGoalRecLoading(String goalId) => _loadingGoalRecs[goalId] == true;
  bool get isLoading => _isLoading;
  bool get isInitialized => _isInitialized;
  bool get isChatLoading => _isChatLoading;
  bool get isAuthenticated => _user != null;

  String? _authError;
  String? get authError => _authError;

  FinProvider() {
    _initialize();
  }

  Future<void> _initialize() async {
    final token = await ApiService.getToken();
    if (token != null && token.isNotEmpty) {
      await _fetchUserProfile();
      if (_user != null) {
        await refreshAllData();
      }
    }

    _isInitialized = true;
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _authError = null;
    notifyListeners();

    final res = await ApiService.post(ApiConfig.authLogin, {
      'email': email,
      'password': password,
    });

    if (res.isSuccess && res.data is Map && res.data['access_token'] != null) {
      final token = res.data['access_token'].toString();
      await ApiService.setToken(token);
      await _fetchUserProfile();
      await refreshAllData();
      _isLoading = false;
      notifyListeners();
      return true;
    }

    _authError = res.errorMessage ?? 'Invalid email or password. Please try again.';
    _isLoading = false;
    notifyListeners();
    return false;
  }

  Future<bool> register(String name, String email, String password, double monthlyIncome) async {
    _isLoading = true;
    notifyListeners();

    final res = await ApiService.post(ApiConfig.authRegister, {
      'name': name,
      'email': email,
      'password': password,
      'monthly_income': monthlyIncome,
    });

    if (res.isSuccess && res.data is Map && res.data['access_token'] != null) {
      final token = res.data['access_token'].toString();
      await ApiService.setToken(token);
      await _fetchUserProfile();
      await refreshAllData();
      _isLoading = false;
      notifyListeners();
      return true;
    }

    _isLoading = false;
    notifyListeners();
    return false;
  }

  Future<void> logout() async {
    await ApiService.clearToken();
    _user = null;
    _kycData = null;
    _transactions = [];
    _goals = [];
    _subscriptions = [];
    _chatHistory = [];
    _activeAnomalies = [];
    _goalRecommendations.clear();
    _loadingGoalRecs.clear();
    _summary = DashboardSummary();
    notifyListeners();
  }

  Future<void> _fetchUserProfile() async {
    final res = await ApiService.get(ApiConfig.authMe);
    if (res.isSuccess && res.data is Map) {
      _user = UserProfile.fromJson(Map<String, dynamic>.from(res.data));
    }
  }

  Future<void> refreshAllData() async {
    await Future.wait([
      _fetchTransactions(),
      _fetchDashboardSummary(),
      _fetchSubscriptions(),
      _fetchGoals(),
      _fetchAnomalies(),
      _fetchForecast(),
      fetchKycStatus(),
    ]);
    notifyListeners();
  }

  Future<void> _fetchTransactions() async {
    final res = await ApiService.get(ApiConfig.transactions);
    if (res.isSuccess && res.data is List) {
      double runningBalance = 0.0;
      final rawList = List<Map<String, dynamic>>.from(res.data);
      final reversed = rawList.reversed.toList();
      final List<Transaction> mapped = [];
      for (final row in reversed) {
        final amt = (row['amount'] as num?)?.toDouble() ?? 0.0;
        runningBalance += amt;
        mapped.add(Transaction.fromJson(row, runningBalance));
      }
      _transactions = mapped.reversed.toList();
    }
  }

  Future<void> _fetchDashboardSummary() async {
    final res = await ApiService.get(ApiConfig.analyticsSummary);
    if (res.isSuccess && res.data is Map) {
      _summary = DashboardSummary.fromJson(Map<String, dynamic>.from(res.data));
    }
  }

  Future<void> _fetchSubscriptions() async {
    final res = await ApiService.get(ApiConfig.analyticsSubscriptions);
    if (res.isSuccess && res.data is Map) {
      final list = (res.data['subscriptions'] as List<dynamic>?) ?? [];
      _subscriptions = list.map((e) => Subscription.fromJson(Map<String, dynamic>.from(e))).toList();
      if (res.data['creep_analysis'] != null) {
        _creepAnalysis = CreepAnalysis.fromJson(Map<String, dynamic>.from(res.data['creep_analysis']));
      }
    }
  }

  Future<void> _fetchGoals() async {
    final res = await ApiService.get(ApiConfig.goals);
    if (res.isSuccess && res.data is List) {
      _goals = (res.data as List<dynamic>)
          .map((e) => Goal.fromJson(Map<String, dynamic>.from(e)))
          .toList();
    }
  }

  Future<void> _fetchAnomalies() async {
    final res = await ApiService.get(ApiConfig.analyticsAnomalies);
    if (res.isSuccess && res.data is List) {
      _activeAnomalies = (res.data as List<dynamic>)
          .map((e) => Anomaly.fromJson(Map<String, dynamic>.from(e)))
          .toList();
    }
  }

  Future<void> _fetchForecast() async {
    final res = await ApiService.get(ApiConfig.analyticsForecast);
    if (res.isSuccess && res.data is List) {
      _forecast = (res.data as List<dynamic>)
          .map((e) => ForecastPoint.fromJson(Map<String, dynamic>.from(e)))
          .toList();
    }
  }

  Future<Map<String, dynamic>> uploadPdfStatement(
    Uint8List fileBytes,
    String fileName, {
    String? password,
  }) async {
    _isLoading = true;
    notifyListeners();

    final res = await ApiService.uploadPdfStatement(fileBytes, fileName, password: password);
    _isLoading = false;
    notifyListeners();

    if (res.isSuccess && res.data is Map) {
      await refreshAllData();
      return {
        'success': true,
        'requires_password': res.data['requires_password'] == true,
        'message': res.data['message'],
        'tier_name': res.data['tier_name'],
      };
    } else {
      return {
        'success': false,
        'requires_password': (res.data is Map && res.data['requires_password'] == true),
        'message': res.errorMessage ?? 'PDF statement parsing failed.',
      };
    }
  }

  Future<bool> addTransaction({
    required String description,
    required double amount,
    required String category,
    required String date,
  }) async {
    final res = await ApiService.post(ApiConfig.transactions, {
      'description': description,
      'amount': amount,
      'category': category,
      'date': date,
    });
    if (res.isSuccess) {
      await refreshAllData();
      return true;
    }
    return false;
  }

  Future<bool> createGoal({
    required String name,
    required double targetAmount,
    required double currentAmount,
    required String targetDate,
    required String category,
  }) async {
    final res = await ApiService.post(ApiConfig.goals, {
      'name': name,
      'target_amount': targetAmount,
      'current_amount': currentAmount,
      'target_date': targetDate,
      'category': category,
    });
    if (res.isSuccess) {
      await _fetchGoals();
      notifyListeners();
      return true;
    }
    return false;
  }

  Future<bool> contributeToGoal(String goalId, double amount) async {
    final res = await ApiService.post('${ApiConfig.goals}/$goalId/contribute', {
      'amount': amount,
    });
    if (res.isSuccess) {
      _goalRecommendations.remove(goalId);
      await _fetchGoals();
      await _fetchDashboardSummary();
      await fetchGoalRecommendations(goalId, force: true);
      notifyListeners();
      return true;
    }
    return false;
  }

  Future<bool> deleteGoal(String goalId) async {
    final res = await ApiService.delete('${ApiConfig.goals}/$goalId');
    if (res.isSuccess) {
      _goalRecommendations.remove(goalId);
      await _fetchGoals();
      await _fetchDashboardSummary();
      notifyListeners();
      return true;
    }
    return false;
  }

  Future<GoalRecommendationData?> fetchGoalRecommendations(String goalId, {bool force = false}) async {
    if (!force && _goalRecommendations.containsKey(goalId)) {
      return _goalRecommendations[goalId];
    }

    _loadingGoalRecs[goalId] = true;
    notifyListeners();

    try {
      final res = await ApiService.get(ApiConfig.goalRecommendations(goalId));
      if (res.isSuccess && res.data is Map) {
        final recData = GoalRecommendationData.fromJson(Map<String, dynamic>.from(res.data));
        _goalRecommendations[goalId] = recData;
        return recData;
      }
    } catch (e) {
      debugPrint('Error fetching recommendations for goal $goalId: $e');
    } finally {
      _loadingGoalRecs[goalId] = false;
      notifyListeners();
    }
    return null;
  }

  Future<void> sendChatMessage(String message) async {
    _sessionId ??= 'session_${DateTime.now().millisecondsSinceEpoch}';
    final userMsg = ChatMessage(
      id: 'u_${DateTime.now().millisecondsSinceEpoch}',
      sender: 'user',
      text: message,
      timestamp: DateTime.now().toIso8601String(),
    );
    _chatHistory.add(userMsg);
    _isChatLoading = true;
    notifyListeners();

    final res = await ApiService.post(ApiConfig.chat, {
      'message': message,
      'session_id': _sessionId,
    });

    _isChatLoading = false;
    if (res.isSuccess && res.data is Map) {
      final agentMsg = ChatMessage(
        id: 'a_${DateTime.now().millisecondsSinceEpoch}',
        sender: 'agent',
        text: res.data['response'] ?? 'I could not process that request.',
        timestamp: DateTime.now().toIso8601String(),
        toolCalls: (res.data['tool_calls_made'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
        sources: (res.data['sources'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      );
      _chatHistory.add(agentMsg);
    } else {
      _chatHistory.add(ChatMessage(
        id: 'err_${DateTime.now().millisecondsSinceEpoch}',
        sender: 'agent',
        text: 'Sorry, I encountered an issue connecting to the financial advisor. Please try again.',
        timestamp: DateTime.now().toIso8601String(),
      ));
    }
    notifyListeners();
  }

  Future<Map<String, dynamic>> whatIfSimulate(String category, double reductionPct) async {
    final res = await ApiService.get(ApiConfig.analyticsWhatIf, {
      'category': category,
      'reduction_pct': reductionPct.toInt().toString(),
    });
    if (res.isSuccess && res.data is Map) {
      return Map<String, dynamic>.from(res.data);
    }
    return {};
  }

  Future<void> fetchKycStatus() async {
    final res = await ApiService.get(ApiConfig.kycStatus);
    if (res.isSuccess && res.data is Map) {
      _kycData = KycData.fromJson(Map<String, dynamic>.from(res.data));
    }
  }

  Future<Map<String, dynamic>> verifyPan(String panNumber) async {
    final res = await ApiService.post(ApiConfig.kycVerifyPan, {
      'pan_number': panNumber,
    });
    if (res.isSuccess) {
      await fetchKycStatus();
      notifyListeners();
      return {'success': true, 'message': 'PAN verified successfully'};
    }
    return {'success': false, 'error': res.errorMessage ?? 'PAN verification failed'};
  }

  Future<Map<String, dynamic>> initiateDigiLocker(String aadhaarNumber) async {
    final res = await ApiService.post(ApiConfig.kycDigilockerInitiate, {
      'aadhaar_number': aadhaarNumber,
    });
    if (res.isSuccess && res.data is Map) {
      return {
        'success': true,
        'session_id': res.data['session_id'],
        'masked_aadhaar': res.data['masked_aadhaar'],
      };
    }
    return {'success': false, 'error': res.errorMessage ?? 'DigiLocker initiation failed'};
  }

  Future<Map<String, dynamic>> verifyDigiLockerOtp(String sessionId, String otp) async {
    final res = await ApiService.post(ApiConfig.kycDigilockerVerifyOtp, {
      'session_id': sessionId,
      'otp': otp,
    });
    if (res.isSuccess) {
      await fetchKycStatus();
      await _fetchUserProfile();
      notifyListeners();
      return {'success': true, 'message': 'Aadhaar verified successfully via DigiLocker'};
    }
    return {'success': false, 'error': res.errorMessage ?? 'OTP verification failed'};
  }
}
