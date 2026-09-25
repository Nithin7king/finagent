class Goal {
  final String id;
  final String name;
  final double targetAmount;
  final double currentAmount;
  final String targetDate;
  final String category;
  final double monthlyContribution;
  final bool isCompleted;

  Goal({
    required this.id,
    required this.name,
    required this.targetAmount,
    required this.currentAmount,
    required this.targetDate,
    required this.category,
    this.monthlyContribution = 0.0,
    this.isCompleted = false,
  });

  double get progressPct {
    if (targetAmount <= 0) return 0.0;
    final pct = (currentAmount / targetAmount) * 100;
    return pct.clamp(0.0, 100.0);
  }

  double get remainingAmount => (targetAmount - currentAmount).clamp(0.0, targetAmount);

  factory Goal.fromJson(Map<String, dynamic> json) {
    return Goal(
      id: json['id']?.toString() ?? '',
      name: json['name'] ?? 'Savings Goal',
      targetAmount: (json['target_amount'] as num?)?.toDouble() ?? 
                    (json['targetAmount'] as num?)?.toDouble() ?? 0.0,
      currentAmount: (json['current_amount'] as num?)?.toDouble() ?? 
                     (json['currentAmount'] as num?)?.toDouble() ?? 0.0,
      targetDate: json['target_date']?.toString().split('T').first ?? 
                  json['targetDate']?.toString().split('T').first ?? '',
      category: json['category'] ?? 'Emergency Fund',
      monthlyContribution: (json['monthly_contribution'] as num?)?.toDouble() ?? 0.0,
      isCompleted: json['is_completed'] == true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'target_amount': targetAmount,
      'current_amount': currentAmount,
      'target_date': targetDate,
      'category': category,
    };
  }
}

class GoalRecommendationItem {
  final String id;
  final String type;
  final String title;
  final String message;
  final String impact;
  final double monthlySavings;
  final String priority;
  final String badge;

  GoalRecommendationItem({
    required this.id,
    required this.type,
    required this.title,
    required this.message,
    required this.impact,
    required this.monthlySavings,
    required this.priority,
    required this.badge,
  });

  factory GoalRecommendationItem.fromJson(Map<String, dynamic> json) {
    return GoalRecommendationItem(
      id: json['id']?.toString() ?? '',
      type: json['type']?.toString() ?? 'spending_cut',
      title: json['title']?.toString() ?? 'Savings Tip',
      message: json['message']?.toString() ?? '',
      impact: json['impact']?.toString() ?? '',
      monthlySavings: (json['monthly_savings'] as num?)?.toDouble() ?? 0.0,
      priority: json['priority']?.toString() ?? 'medium',
      badge: json['badge']?.toString() ?? '⚡ Tip',
    );
  }
}

class GoalRecommendationData {
  final String goalId;
  final String goalName;
  final double remainingAmount;
  final double currentTimelineMonths;
  final double optimizedTimelineMonths;
  final double monthsSaved;
  final double accelerationPct;
  final List<GoalRecommendationItem> recommendations;

  GoalRecommendationData({
    required this.goalId,
    required this.goalName,
    required this.remainingAmount,
    required this.currentTimelineMonths,
    required this.optimizedTimelineMonths,
    required this.monthsSaved,
    required this.accelerationPct,
    required this.recommendations,
  });

  factory GoalRecommendationData.fromJson(Map<String, dynamic> json) {
    final rawRecs = (json['recommendations'] as List<dynamic>?) ?? [];
    return GoalRecommendationData(
      goalId: json['goal_id']?.toString() ?? '',
      goalName: json['goal_name']?.toString() ?? '',
      remainingAmount: (json['remaining_amount'] as num?)?.toDouble() ?? 0.0,
      currentTimelineMonths: (json['current_timeline_months'] as num?)?.toDouble() ?? 0.0,
      optimizedTimelineMonths: (json['optimized_timeline_months'] as num?)?.toDouble() ?? 0.0,
      monthsSaved: (json['months_saved'] as num?)?.toDouble() ?? 0.0,
      accelerationPct: (json['acceleration_pct'] as num?)?.toDouble() ?? 0.0,
      recommendations: rawRecs.map((r) => GoalRecommendationItem.fromJson(Map<String, dynamic>.from(r))).toList(),
    );
  }
}
