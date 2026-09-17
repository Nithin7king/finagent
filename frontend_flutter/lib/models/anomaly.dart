class AnomalyItem {
  final String id;
  final String transactionId;
  final String date;
  final String merchant;
  final double amount;
  final String severity; // Low, Medium, High
  final String? explanation;

  AnomalyItem({
    required this.id,
    required this.transactionId,
    required this.date,
    required this.merchant,
    required this.amount,
    required this.severity,
    this.explanation,
  });

  factory AnomalyItem.fromJson(Map<String, dynamic> json) {
    final sev = json['severity']?.toString() ?? 'low';
    final capitalizedSev = sev.isNotEmpty ? '${sev[0].toUpperCase()}${sev.substring(1)}' : 'Low';

    return AnomalyItem(
      id: json['id'].toString(),
      transactionId: json['id'].toString(),
      date: json['date'] ?? '',
      merchant: json['description'] ?? 'Flagged transaction',
      amount: (json['amount'] as num).toDouble(),
      severity: capitalizedSev,
      explanation: json['explanation'],
    );
  }
}
