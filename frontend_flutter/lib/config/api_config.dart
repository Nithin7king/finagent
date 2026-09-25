import 'package:flutter/foundation.dart';
import 'dart:io' show Platform;

class ApiConfig {
  // Direct FastAPI Backend on port 8000 matches endpoints (/auth/login, /transactions, etc.)
  static const bool useGateway = false;
  static const int gatewayPort = 5000;
  static const int backendPort = 8000;

  // Physical phone via USB (with 'adb reverse tcp:8000 tcp:8000')
  static String customBaseUrl = 'http://127.0.0.1:8000';

  static String get baseUrl {
    // 1. Check if passed via flutter run --dart-define=API_URL=http://...
    const String envUrl = String.fromEnvironment('API_URL');
    if (envUrl.isNotEmpty) {
      return envUrl.replaceAll(RegExp(r'/+$'), '');
    }

    final int port = useGateway ? gatewayPort : backendPort;
    
    if (kIsWeb) {
      return 'http://localhost:$port';
    }

    // 2. Check if configured for physical device / USB reverse
    if (customBaseUrl.isNotEmpty) {
      return customBaseUrl.replaceAll(RegExp(r'/+$'), '');
    }
    
    try {
      if (Platform.isAndroid) {
        // Android emulator loopback to host machine
        return 'http://10.0.2.2:$port';
      }
    } catch (_) {
      // Platform check may fail on non-supported targets
    }
    
    return 'http://localhost:$port';
  }


  // Endpoints
  static const String authRegister = '/auth/register';
  static const String authLogin = '/auth/login';
  static const String authMe = '/auth/me';

  static const String transactions = '/transactions';
  static const String transactionsUpload = '/transactions/upload';
  static const String transactionsSummary = '/transactions/summary';

  static const String analyticsSummary = '/analytics/summary';
  static const String analyticsForecast = '/analytics/forecast';
  static const String analyticsWhatIf = '/analytics/what-if';
  static const String analyticsSubscriptions = '/analytics/subscriptions';
  static const String analyticsAnomalies = '/analytics/anomalies';

  static const String goals = '/goals';
  static String goalRecommendations(String id) => '/goals/$id/recommendations';
  static const String alerts = '/alerts';
  static const String chat = '/chat';
  static const String chatHistory = '/chat/history';

  static const String kycStatus = '/kyc/status';
  static const String kycVerifyPan = '/kyc/verify-pan';
  static const String kycDigilockerInitiate = '/kyc/digilocker/initiate';
  static const String kycDigilockerVerifyOtp = '/kyc/digilocker/verify-otp';
}
