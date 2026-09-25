class ForecastPoint {
  final String date;
  final double projected;
  final double confidenceMin;
  final double confidenceMax;

  ForecastPoint({
    required this.date,
    required this.projected,
    required this.confidenceMin,
    required this.confidenceMax,
  });

  factory ForecastPoint.fromJson(Map<String, dynamic> json) {
    return ForecastPoint(
      date: json['date'] ?? json['name'] ?? '',
      projected: (json['projected'] as num?)?.toDouble() ?? 
                 (json['Baseline'] as num?)?.toDouble() ?? 0.0,
      confidenceMin: (json['confidenceMin'] as num?)?.toDouble() ?? 0.0,
      confidenceMax: (json['confidenceMax'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class DashboardSummary {
  final double totalBalance;
  final double thisMonthSpend;
  final double savingsRate;
  final int anomaliesCount;

  DashboardSummary({
    this.totalBalance = 0.0,
    this.thisMonthSpend = 0.0,
    this.savingsRate = 0.0,
    this.anomaliesCount = 0,
  });

  factory DashboardSummary.fromJson(Map<String, dynamic> json) {
    return DashboardSummary(
      totalBalance: (json['totalBalance'] as num?)?.toDouble() ?? 
                    (json['net_worth'] as num?)?.toDouble() ?? 
                    (json['total_balance'] as num?)?.toDouble() ?? 0.0,
      thisMonthSpend: (json['thisMonthSpend'] as num?)?.toDouble() ?? 
                      (json['this_month_spending'] as num?)?.toDouble() ?? 
                      (json['total_expenses'] as num?)?.toDouble() ?? 0.0,
      savingsRate: (json['savingsRate'] as num?)?.toDouble() ?? 
                   (json['savings_rate'] as num?)?.toDouble() ?? 0.0,
      anomaliesCount: (json['anomaliesCount'] as num?)?.toInt() ?? 
                      (json['active_anomalies_count'] as num?)?.toInt() ?? 0,
    );
  }
}
