import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'package:file_picker/file_picker.dart';
import '../config/app_theme.dart';
import '../providers/fin_provider.dart';
import '../models/transaction_model.dart';
import '../widgets/stamp_badge.dart';
import '../widgets/passbook_app_bar.dart';

class LedgerScreen extends StatefulWidget {
  const LedgerScreen({Key? key}) : super(key: key);

  @override
  State<LedgerScreen> createState() => _LedgerScreenState();
}

class _LedgerScreenState extends State<LedgerScreen> {
  String _searchTerm = '';
  String _selectedCategory = 'ALL';
  String _typeFilter = 'ALL'; // 'ALL' | 'EXPENSE' | 'INCOME'

  final List<String> _categories = [
    'ALL', 'Salary', 'Investment', 'Housing', 'Food', 'Utilities', 'Transport', 'Shopping', 'Entertainment', 'Others'
  ];

  String _formatCurrency(double val) {
    final formatted = NumberFormat.currency(
      locale: 'en_IN',
      symbol: '₹',
      decimalDigits: 0,
    ).format(val.abs());
    return val < 0 ? '- $formatted' : '+ $formatted';
  }

  String _formatBalance(double val) {
    return NumberFormat.currency(
      locale: 'en_IN',
      symbol: '₹',
      decimalDigits: 0,
    ).format(val);
  }

