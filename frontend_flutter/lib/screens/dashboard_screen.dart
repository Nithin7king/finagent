import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
import '../config/app_theme.dart';
import '../providers/fin_provider.dart';
import '../widgets/stat_card.dart';
import '../widgets/stamp_badge.dart';
import '../widgets/goal_card.dart';
import '../widgets/passbook_app_bar.dart';

class DashboardScreen extends StatelessWidget {
  final Function(int tabIndex)? onNavigateTab;

  const DashboardScreen({Key? key, this.onNavigateTab}) : super(key: key);

  String _formatCurrency(double amount) {
    return NumberFormat.currency(
      locale: 'en_IN',
      symbol: '₹',
      decimalDigits: 0,
    ).format(amount);
  }

  @override
  Widget build(BuildContext context) {
    final fin = context.watch<FinProvider>();
    final user = fin.user;
    final summary = fin.summary;
    final anomalies = fin.activeAnomalies;
    final transactions = fin.transactions.take(5).toList();
    final goals = fin.goals.take(2).toList();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: const PassbookAppBar(),
      body: RefreshIndicator(
        onRefresh: () => fin.refreshAllData(),
        color: AppColors.primary,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Welcome Banner
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Welcome back, ${user?.name.split(' ').first ?? 'User'} 👋',
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 2),
                        const Text(
                          'Here is your live financial snapshot & alerts',
                          style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // Quick Actions Bar
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _buildActionButton(
                      icon: Icons.upload_file,
                      label: 'Statement Import',
                      isPrimary: true,
                      onTap: () => onNavigateTab?.call(1), // Passbook Tab
                    ),
                    const SizedBox(width: 8),
                    _buildActionButton(
                      icon: Icons.auto_awesome,
                      label: 'Ask AI Advisor',
                      onTap: () => onNavigateTab?.call(4), // Chat Tab
                    ),
                    const SizedBox(width: 8),
                    _buildActionButton(
                      icon: Icons.flag_outlined,
                      label: 'New Goal',
                      onTap: () => onNavigateTab?.call(3), // Goals Tab
                    ),
                    const SizedBox(width: 8),
                    _buildActionButton(
                      icon: Icons.analytics_outlined,
                      label: 'Analytics',
                      onTap: () => onNavigateTab?.call(2), // Analytics Tab
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),

              // 4 Stat Cards in 2x2 Grid
              GridView.count(
                crossAxisCount: 2,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                childAspectRatio: 1.08,
                children: [
                  StatCard(
                    title: 'Total Balance',
                    value: _formatCurrency(summary.totalBalance),
                    icon: Icons.account_balance_wallet_outlined,
                    iconColor: AppColors.primary,
                    subtext: 'Liquid balance',
                    isPositive: true,
                  ),
                  StatCard(
                    title: 'This Month',
                    value: _formatCurrency(summary.thisMonthSpend),
                    icon: Icons.shopping_bag_outlined,
                    iconColor: AppColors.warning,
                    subtext: 'Monthly outflow',
                    isPositive: false,
                  ),
                  StatCard(
                    title: 'Savings Rate',
                    value: '${summary.savingsRate.toStringAsFixed(1)}%',
                    icon: Icons.savings_outlined,
                    iconColor: AppColors.success,
                    subtext: summary.savingsRate >= 20 ? 'Optimal (>=20%)' : 'Below 20% target',
                    isPositive: summary.savingsRate >= 20,
                  ),
                  StatCard(
                    title: 'Anomalies Flagged',
                    value: summary.anomaliesCount.toString(),
                    icon: Icons.warning_amber_rounded,
                    iconColor: summary.anomaliesCount > 0 ? AppColors.danger : AppColors.success,
                    subtext: summary.anomaliesCount > 0 ? 'Requires Review' : 'All transactions clear',
                    isPositive: summary.anomaliesCount == 0,
                    onTap: () => onNavigateTab?.call(2),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Anomaly Banner (if any)
              if (anomalies.isNotEmpty) ...[
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.danger.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.danger.withOpacity(0.35)),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: AppColors.danger.withOpacity(0.2),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.warning, color: AppColors.danger, size: 20),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${anomalies.length} Unusual Spend Anomaly Detected',
                              style: const TextStyle(
                                color: AppColors.danger,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              anomalies.first.explanation,
                              style: const TextStyle(color: AppColors.textSecondary, fontSize: 11),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ),
                      ),
                      TextButton(
                        onPressed: () => onNavigateTab?.call(2),
                        child: const Text('Review', style: TextStyle(color: AppColors.danger, fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
              ],

              // Spending Trends Chart
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.cardSurface,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.border),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Spending Trend',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withOpacity(0.12),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: const Text(
                            'Last 6 Months',
                            style: TextStyle(fontSize: 10, color: AppColors.primary, fontWeight: FontWeight.w600),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    SizedBox(
                      height: 160,
                      child: LineChart(
                        LineChartData(
                          gridData: FlGridData(
                            show: true,
                            drawVerticalLine: false,
                            getDrawingHorizontalLine: (val) => FlLine(color: AppColors.border, strokeWidth: 0.8),
                          ),
                          titlesData: FlTitlesData(
                            leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                            topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                            bottomTitles: AxisTitles(
                              sideTitles: SideTitles(
                                showTitles: true,
                                getTitlesWidget: (val, meta) {
                                  final months = ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'];
                                  final idx = val.toInt();
                                  if (idx >= 0 && idx < months.length) {
                                    return Text(months[idx], style: const TextStyle(color: AppColors.textMuted, fontSize: 10));
                                  }
                                  return const Text('');
                                },
                              ),
                            ),
                          ),
                          borderData: FlBorderData(show: false),
                          lineBarsData: [
                            LineChartBarData(
                              spots: const [
                                FlSpot(0, 35),
                                FlSpot(1, 28),
                                FlSpot(2, 42),
                                FlSpot(3, 31),
                                FlSpot(4, 38),
                                FlSpot(5, 34),
                              ],
                              isCurved: true,
                              color: AppColors.primary,
                              barWidth: 3,
                              belowBarData: BarAreaData(
                                show: true,
                                color: AppColors.primary.withOpacity(0.15),
                              ),
                              dotData: const FlDotData(show: false),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // Recent Passbook Transactions Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Recent Transactions',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  TextButton(
                    onPressed: () => onNavigateTab?.call(1),
                    child: const Text('View Passbook', style: TextStyle(color: AppColors.primary, fontSize: 12)),
                  ),
                ],
              ),
              const SizedBox(height: 8),

              // Recent Transactions List
              if (transactions.isEmpty)
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: AppColors.cardSurface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: const Center(
                    child: Text('No transactions recorded yet.', style: TextStyle(color: AppColors.textMuted)),
                  ),
                )
              else
                ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: transactions.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (ctx, i) {
                    final t = transactions[i];
                    final isExpense = t.amount < 0;
                    return Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                      decoration: BoxDecoration(
                        color: AppColors.cardSurface,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  t.description,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w600,
                                    fontSize: 13.5,
                                    color: AppColors.textPrimary,
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    Text(
                                      t.date,
                                      style: const TextStyle(color: AppColors.textMuted, fontSize: 11),
                                    ),
                                    const SizedBox(width: 8),
                                    Flexible(
                                      child: StampBadge(
                                        category: t.category,
                                        isAnomaly: t.isAnomaly,
                                        compact: true,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            (isExpense ? '- ' : '+ ') + _formatCurrency(t.amount.abs()),
                            style: TextStyle(
                              color: isExpense ? AppColors.textPrimary : AppColors.success,
                              fontWeight: FontWeight.bold,
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              const SizedBox(height: 24),

              // Savings Goals Section
              if (goals.isNotEmpty) ...[
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Savings Goals',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    TextButton(
                      onPressed: () => onNavigateTab?.call(3),
                      child: const Text('View All', style: TextStyle(color: AppColors.primary, fontSize: 12)),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: goals.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (ctx, i) {
                    return GoalCard(
                      goal: goals[i],
                      onContribute: (amt) => fin.contributeToGoal(goals[i].id, amt),
                    );
                  },
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    bool isPrimary = false,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
        decoration: BoxDecoration(
          color: isPrimary ? AppColors.primary : AppColors.cardSurface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: isPrimary ? AppColors.primary : AppColors.border),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 14, color: isPrimary ? Colors.white : AppColors.primary),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                fontSize: 11.5,
                fontWeight: FontWeight.w600,
                color: isPrimary ? Colors.white : AppColors.textPrimary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
