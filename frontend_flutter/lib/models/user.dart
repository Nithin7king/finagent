class UserProfile {
  final int? id;
  final String name;
  final String email;
  final double monthlyIncome;
  final String currency;

  UserProfile({
    this.id,
    required this.name,
    required this.email,
    this.monthlyIncome = 0.0,
    this.currency = 'INR',
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] != null ? (json['id'] as num).toInt() : null,
      name: json['name'] ?? '',
      email: json['email'] ?? '',
      monthlyIncome: (json['monthly_income'] as num?)?.toDouble() ?? 0.0,
      currency: json['currency'] ?? 'INR',
    );
  }
}

class AuthTokenResponse {
  final String accessToken;
  final int userId;
  final String name;
  final String email;

  AuthTokenResponse({
    required this.accessToken,
    required this.userId,
    required this.name,
    required this.email,
  });

  factory AuthTokenResponse.fromJson(Map<String, dynamic> json) {
    return AuthTokenResponse(
      accessToken: json['access_token'] ?? '',
      userId: (json['user_id'] as num).toInt(),
      name: json['name'] ?? '',
      email: json['email'] ?? '',
    );
  }
}
