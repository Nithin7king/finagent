class LedgerTransaction {
  final String id;
  final String date;
  final String description;
  final double amount;
  final String category;
  final String status; // 'AI-assigned' or 'user-corrected'
  final bool isAnomaly;
  final double? anomalyScore;
  final String? anomalyExplanation;
  final double balanceAfter;

  LedgerTransaction({
    required this.id,
    required this.date,
    required this.description,
    required this.amount,
    required this.category,
    this.status = 'AI-assigned',
    this.isAnomaly = false,
    this.anomalyScore,
    this.anomalyExplanation,
    this.balanceAfter = 0.0,
  });

  factory LedgerTransaction.fromJson(Map<String, dynamic> json, {double runningBalance = 0.0}) {
    final rawAmount = (json['amount'] as num).toDouble();
    final isAnomaly = json['anomaly_label'] == true;
    final cat = json['category'] ?? json['ml_category'] ?? 'Other';
    final isUserCorrected = json['source'] == 'manual' || (json['category'] != null && json['category'] != json['ml_category']);
    final dateStr = json['date']?.toString() ?? '';
    final formattedDate = dateStr.length >= 10 ? dateStr.substring(0, 10) : dateStr;

    return LedgerTransaction(
      id: json['id'].toString(),
      date: formattedDate,
      description: json['description'] ?? '',
      amount: rawAmount,
      category: cat,
      status: isUserCorrected ? 'user-corrected' : 'AI-assigned',
      isAnomaly: isAnomaly,
      anomalyScore: (json['anomaly_score'] as num?)?.toDouble(),
      anomalyExplanation: json['anomaly_explanation'],
      balanceAfter: runningBalance,
    );
  }
}
