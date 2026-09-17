class ForecastPoint {
  final String label;
  final int days;
  final double projected;
  final double confidenceMin;
  final double confidenceMax;

  ForecastPoint({
    required this.label,
    required this.days,
    required this.projected,
    required this.confidenceMin,
    required this.confidenceMax,
  });

  factory ForecastPoint.fromJson(Map<String, dynamic> json) {
    final days = (json['period_days'] as num?)?.toInt() ?? 30;
    final projected = (json['predicted_total_expense'] as num?)?.toDouble() ?? 0.0;

    return ForecastPoint(
      label: '$days Days Forecast',
      days: days,
      projected: projected,
      confidenceMin: projected * 0.85,
      confidenceMax: projected * 1.15,
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
}
