import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../models/goal.dart';
import '../providers/fin_provider.dart';
import '../theme/fin_theme.dart';
import '../widgets/goal_card.dart';

class GoalsScreen extends StatefulWidget {
  const GoalsScreen({super.key});

  @override
  State<GoalsScreen> createState() => _GoalsScreenState();
}

class _GoalsScreenState extends State<GoalsScreen> {
  void _showCreateGoalDialog() {
    final nameCtrl = TextEditingController();
    final targetCtrl = TextEditingController();
    final descCtrl = TextEditingController(text: 'Emergency Fund');
    final dateCtrl = TextEditingController(
      text: DateFormat('yyyy-MM-dd').format(DateTime.now().add(const Duration(days: 180))),
    );

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Create Savings Goal', style: GoogleFonts.fraunces(fontSize: 20)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameCtrl,
                decoration: const InputDecoration(labelText: 'Goal Title (e.g. Goa Trip, MacBook)'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: targetCtrl,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Target Amount (₹)'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: descCtrl,
                decoration: const InputDecoration(labelText: 'Category / Purpose'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: dateCtrl,
                decoration: const InputDecoration(labelText: 'Target Date (YYYY-MM-DD)'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('CANCEL'),
          ),
          ElevatedButton(
            onPressed: () async {
              final targetAmt = double.tryParse(targetCtrl.text) ?? 0.0;
              if (nameCtrl.text.isNotEmpty && targetAmt > 0) {
                await context.read<FinProvider>().createGoal(
                  name: nameCtrl.text.trim(),
                  description: descCtrl.text.trim(),
                  targetAmount: targetAmt,
                  targetDate: dateCtrl.text.trim(),
                );
                if (mounted) Navigator.pop(ctx);
              }
            },
            child: const Text('INITIALIZE GOAL'),
          ),
        ],
      ),
    );
  }

  void _showContributeDialog(SavingsGoal goal) {
    final amountCtrl = TextEditingController(text: '5000');

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Contribute to ${goal.name}', style: GoogleFonts.fraunces(fontSize: 18)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Allocate funds toward this goal:',
              style: GoogleFonts.inter(fontSize: 12),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: amountCtrl,
              keyboardType: TextInputType.number,
              autofocus: true,
              decoration: const InputDecoration(labelText: 'Contribution Amount (₹)'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('CANCEL'),
          ),
          ElevatedButton(
            onPressed: () async {
              final amt = double.tryParse(amountCtrl.text) ?? 0.0;
              if (amt > 0) {
                await context.read<FinProvider>().contributeToGoal(goal.id, amt);
                if (mounted) Navigator.pop(ctx);
              }
            },
            child: const Text('CONFIRM ALLOCATION'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final fin = context.watch<FinProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
      child: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 1200),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'SAVINGS TARGETS',
                        style: GoogleFonts.ibmPlexMono(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.5,
                          color: isDark ? FinColors.darkGold : FinColors.lightGold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Financial Milestones (${fin.goals.length})',
                        style: GoogleFonts.fraunces(
                          fontSize: 24,
                          fontWeight: FontWeight.w600,
                          color: isDark ? Colors.white : FinColors.lightInkText,
                        ),
                      ),
                    ],
                  ),
                  ElevatedButton.icon(
                    onPressed: _showCreateGoalDialog,
                    icon: const Icon(Icons.add, size: 16),
                    label: Text(
                      'NEW GOAL',
                      style: GoogleFonts.ibmPlexMono(fontSize: 10, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Goals List / Grid
              if (fin.goals.isEmpty)
                Container(
                  padding: const EdgeInsets.all(40),
                  decoration: BoxDecoration(
                    color: isDark ? FinColors.darkInkRaised : FinColors.lightInkRaised,
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(
                      color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.18),
                    ),
                  ),
                  child: Center(
                    child: Text(
                      'No savings goals created yet. Click "NEW GOAL" to start tracking.',
                      style: GoogleFonts.inter(color: isDark ? FinColors.darkMist : FinColors.lightMist),
                    ),
                  ),
                )
              else
                LayoutBuilder(
                  builder: (context, constraints) {
                    final isNarrow = constraints.maxWidth < 750;
                    return GridView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: fin.goals.length,
                      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: isNarrow ? 1 : 2,
                        crossAxisSpacing: 18,
                        mainAxisSpacing: 18,
                        childAspectRatio: isNarrow ? 1.6 : 1.75,
                      ),
                      itemBuilder: (context, idx) {
                        final g = fin.goals[idx];
                        return GoalCard(
                          goal: g,
                          onContribute: () => _showContributeDialog(g),
                        );
                      },
                    );
                  },
                ),
            ],
          ),
        ),
      ),
    );
  }
}
