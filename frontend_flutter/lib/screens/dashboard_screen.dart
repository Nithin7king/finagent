import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../providers/fin_provider.dart';
import '../theme/fin_theme.dart';
import '../widgets/stat_card.dart';
import '../widgets/stamp_badge.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final fin = context.watch<FinProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final currencyFormatter = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
      child: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 1200),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Welcome Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'AUTONOMOUS PERSONAL LEDGER',
                        style: GoogleFonts.ibmPlexMono(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.5,
                          color: isDark ? FinColors.darkGold : FinColors.lightGold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Welcome, ${fin.user?.name ?? 'User'}',
                        style: GoogleFonts.fraunces(
                          fontSize: 28,
                          fontWeight: FontWeight.w600,
                          fontStyle: FontStyle.italic,
                          color: isDark ? Colors.white : FinColors.lightInkText,
                        ),
                      ),
                    ],
                  ),
                  IconButton(
                    icon: const Icon(Icons.refresh),
                    tooltip: 'Refresh Ledger',
                    onPressed: () => fin.refreshAllData(),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // KPI Stats Grid
              LayoutBuilder(
                builder: (context, constraints) {
                  final isNarrow = constraints.maxWidth < 750;
                  return GridView.count(
                    crossAxisCount: isNarrow ? 2 : 4,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisSpacing: 16,
                    mainAxisSpacing: 16,
                    childAspectRatio: isNarrow ? 1.6 : 2.0,
                    children: [
                      StatCard(
                        label: 'Total Balance',
                        value: currencyFormatter.format(fin.summary.totalBalance),
                        icon: Icons.account_balance_wallet_outlined,
                        accentColor: fin.summary.totalBalance >= 0
                            ? (isDark ? FinColors.darkSage : FinColors.lightSage)
                            : (isDark ? FinColors.darkCoral : FinColors.lightCoral),
                      ),
                      StatCard(
                        label: '30D Expenses',
                        value: currencyFormatter.format(fin.summary.thisMonthSpend),
                        icon: Icons.arrow_outward_outlined,
                        accentColor: isDark ? FinColors.darkCoral : FinColors.lightCoral,
                      ),
                      StatCard(
                        label: 'Savings Rate',
                        value: '${fin.summary.savingsRate.toStringAsFixed(1)}%',
                        icon: Icons.pie_chart_outline,
                        accentColor: isDark ? FinColors.darkGold : FinColors.lightGold,
                      ),
                      StatCard(
                        label: 'Anomalies Flagged',
                        value: fin.summary.anomaliesCount.toString(),
                        icon: Icons.warning_amber_outlined,
                        accentColor: fin.summary.anomaliesCount > 0
                            ? (isDark ? FinColors.darkCoral : FinColors.lightCoral)
                            : (isDark ? FinColors.darkSage : FinColors.lightSage),
                      ),
                    ],
                  );
                },
              ),
              const SizedBox(height: 28),

              // Urgent Anomaly Banner if any exist
              if (fin.activeAnomalies.isNotEmpty) ...[
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: (isDark ? FinColors.darkCoral : FinColors.lightCoral).withOpacity(0.08),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(
                      color: (isDark ? FinColors.darkCoral : FinColors.lightCoral).withOpacity(0.35),
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.crisis_alert_outlined,
                        size: 24,
                        color: isDark ? FinColors.darkCoral : FinColors.lightCoral,
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'ML ANOMALY MONITOR: ${fin.activeAnomalies.length} UNUSUAL TRANSACTIONS FLAGGED',
                              style: GoogleFonts.ibmPlexMono(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 1,
                                color: isDark ? FinColors.darkCoral : FinColors.lightCoral,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              fin.activeAnomalies.first.explanation ??
                                  'IsolationForest detected unusual spending patterns relative to your history.',
                              style: GoogleFonts.inter(
                                fontSize: 12,
                                color: isDark ? Colors.white70 : FinColors.lightInkText,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      ElevatedButton(
                        onPressed: () => fin.setNavIndex(1), // Go to Ledger
                        style: ElevatedButton.styleFrom(
                          backgroundColor: (isDark ? FinColors.darkCoral : FinColors.lightCoral).withOpacity(0.2),
                          foregroundColor: isDark ? FinColors.darkCoral : FinColors.lightCoral,
                          elevation: 0,
                          side: BorderSide(
                            color: (isDark ? FinColors.darkCoral : FinColors.lightCoral).withOpacity(0.5),
                          ),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(2)),
                        ),
                        child: Text(
                          'AUDIT LEDGER',
                          style: GoogleFonts.ibmPlexMono(fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 28),
              ],

              // Spending History Area Chart
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: isDark ? FinColors.darkInkRaised : FinColors.lightInkRaised,
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(
                    color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.18),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'EXPENDITURE TRAJECTORY',
                              style: GoogleFonts.ibmPlexMono(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 1.5,
                                color: isDark ? FinColors.darkGold : FinColors.lightGold,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Monthly Category Outflows',
                              style: GoogleFonts.fraunces(
                                fontSize: 18,
                                fontWeight: FontWeight.w600,
                                color: isDark ? Colors.white : FinColors.lightInkText,
                              ),
                            ),
                          ],
                        ),
                        Row(
                          children: [
                            StampBadge(text: 'Food', type: StampType.gold),
                            const SizedBox(width: 6),
                            StampBadge(text: 'Investments', type: StampType.sage),
                            const SizedBox(width: 6),
                            StampBadge(text: 'Shopping', type: StampType.coral),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 28),
                    SizedBox(
                      height: 240,
                      child: LineChart(
                        LineChartData(
                          gridData: FlGridData(
                            show: true,
                            drawVerticalLine: false,
                            getDrawingHorizontalLine: (val) => FlLine(
                              color: (isDark ? Colors.white : Colors.black).withOpacity(0.05),
                              strokeWidth: 1,
                            ),
                          ),
                          titlesData: FlTitlesData(
                            leftTitles: AxisTitles(
                              sideTitles: SideTitles(
                                showTitles: true,
                                reservedSize: 44,
                                getTitlesWidget: (val, meta) => Text(
                                  '₹${(val / 1000).toInt()}k',
                                  style: GoogleFonts.ibmPlexMono(
                                    fontSize: 9,
                                    color: isDark ? FinColors.darkMist : FinColors.lightMist,
                                  ),
                                ),
                              ),
                            ),
                            bottomTitles: AxisTitles(
                              sideTitles: SideTitles(
                                showTitles: true,
                                getTitlesWidget: (val, meta) {
                                  const months = ['Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'];
                                  final idx = val.toInt();
                                  if (idx >= 0 && idx < months.length) {
                                    return Padding(
                                      padding: const EdgeInsets.only(top: 8),
                                      child: Text(
                                        months[idx],
                                        style: GoogleFonts.ibmPlexMono(
                                          fontSize: 10,
                                          color: isDark ? FinColors.darkMist : FinColors.lightMist,
                                        ),
                                      ),
                                    );
                                  }
                                  return const SizedBox.shrink();
                                },
                              ),
                            ),
                            topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                            rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          ),
                          borderData: FlBorderData(show: false),
                          lineBarsData: [
                            // Food & Dining Line
                            LineChartBarData(
                              spots: const [
                                FlSpot(0, 15400),
                                FlSpot(1, 14200),
                                FlSpot(2, 16100),
                                FlSpot(3, 13900),
                                FlSpot(4, 15200),
                                FlSpot(5, 13800),
                              ],
                              isCurved: true,
                              color: isDark ? FinColors.darkGold : FinColors.lightGold,
                              barWidth: 2.5,
                              belowBarData: BarAreaData(
                                show: true,
                                color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.12),
                              ),
                              dotData: const FlDotData(show: false),
                            ),
                            // Investment Line
                            LineChartBarData(
                              spots: const [
                                FlSpot(0, 20000),
                                FlSpot(1, 25000),
                                FlSpot(2, 25000),
                                FlSpot(3, 30000),
                                FlSpot(4, 30000),
                                FlSpot(5, 30000),
                              ],
                              isCurved: true,
                              color: isDark ? FinColors.darkSage : FinColors.lightSage,
                              barWidth: 2.5,
                              belowBarData: BarAreaData(
                                show: true,
                                color: (isDark ? FinColors.darkSage : FinColors.lightSage).withOpacity(0.08),
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
            ],
          ),
        ),
      ),
    );
  }
}
