class Subscription {
  final String id;
  final String merchant;
  final double amount;
  final String cadence;
  final String nextChargeDate;
  final double creepScore; // 0 to 100
  final double monthlyCost;

  Subscription({
    required this.id,
    required this.merchant,
    required this.amount,
    required this.cadence,
    required this.nextChargeDate,
    required this.creepScore,
    required this.monthlyCost,
  });

  factory Subscription.fromJson(Map<String, dynamic> json) {
    final double amt = (json['amount'] as num?)?.toDouble() ?? 0.0;
    final int interval = (json['interval_days'] as num?)?.toInt() ?? 30;
    final double mCost = (json['monthly_cost'] as num?)?.toDouble() ?? (amt * (30 / interval));

    return Subscription(
      id: json['id']?.toString() ?? json['merchant'] ?? '',
      merchant: json['merchant'] ?? 'Subscription',
      amount: amt,
      cadence: json['cadence'] ?? (interval <= 35 ? 'Monthly' : 'Annual'),
      nextChargeDate: json['next_expected']?.toString().split('T').first ?? 
                      json['nextChargeDate']?.toString().split('T').first ?? 'Upcoming',
      creepScore: (json['creepScore'] as num?)?.toDouble() ?? 
                  ((json['confidence'] == 'high') ? 85.0 : 50.0),
      monthlyCost: mCost,
    );
  }
}

class CreepAnalysis {
  final double totalMonthly;
  final double incomePct;
  final String riskLevel; // 'low' | 'medium' | 'high'
  final String insight;

  CreepAnalysis({
    required this.totalMonthly,
    required this.incomePct,
    required this.riskLevel,
    required this.insight,
  });

  factory CreepAnalysis.fromJson(Map<String, dynamic> json) {
    return CreepAnalysis(
      totalMonthly: (json['total_monthly_subscriptions'] as num?)?.toDouble() ?? 0.0,
      incomePct: (json['income_pct'] as num?)?.toDouble() ?? 0.0,
      riskLevel: json['risk_level'] ?? 'low',
      insight: json['insight'] ?? 'Your recurring subscriptions are healthy.',
    );
  }
}
