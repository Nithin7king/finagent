class Transaction {
  final String id;
  final String date;
  final String description;
  final double amount;
  final String category;
  final String status; // 'AI-assigned' | 'user-corrected'
  final bool isAnomaly;
  final double balanceAfter;

  Transaction({
    required this.id,
    required this.date,
    required this.description,
    required this.amount,
    required this.category,
    required this.status,
    required this.isAnomaly,
    required this.balanceAfter,
  });

  factory Transaction.fromJson(Map<String, dynamic> json, [double runningBalance = 0.0]) {
    final double rawAmount = (json['amount'] as num?)?.toDouble() ?? 0.0;
    final String cat = json['category'] ?? 'Others';
    final String mlCat = json['ml_category'] ?? cat;
    final String src = json['source'] ?? 'bank';
    final bool isUserCorrected = src == 'manual' || cat != mlCat;

    return Transaction(
      id: json['id']?.toString() ?? '',
      date: json['date']?.toString().split('T').first ?? '',
      description: json['description'] ?? 'Transaction',
      amount: rawAmount,
      category: _normalizeCategory(cat),
      status: isUserCorrected ? 'user-corrected' : 'AI-assigned',
      isAnomaly: json['is_anomaly'] == true || json['anomaly_label'] == true,
      balanceAfter: (json['balanceAfter'] as num?)?.toDouble() ?? runningBalance,
    );
  }

  static String _normalizeCategory(String? cat) {
    if (cat == null) return 'Others';
    switch (cat.toLowerCase()) {
      case 'salary':
      case 'income':
        return 'Salary';
      case 'investment':
      case 'investments':
        return 'Investment';
      case 'food':
      case 'food & dining':
      case 'dining':
        return 'Food';
      case 'housing':
      case 'rent':
        return 'Housing';
      case 'utilities':
      case 'utilities & bills':
      case 'bills':
        return 'Utilities';
      case 'transport':
      case 'travel':
        return 'Transport';
      case 'shopping':
        return 'Shopping';
      case 'entertainment':
        return 'Entertainment';
      default:
        return 'Others';
    }
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'date': date,
      'description': description,
      'amount': amount,
      'category': category,
      'status': status,
      'isAnomaly': isAnomaly,
      'balanceAfter': balanceAfter,
    };
  }
}

class Anomaly {
  final String id;
  final String transactionId;
  final String date;
  final String merchant;
  final double amount;
  final String severity; // 'Low' | 'Medium' | 'High'
  final String explanation;

  Anomaly({
    required this.id,
    required this.transactionId,
    required this.date,
    required this.merchant,
    required this.amount,
    required this.severity,
    required this.explanation,
  });

  factory Anomaly.fromJson(Map<String, dynamic> json) {
    return Anomaly(
      id: json['id']?.toString() ?? '',
      transactionId: json['transaction_id']?.toString() ?? json['transactionId']?.toString() ?? '',
      date: json['date']?.toString().split('T').first ?? '',
      merchant: json['description'] ?? json['merchant'] ?? 'Unknown Merchant',
      amount: (json['amount'] as num?)?.toDouble() ?? 0.0,
      severity: _normalizeSeverity(json['severity']),
      explanation: json['explanation'] ?? json['message'] ?? 'Spend flagged as unusual.',
    );
  }

  static String _normalizeSeverity(dynamic sev) {
    final String s = sev?.toString().toLowerCase() ?? 'medium';
    if (s == 'high') return 'High';
    if (s == 'low') return 'Low';
    return 'Medium';
  }
}
