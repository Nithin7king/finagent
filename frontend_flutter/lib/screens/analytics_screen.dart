import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/fin_provider.dart';
import '../services/api_service.dart';
import '../theme/fin_theme.dart';
import '../widgets/stamp_badge.dart';

class AnalyticsScreen extends StatefulWidget {
  const AnalyticsScreen({super.key});

  @override
  State<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends State<AnalyticsScreen> {
  String whatIfCategory = 'Food & Dining';
  double reductionPct = 20.0;
  Map<String, dynamic>? whatIfResult;
  bool isCalculating = false;

  final categories = [
    'Food & Dining',
    'Shopping',
    'Entertainment',
    'Transport',
    'Utilities & Bills',
    'Travel',
  ];

  @override
  void initState() {
    super.initState();
    _runWhatIf();
  }

  void _runWhatIf() async {
    setState(() => isCalculating = true);
    try {
      final res = await ApiService.getWhatIfSimulator(
        category: whatIfCategory,
        reductionPct: reductionPct,
      );
      setState(() => whatIfResult = res);
    } catch (e) {
      debugPrint('What-If error: $e');
    } finally {
      setState(() => isCalculating = false);
    }
  }

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
              // Header
              Text(
                'PREDICTIVE INTELLIGENCE',
                style: GoogleFonts.ibmPlexMono(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 1.5,
                  color: isDark ? FinColors.darkGold : FinColors.lightGold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Forecasts & Behavior Analytics',
                style: GoogleFonts.fraunces(
                  fontSize: 24,
                  fontWeight: FontWeight.w600,
                  color: isDark ? Colors.white : FinColors.lightInkText,
                ),
              ),
              const SizedBox(height: 24),

              // Forecast Cards Row (30, 60, 90 days)
              Row(
                children: fin.forecast.map((f) {
                  return Expanded(
                    child: Container(
                      margin: const EdgeInsets.symmetric(horizontal: 6),
                      padding: const EdgeInsets.all(18),
                      decoration: BoxDecoration(
                        color: isDark ? FinColors.darkInkRaised : FinColors.lightInkRaised,
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(
                          color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.2),
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            f.label.toUpperCase(),
                            style: GoogleFonts.ibmPlexMono(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1,
                              color: isDark ? FinColors.darkMist : FinColors.lightMist,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            currencyFormatter.format(f.projected),
                            style: GoogleFonts.ibmPlexMono(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              color: isDark ? FinColors.darkGold : FinColors.lightGold,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Band: ${currencyFormatter.format(f.confidenceMin)} – ${currencyFormatter.format(f.confidenceMax)}',
                            style: GoogleFonts.inter(
                              fontSize: 10,
                              color: isDark ? FinColors.darkMist : FinColors.lightMist,
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 28),

              // Subscription Creep & What-If simulator row
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Subscription Creep Container
                  Expanded(
                    flex: 1,
                    child: Container(
                      padding: const EdgeInsets.all(22),
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
                              Text(
                                'SUBSCRIPTION CREEP',
                                style: GoogleFonts.ibmPlexMono(
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                  letterSpacing: 1.5,
                                  color: isDark ? FinColors.darkGold : FinColors.lightGold,
                                ),
                              ),
                              StampBadge(
                                text: '${fin.subscriptions.length} RECURRING',
                                type: StampType.sage,
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          if (fin.subscriptions.isEmpty)
                            Padding(
                              padding: const EdgeInsets.symmetric(vertical: 20),
                              child: Text(
                                'No recurring charges detected in 180-day history.',
                                style: GoogleFonts.inter(fontSize: 12, color: FinColors.darkMist),
                              ),
                            )
                          else
                            ListView.separated(
                              shrinkWrap: true,
                              physics: const NeverScrollableScrollPhysics(),
                              itemCount: fin.subscriptions.length,
                              separatorBuilder: (context, idx) => const Divider(height: 12),
                              itemBuilder: (context, idx) {
                                final sub = fin.subscriptions[idx];
                                return Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          sub.merchant,
                                          style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w600),
                                        ),
                                        Text(
                                          'Due: ${sub.nextChargeDate} • ${sub.cadence}',
                                          style: GoogleFonts.inter(fontSize: 10, color: FinColors.darkMist),
                                        ),
                                      ],
                                    ),
                                    Text(
                                      currencyFormatter.format(sub.amount),
                                      style: GoogleFonts.ibmPlexMono(
                                        fontSize: 13,
                                        fontWeight: FontWeight.bold,
                                        color: isDark ? FinColors.darkCoral : FinColors.lightCoral,
                                      ),
                                    ),
                                  ],
                                );
                              },
                            ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 20),

                  // What-If Simulator
                  Expanded(
                    flex: 1,
                    child: Container(
                      padding: const EdgeInsets.all(22),
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
                          Text(
                            'WHAT-IF EXPENDITURE CUT SIMULATOR',
                            style: GoogleFonts.ibmPlexMono(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 1.5,
                              color: isDark ? FinColors.darkGold : FinColors.lightGold,
                            ),
                          ),
                          const SizedBox(height: 14),

                          DropdownButtonFormField<String>(
                            value: whatIfCategory,
                            decoration: const InputDecoration(
                              labelText: 'Target Category',
                              isDense: true,
                            ),
                            items: categories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                            onChanged: (val) {
                              if (val != null) {
                                setState(() => whatIfCategory = val);
                                _runWhatIf();
                              }
                            },
                          ),
                          const SizedBox(height: 16),

                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                'Reduction Percentage:',
                                style: GoogleFonts.inter(fontSize: 12),
                              ),
                              Text(
                                '${reductionPct.toInt()}%',
                                style: GoogleFonts.ibmPlexMono(
                                  fontSize: 14,
                                  fontWeight: FontWeight.bold,
                                  color: isDark ? FinColors.darkGold : FinColors.lightGold,
                                ),
                              ),
                            ],
                          ),
                          Slider(
                            value: reductionPct,
                            min: 5,
                            max: 75,
                            divisions: 14,
                            activeColor: isDark ? FinColors.darkGold : FinColors.lightGold,
                            onChanged: (val) {
                              setState(() => reductionPct = val);
                              _runWhatIf();
                            },
                          ),
                          const SizedBox(height: 12),

                          if (whatIfResult != null && !isCalculating) ...[
                            Container(
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(
                                color: (isDark ? FinColors.darkSage : FinColors.lightSage).withOpacity(0.08),
                                borderRadius: BorderRadius.circular(4),
                                border: Border.all(
                                  color: (isDark ? FinColors.darkSage : FinColors.lightSage).withOpacity(0.3),
                                ),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text(
                                        'MONTHLY SAVINGS:',
                                        style: GoogleFonts.ibmPlexMono(
                                          fontSize: 10,
                                          fontWeight: FontWeight.bold,
                                          color: isDark ? FinColors.darkSage : FinColors.lightSage,
                                        ),
                                      ),
                                      Text(
                                        currencyFormatter.format(whatIfResult!['monthly_savings'] ?? 0),
                                        style: GoogleFonts.ibmPlexMono(
                                          fontSize: 14,
                                          fontWeight: FontWeight.bold,
                                          color: isDark ? FinColors.darkSage : FinColors.lightSage,
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 4),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Text(
                                        'ANNUAL COMPOUNDED:',
                                        style: GoogleFonts.ibmPlexMono(
                                          fontSize: 10,
                                          fontWeight: FontWeight.bold,
                                          color: isDark ? FinColors.darkGold : FinColors.lightGold,
                                        ),
                                      ),
                                      Text(
                                        currencyFormatter.format(whatIfResult!['annual_savings'] ?? 0),
                                        style: GoogleFonts.ibmPlexMono(
                                          fontSize: 14,
                                          fontWeight: FontWeight.bold,
                                          color: isDark ? FinColors.darkGold : FinColors.lightGold,
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 8),
                                  Text(
                                    whatIfResult!['insight'] ?? '',
                                    style: GoogleFonts.inter(fontSize: 11, height: 1.4),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