  Future<void> _handleUploadPdf(FinProvider fin) async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'csv'],
      withData: true,
    );

    if (result != null && result.files.isNotEmpty) {
      final file = result.files.first;
      if (file.bytes == null) return;

      // Try initial upload
      final res = await fin.uploadPdfStatement(file.bytes!, file.name);

      if (res['requires_password'] == true && mounted) {
        // Prompt for PDF Password (Indian bank statement encryption)
        _promptPdfPassword(fin, file.bytes!, file.name);
      } else if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            backgroundColor: res['success'] == true ? AppColors.success : AppColors.danger,
            content: Text(res['message'] ?? 'Statement uploaded successfully!'),
          ),
        );
      }
    }
  }

  void _promptPdfPassword(FinProvider fin, dynamic bytes, String fileName) {
    final passwordController = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          backgroundColor: AppColors.cardSurfaceRaised,
          title: const Row(
            children: [
              Icon(Icons.lock_outline, color: AppColors.warning, size: 20),
              SizedBox(width: 8),
              Text('Encrypted PDF Statement', style: TextStyle(fontSize: 16)),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'This bank statement is password protected (e.g. HDFC, ICICI, SBI). Enter the statement password to unlock and import transactions.',
                style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: passwordController,
                obscureText: true,
                decoration: const InputDecoration(
                  hintText: 'Statement Password',
                  prefixIcon: Icon(Icons.key, size: 16),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel', style: TextStyle(color: AppColors.textSecondary)),
            ),
            ElevatedButton(
              onPressed: () async {
                final pwd = passwordController.text.trim();
                Navigator.pop(ctx);
                final res = await fin.uploadPdfStatement(bytes, fileName, password: pwd);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      backgroundColor: res['success'] == true ? AppColors.success : AppColors.danger,
                      content: Text(res['message'] ?? 'Statement decrypted and imported!'),
                    ),
                  );
                }
              },
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary),
              child: const Text('Decrypt & Import'),
            ),
          ],
        );
      },
    );
  }

  void _showAddTransactionSheet(BuildContext context, FinProvider fin) {
    final descController = TextEditingController();
    final amountController = TextEditingController();
    String selectedCat = 'Food';
    bool isExpense = true;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.cardSurfaceRaised,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setSheetState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 24,
                bottom: MediaQuery.of(ctx).viewInsets.bottom + 24,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Add Passbook Entry', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: ChoiceChip(
                          label: const Center(child: Text('Expense')),
                          selected: isExpense,
                          selectedColor: AppColors.danger.withOpacity(0.2),
                          onSelected: (_) => setSheetState(() => isExpense = true),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: ChoiceChip(
                          label: const Center(child: Text('Income')),
                          selected: !isExpense,
                          selectedColor: AppColors.success.withOpacity(0.2),
                          onSelected: (_) => setSheetState(() => isExpense = false),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: descController,
                    decoration: const InputDecoration(
                      hintText: 'Merchant / Description (e.g. Swiggy, Netflix)',
                      prefixIcon: Icon(Icons.description_outlined, size: 18),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: amountController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      hintText: 'Amount',
                      prefixText: '₹ ',
                      prefixIcon: Icon(Icons.currency_rupee, size: 18),
                    ),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    value: selectedCat,
                    dropdownColor: AppColors.cardSurfaceRaised,
                    decoration: const InputDecoration(
                      prefixIcon: Icon(Icons.category_outlined, size: 18),
                    ),
                    items: _categories.where((c) => c != 'ALL').map((c) {
                      return DropdownMenuItem(value: c, child: Text(c));
                    }).toList(),
                    onChanged: (val) {
                      if (val != null) setSheetState(() => selectedCat = val);
                    },
                  ),
                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton(
                      onPressed: () async {
                        final desc = descController.text.trim();
                        final rawAmt = double.tryParse(amountController.text.trim());
                        if (desc.isNotEmpty && rawAmt != null && rawAmt > 0) {
                          final finalAmt = isExpense ? -rawAmt : rawAmt;
                          final dateStr = DateFormat('yyyy-MM-dd').format(DateTime.now());
                          Navigator.pop(ctx);
                          await fin.addTransaction(
                            description: desc,
                            amount: finalAmt,
                            category: selectedCat,
                            date: dateStr,
                          );
                        }
                      },
                      style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary),
                      child: const Text('Save to Passbook', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final fin = context.watch<FinProvider>();
    final allTransactions = fin.transactions;

    // Filter logic matching Ledger.tsx
    final filtered = allTransactions.where((t) {
      final matchesSearch = t.description.toLowerCase().contains(_searchTerm.toLowerCase()) ||
                            t.category.toLowerCase().contains(_searchTerm.toLowerCase());
      final matchesCategory = _selectedCategory == 'ALL' || t.category == _selectedCategory;
      final matchesType = _typeFilter == 'ALL' ||
                          (_typeFilter == 'EXPENSE' ? t.amount < 0 : t.amount > 0);
      return matchesSearch && matchesCategory && matchesType;
    }).toList();


    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: const PassbookAppBar(title: 'Passbook Ledger'),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showAddTransactionSheet(context, fin),
        backgroundColor: AppColors.primary,
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text('Add Entry', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
      ),
      body: Column(
        children: [
          // Search & Action Header
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    onChanged: (val) => setState(() => _searchTerm = val),
                    decoration: InputDecoration(
                      hintText: 'Search merchant or category...',
                      prefixIcon: const Icon(Icons.search, size: 18),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      isDense: true,
                      suffixIcon: _searchTerm.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear, size: 16),
                              onPressed: () => setState(() => _searchTerm = ''),
                            )
                          : null,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                InkWell(
                  onTap: () => _handleUploadPdf(fin),
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.primary.withOpacity(0.3)),
                    ),
                    child: const Icon(Icons.upload_file, size: 20, color: AppColors.primary),
                  ),
                ),
              ],
            ),
          ),

          // Category Filter Pills
          SizedBox(
            height: 38,
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              scrollDirection: Axis.horizontal,
              itemCount: _categories.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (ctx, i) {
                final cat = _categories[i];
                final isSelected = _selectedCategory == cat;
                return ChoiceChip(
                  label: Text(cat),
                  labelStyle: TextStyle(
                    fontSize: 11.5,
                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                    color: isSelected ? Colors.white : AppColors.textSecondary,
                  ),
                  selected: isSelected,
                  selectedColor: AppColors.primary,
                  backgroundColor: AppColors.cardSurface,
                  side: BorderSide(color: isSelected ? AppColors.primary : AppColors.border),
                  onSelected: (_) => setState(() => _selectedCategory = cat),
                );
              },
            ),
          ),
          const SizedBox(height: 10),

          // Passbook Entries List
          Expanded(
            child: filtered.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.receipt_long_outlined, size: 48, color: AppColors.textMuted.withOpacity(0.5)),
                        const SizedBox(height: 12),
                        const Text('No transactions match your search.', style: TextStyle(color: AppColors.textMuted)),
                      ],
                    ),
                  )
                : ListView.separated(
                    padding: const EdgeInsets.only(left: 16, right: 16, top: 4, bottom: 80),
                    itemCount: filtered.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (ctx, i) {
                      final t = filtered[i];
                      final isExpense = t.amount < 0;

                      return Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: AppColors.cardSurface,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(
                            color: t.isAnomaly ? AppColors.danger.withOpacity(0.4) : AppColors.border,
                          ),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    t.description,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 14,
                                      color: AppColors.textPrimary,
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                  const SizedBox(height: 5),
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
                                          status: t.status,
                                          compact: true,
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(width: 8),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text(
                                  _formatCurrency(t.amount),
                                  style: TextStyle(
                                    fontWeight: FontWeight.w800,
                                    fontSize: 15,
                                    color: isExpense ? AppColors.textPrimary : AppColors.success,
                                  ),
                                ),
                                const SizedBox(height: 3),
                                Text(
                                  'Bal: ${_formatBalance(t.balanceAfter)}',
                                  style: const TextStyle(
                                    fontSize: 11,
                                    color: AppColors.textMuted,
                                    fontFamily: 'monospace',
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

