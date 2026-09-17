class SubscriptionItem {
  final String id;
  final String merchant;
  final double amount;
  final String cadence;
  final String nextChargeDate;
  final int creepScore;

  SubscriptionItem({
    required this.id,
    required this.merchant,
    required this.amount,
    required this.cadence,
    required this.nextChargeDate,
    this.creepScore = 0,
  });

  factory SubscriptionItem.fromJson(Map<String, dynamic> json, int index, int creep) {
    final merchant = json['merchant'] ?? 'Subscription';
    final intervalDays = json['interval_days'] ?? 30;
    return SubscriptionItem(
      id: '$merchant-$index',
      merchant: merchant,
      amount: (json['amount'] as num?)?.toDouble() ?? 0.0,
      cadence: '$intervalDays days',
      nextChargeDate: json['next_expected'] ?? '—',
      creepScore: creep,
    );
  }
}
