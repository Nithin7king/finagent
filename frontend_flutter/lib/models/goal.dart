class SavingsGoal {
  final String id;
  final String name;
  final String description;
  final double targetAmount;
  final double currentAmount;
  final String targetDate;
  final double monthlyContribution;
  final double progressPct;
  final double? monthsToGoal;
  final bool isCompleted;

  SavingsGoal({
    required this.id,
    required this.name,
    this.description = 'Savings',
    required this.targetAmount,
    required this.currentAmount,
    this.targetDate = '',
    this.monthlyContribution = 0.0,
    this.progressPct = 0.0,
    this.monthsToGoal,
    this.isCompleted = false,
  });

  factory SavingsGoal.fromJson(Map<String, dynamic> json) {
    final dateStr = json['target_date']?.toString() ?? '';
    final formattedDate = dateStr.length >= 10 ? dateStr.substring(0, 10) : dateStr;

    return SavingsGoal(
      id: json['id'].toString(),
      name: json['name'] ?? '',
      description: json['description'] ?? 'Savings',
      targetAmount: (json['target_amount'] as num).toDouble(),
      currentAmount: (json['current_amount'] as num?)?.toDouble() ?? 0.0,
      targetDate: formattedDate,
      monthlyContribution: (json['monthly_contribution'] as num?)?.toDouble() ?? 0.0,
      progressPct: (json['progress_pct'] as num?)?.toDouble() ??
          (((json['current_amount'] as num? ?? 0) / ((json['target_amount'] as num? ?? 1)) * 100)).toDouble(),
      monthsToGoal: (json['months_to_goal'] as num?)?.toDouble(),
      isCompleted: json['is_completed'] == true,
    );
  }
}
