class KycData {
  final String kycStatus; // 'pending' | 'pan_verified' | 'verified'
  final String? panNumber;
  final bool panVerified;
  final String? aadhaarMasked;
  final bool digilockerVerified;
  final double monthlyIncome;
  final String? kycCompletedAt;

  KycData({
    required this.kycStatus,
    this.panNumber,
    required this.panVerified,
    this.aadhaarMasked,
    required this.digilockerVerified,
    required this.monthlyIncome,
    this.kycCompletedAt,
  });

  factory KycData.fromJson(Map<String, dynamic> json) {
    return KycData(
      kycStatus: json['kyc_status'] ?? 'pending',
      panNumber: json['pan_number'],
      panVerified: json['pan_verified'] ?? false,
      aadhaarMasked: json['aadhaar_masked'],
      digilockerVerified: json['digilocker_verified'] ?? false,
      monthlyIncome: (json['monthly_income'] as num?)?.toDouble() ?? 50000.0,
      kycCompletedAt: json['kyc_completed_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'kyc_status': kycStatus,
      'pan_number': panNumber,
      'pan_verified': panVerified,
      'aadhaar_masked': aadhaarMasked,
      'digilocker_verified': digilockerVerified,
      'monthly_income': monthlyIncome,
      'kyc_completed_at': kycCompletedAt,
    };
  }
}

class UserProfile {
  final int? id;
  final String name;
  final String email;
  final double monthlyIncome;
  final String currency;
  final String kycStatus;
  final bool digilockerVerified;
  final bool panVerified;

  UserProfile({
    this.id,
    required this.name,
    required this.email,
    this.monthlyIncome = 50000.0,
    this.currency = 'INR',
    this.kycStatus = 'pending',
    this.digilockerVerified = false,
    this.panVerified = false,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] as int?,
      name: json['name'] ?? 'User',
      email: json['email'] ?? '',
      monthlyIncome: (json['monthly_income'] as num?)?.toDouble() ?? 50000.0,
      currency: json['currency'] ?? 'INR',
      kycStatus: json['kyc_status'] ?? 'pending',
      digilockerVerified: json['digilocker_verified'] ?? false,
      panVerified: json['pan_verified'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'email': email,
      'monthly_income': monthlyIncome,
      'currency': currency,
      'kyc_status': kycStatus,
      'digilocker_verified': digilockerVerified,
      'pan_verified': panVerified,
    };
  }
}
