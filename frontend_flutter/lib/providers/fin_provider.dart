import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user.dart';
import '../models/transaction.dart';
import '../models/goal.dart';
import '../models/subscription.dart';
import '../models/anomaly.dart';
import '../models/forecast.dart';
import '../models/chat_message.dart';
import '../services/api_service.dart';

class FinProvider extends ChangeNotifier {
  UserProfile? _user;
  List<LedgerTransaction> _transactions = [];
  List<SavingsGoal> _goals = [];
  List<SubscriptionItem> _subscriptions = [];
  List<AnomalyItem> _activeAnomalies = [];
  DashboardSummary _summary = DashboardSummary();
  List<ForecastPoint> _forecast = [];
  List<ChatTurn> _chatHistory = [];

  bool _isLoading = true;
  bool _isChatLoading = false;
  bool _isBackendConnected = true;
  ThemeMode _themeMode = ThemeMode.dark;
  String? _sessionId;
  int _currentNavIndex = 0; // 0: Dashboard, 1: Ledger, 2: Analytics, 3: Goals, 4: Chat

  // Getters
  UserProfile? get user => _user;
  List<LedgerTransaction> get transactions => _transactions;
  List<SavingsGoal> get goals => _goals;
  List<SubscriptionItem> get subscriptions => _subscriptions;
  List<AnomalyItem> get activeAnomalies => _activeAnomalies;
  DashboardSummary get summary => _summary;
  List<ForecastPoint> get forecast => _forecast;
  List<ChatTurn> get chatHistory => _chatHistory;
  bool get isLoading => _isLoading;
  bool get isChatLoading => _isChatLoading;
  bool get isBackendConnected => _isBackendConnected;
  ThemeMode get themeMode => _themeMode;
  bool get isDarkMode => _themeMode == ThemeMode.dark;
  int get currentNavIndex => _currentNavIndex;

  void setNavIndex(int index) {
    _currentNavIndex = index;
    notifyListeners();
  }

  void toggleTheme() async {
    _themeMode = _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('fin_theme', _themeMode == ThemeMode.dark ? 'dark' : 'light');
  }

