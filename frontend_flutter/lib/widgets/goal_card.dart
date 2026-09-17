import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import '../models/goal.dart';
import '../theme/fin_theme.dart';
import 'stamp_badge.dart';

class GoalCard extends StatelessWidget {
  final SavingsGoal goal;
  final VoidCallback onContribute;

  const GoalCard({
    super.key,
    required this.goal,
    required this.onContribute,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final currencyFormatter = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);

    final progress = (goal.targetAmount > 0 ? (goal.currentAmount / goal.targetAmount) : 0.0).clamp(0.0, 1.0);
    final remaining = (goal.targetAmount - goal.currentAmount).clamp(0.0, double.infinity);

    return Container(
      padding: const EdgeInsets.all(20),
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
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      goal.name,
                      style: GoogleFonts.fraunces(
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                        color: isDark ? Colors.white : FinColors.lightInkText,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      goal.description,
                      style: GoogleFonts.inter(
                        fontSize: 12,
                        color: isDark ? FinColors.darkMist : FinColors.lightMist,
                      ),
                    ),
                  ],
                ),
              ),
              StampBadge(
                text: '${(progress * 100).toStringAsFixed(1)}%',
                type: progress >= 1.0 ? StampType.sage : StampType.gold,
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Progress Bar
          ClipRRect(
            borderRadius: BorderRadius.circular(2),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 6,
              backgroundColor: (isDark ? Colors.white : Colors.black).withOpacity(0.08),
              valueColor: AlwaysStoppedAnimation<Color>(
                progress >= 1.0
                    ? (isDark ? FinColors.darkSage : FinColors.lightSage)
                    : (isDark ? FinColors.darkGold : FinColors.lightGold),
              ),
            ),
          ),
          const SizedBox(height: 14),

          // Numbers row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'SAVED',
                    style: GoogleFonts.ibmPlexMono(
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1,
                      color: isDark ? FinColors.darkMist : FinColors.lightMist,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    currencyFormatter.format(goal.currentAmount),
                    style: GoogleFonts.ibmPlexMono(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: isDark ? FinColors.darkSage : FinColors.lightSage,
                    ),
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Text(
                    'REMAINING',
                    style: GoogleFonts.ibmPlexMono(
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1,
                      color: isDark ? FinColors.darkMist : FinColors.lightMist,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    currencyFormatter.format(remaining),
                    style: GoogleFonts.ibmPlexMono(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: isDark ? Colors.white70 : Colors.black54,
                    ),
                  ),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    'TARGET',
                    style: GoogleFonts.ibmPlexMono(
                      fontSize: 9,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1,
                      color: isDark ? FinColors.darkMist : FinColors.lightMist,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    currencyFormatter.format(goal.targetAmount),
                    style: GoogleFonts.ibmPlexMono(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: isDark ? FinColors.darkGold : FinColors.lightGold,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          const Divider(height: 1),
          const SizedBox(height: 12),

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              if (goal.targetDate.isNotEmpty)
                Text(
                  'Target: ${goal.targetDate}',
                  style: GoogleFonts.inter(
                    fontSize: 11,
                    color: isDark ? FinColors.darkMist : FinColors.lightMist,
                  ),
                )
              else
                const SizedBox.shrink(),
              ElevatedButton.icon(
                onPressed: onContribute,
                icon: const Icon(Icons.add, size: 14),
                label: Text(
                  'CONTRIBUTE',
                  style: GoogleFonts.ibmPlexMono(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 1,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.15),
                  foregroundColor: isDark ? FinColors.darkGold : FinColors.lightGold,
                  elevation: 0,
                  side: BorderSide(
                    color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.3),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(2)),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
