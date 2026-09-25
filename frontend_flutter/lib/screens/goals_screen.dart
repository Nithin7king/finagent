import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../config/app_theme.dart';
import '../providers/fin_provider.dart';
import '../widgets/goal_card.dart';
import '../widgets/passbook_app_bar.dart';

class GoalsScreen extends StatelessWidget {
  const GoalsScreen({Key? key}) : super(key: key);

  void _showCreateGoalDialog(BuildContext context, FinProvider fin) {
    final nameController = TextEditingController();
    final targetAmountController = TextEditingController();
    final currentAmountController = TextEditingController(text: '0');
    final targetDateController = TextEditingController(
      text: DateFormat('yyyy-MM-dd').format(DateTime.now().add(const Duration(days: 365))),
    );
    String selectedCategory = 'Emergency Fund';

    final categories = ['Emergency Fund', 'Travel', 'Vehicle', 'Gadget', 'Home', 'Investment'];

    showDialog(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setDialogState) {
            return AlertDialog(
              backgroundColor: AppColors.cardSurfaceRaised,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              title: const Row(
                children: [
                  Icon(Icons.flag_outlined, color: AppColors.primary, size: 20),
                  SizedBox(width: 8),
                  Text('Create Savings Goal', style: TextStyle(fontSize: 16)),
                ],
              ),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextField(
                      controller: nameController,
                      decoration: const InputDecoration(
                        hintText: 'Goal Name (e.g. Goa Trip, New Laptop)',
                        prefixIcon: Icon(Icons.edit_outlined, size: 18),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: targetAmountController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        hintText: 'Target Amount',
                        prefixText: '₹ ',
                        prefixIcon: Icon(Icons.currency_rupee, size: 18),
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: currentAmountController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        hintText: 'Starting Saved Amount',
                        prefixText: '₹ ',
                        prefixIcon: Icon(Icons.savings_outlined, size: 18),
                      ),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      value: selectedCategory,
                      dropdownColor: AppColors.cardSurfaceRaised,
                      decoration: const InputDecoration(
                        prefixIcon: Icon(Icons.category_outlined, size: 18),
                      ),
                      items: categories.map((c) {
                        return DropdownMenuItem(value: c, child: Text(c));
                      }).toList(),
                      onChanged: (val) {
                        if (val != null) setDialogState(() => selectedCategory = val);
                      },
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Cancel', style: TextStyle(color: AppColors.textSecondary)),
                ),
                ElevatedButton(
                  onPressed: () async {
                    final name = nameController.text.trim();
                    final target = double.tryParse(targetAmountController.text.trim());
                    final current = double.tryParse(currentAmountController.text.trim()) ?? 0.0;
                    if (name.isNotEmpty && target != null && target > 0) {
                      Navigator.pop(ctx);
                      await fin.createGoal(
                        name: name,
                        targetAmount: target,
                        currentAmount: current,
                        targetDate: targetDateController.text,
                        category: selectedCategory,
                      );
                    }
                  },
                  style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary),
                  child: const Text('Create Goal'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final fin = context.watch<FinProvider>();
    final goals = fin.goals;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: const PassbookAppBar(title: 'Savings Targets'),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateGoalDialog(context, fin),
        backgroundColor: AppColors.primary,
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text('New Goal', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
      ),
      body: goals.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.12),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.flag_outlined, size: 48, color: AppColors.primary),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'No Savings Goals Yet',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Create an emergency fund or milestone savings goal to track your growth.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                  ),
                ],
              ),
            )
          : RefreshIndicator(
              onRefresh: () => fin.refreshAllData(),
              color: AppColors.primary,
              backgroundColor: AppColors.cardSurfaceRaised,
              child: ListView.builder(
                padding: const EdgeInsets.only(left: 16, right: 16, top: 12, bottom: 85),
                itemCount: goals.length + 1,
                itemBuilder: (ctx, i) {
                  if (i == 0) {
                    return Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withOpacity(0.08),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.primary.withOpacity(0.2)),
                      ),
                      child: const Row(
                        children: [
                          Icon(Icons.auto_awesome, color: AppColors.primary, size: 16),
                          SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'AI Recommender active: tap "AI Goal Accelerator" on any goal to unlock early completion strategies.',
                              style: TextStyle(
                                fontSize: 11,
                                color: AppColors.textSecondary,
                                height: 1.3,
                              ),
                            ),
                          ),
                        ],
                      ),
                    );
                  }
                  final g = goals[i - 1];
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: GoalCard(
                      goal: g,
                      onContribute: (amt) => fin.contributeToGoal(g.id, amt),
                      onDelete: () => fin.deleteGoal(g.id),
                    ),
                  );
                },
              ),
            ),
    );
  }
}