  Future<void> init() async {
    _isLoading = true;
    notifyListeners();

    try {
      final prefs = await SharedPreferences.getInstance();
      final savedTheme = prefs.getString('fin_theme');
      if (savedTheme != null) {
        _themeMode = savedTheme == 'light' ? ThemeMode.light : ThemeMode.dark;
      }

      _isBackendConnected = await ApiService.checkHealth();

      final token = await ApiService.getToken();
      if (token != null && token.isNotEmpty) {
        _user = await ApiService.getMe();
        if (_user != null) {
          await refreshAllData();
        } else {
          await ApiService.clearToken();
        }
      }
    } catch (e) {
      debugPrint('[FinProvider] Init error: $e');
      await ApiService.clearToken();
      _user = null;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    notifyListeners();
    try {
      final auth = await ApiService.login(email, password);
      if (auth != null) {
        _user = UserProfile(
          id: auth.userId,
          name: auth.name,
          email: auth.email,
        );
        await refreshAllData();
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('[FinProvider] Login error: $e');
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<bool> register({
    required String name,
    required String email,
    required String password,
    double monthlyIncome = 0.0,
    String currency = 'INR',
  }) async {
    _isLoading = true;
    notifyListeners();
    try {
      final auth = await ApiService.register(
        name: name,
        email: email,
        password: password,
        monthlyIncome: monthlyIncome,
        currency: currency,
      );
      if (auth != null) {
        _user = UserProfile(
          id: auth.userId,
          name: auth.name,
          email: auth.email,
          monthlyIncome: monthlyIncome,
          currency: currency,
        );
        await refreshAllData();
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('[FinProvider] Registration error: $e');
      return false;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await ApiService.clearToken();
    _user = null;
    _transactions = [];
    _goals = [];
    _subscriptions = [];
    _activeAnomalies = [];
    _chatHistory = [];
    _currentNavIndex = 0;
    notifyListeners();
  }

  Future<void> refreshAllData() async {
    try {
      final results = await Future.wait([
        ApiService.getTransactions(perPage: 200),
        ApiService.getSpendingSummary(days: 30),
        ApiService.getAnomalies(days: 30),
        ApiService.getSubscriptions(),
        ApiService.getGoals(),
      ]);

      final txData = results[0] as Map<String, dynamic>;
      final summaryData = results[1] as Map<String, dynamic>;
      final anomalyData = results[2] as Map<String, dynamic>;
      final subData = results[3] as Map<String, dynamic>;
      final goalData = results[4] as List<dynamic>;

      // Map Transactions & compute running balance
      final rawTxList = (txData['transactions'] as List<dynamic>?) ?? [];
      double runningBalance = 0.0;
      final reversed = rawTxList.reversed.toList();
      final List<LedgerTransaction> mapped = [];

      for (final r in reversed) {
        final amt = (r['amount'] as num).toDouble();
        runningBalance += amt;
        mapped.add(LedgerTransaction.fromJson(r as Map<String, dynamic>, runningBalance: runningBalance));
      }
      _transactions = mapped.reversed.toList();

      // Summary
      _summary = DashboardSummary(
        totalBalance: runningBalance,
        thisMonthSpend: (summaryData['total_expenses'] as num?)?.toDouble() ?? 0.0,
        savingsRate: (summaryData['savings_rate'] as num?)?.toDouble() ?? 0.0,
        anomaliesCount: (anomalyData['count'] as num?)?.toInt() ?? 0,
      );

      // Anomalies
      final anomalyList = (anomalyData['anomalies'] as List<dynamic>?) ?? [];
      _activeAnomalies = anomalyList.map((a) => AnomalyItem.fromJson(a as Map<String, dynamic>)).toList();

      // Subscriptions
      final subList = (subData['subscriptions'] as List<dynamic>?) ?? [];
      final creepAnalysis = subData['creep_analysis'] as Map<String, dynamic>?;
      final incomePct = (creepAnalysis?['income_pct'] as num?)?.toDouble() ?? 0.0;
      final creepScore = (incomePct * 5).round().clamp(0, 100);

      _subscriptions = subList.asMap().entries.map((entry) {
        return SubscriptionItem.fromJson(entry.value as Map<String, dynamic>, entry.key, creepScore);
      }).toList();

      // Goals
      _goals = goalData.map((g) => SavingsGoal.fromJson(g as Map<String, dynamic>)).toList();

      // Forecasts (30, 60, 90 days)
      final forecastResponses = await Future.wait([
        ApiService.getForecast(30),
        ApiService.getForecast(60),
        ApiService.getForecast(90),
      ]);
      _forecast = forecastResponses.map((f) => ForecastPoint.fromJson(f)).toList();

      notifyListeners();
    } catch (e) {
      debugPrint('[FinProvider] refreshAllData error: $e');
    }
  }

  Future<void> addTransaction({
    required String description,
    required double amount,
    required String category,
    required String date,
  }) async {
    final success = await ApiService.addTransaction(
      description: description,
      amount: amount,
      category: category,
      date: date,
    );
    if (success) {
      await refreshAllData();
    }
  }

  Future<void> correctCategory(String txId, String newCategory) async {
    final success = await ApiService.updateCategory(txId, newCategory);
    if (success) {
      await refreshAllData();
    }
  }

  Future<void> commitCsvTransactions(List<LedgerTransaction> txs) async {
    for (final tx in txs) {
      await ApiService.addTransaction(
        description: tx.description,
        amount: tx.amount,
        category: tx.category,
        date: tx.date,
      );
    }
    await refreshAllData();
  }

  Future<void> createGoal({
    required String name,
    required String description,
    required double targetAmount,
    double currentAmount = 0.0,
    String? targetDate,
  }) async {
    final success = await ApiService.createGoal(
      name: name,
      description: description,
      targetAmount: targetAmount,
      currentAmount: currentAmount,
      targetDate: targetDate,
    );
    if (success) {
      await refreshAllData();
    }
  }

  Future<void> contributeToGoal(String goalId, double amount) async {
    final success = await ApiService.contributeToGoal(goalId, amount);
    if (success) {
      await refreshAllData();
    }
  }

  Future<void> sendChatMessage(String text) async {
    if (text.trim().isEmpty || _isChatLoading) return;

    final userTurn = ChatTurn(
      id: 'user-${DateTime.now().millisecondsSinceEpoch}',
      sender: 'user',
      text: text,
      timestamp: DateTime.now(),
    );
    _chatHistory.add(userTurn);
    _isChatLoading = true;
    notifyListeners();

    try {
      final res = await ApiService.sendChatMessage(text, _sessionId);
      _sessionId = res['session_id'];
      final rawToolCalls = (res['tool_calls_made'] as List<dynamic>?)?.map((t) => t.toString()).toList() ?? [];

      final agentTurn = ChatTurn(
        id: 'agent-${DateTime.now().millisecondsSinceEpoch}',
        sender: 'agent',
        text: res['response'] ?? '',
        timestamp: DateTime.now(),
        toolCalls: rawToolCalls,
      );
      _chatHistory.add(agentTurn);
    } catch (e) {
      _chatHistory.add(
        ChatTurn(
          id: 'agent-err-${DateTime.now().millisecondsSinceEpoch}',
          sender: 'agent',
          text: 'Apologies, I encountered an error communicating with the agent: $e',
          timestamp: DateTime.now(),
        ),
      );
    } finally {
      _isChatLoading = false;
      notifyListeners();
    }
  }

  Future<String> getWeeklyDigest() async {
    return await ApiService.getWeeklyDigest();
  }
}
