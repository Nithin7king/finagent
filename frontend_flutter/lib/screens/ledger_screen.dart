import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../models/transaction.dart';
import '../providers/fin_provider.dart';
import '../services/csv_parser.dart';
import '../theme/fin_theme.dart';
import '../widgets/stamp_badge.dart';

class LedgerScreen extends StatefulWidget {
  const LedgerScreen({super.key});

  @override
  State<LedgerScreen> createState() => _LedgerScreenState();
}

class _LedgerScreenState extends State<LedgerScreen> {
  String searchTerm = '';
  String selectedCategory = 'ALL';

  final categories = [
    'ALL',
    'Food & Dining',
    'Transport',
    'Shopping',
    'Utilities & Bills',
    'Healthcare',
    'Entertainment',
    'Income',
    'Investments',
    'Other',
  ];

  void _showAddTransactionDialog() {
    final descCtrl = TextEditingController();
    final amountCtrl = TextEditingController();
    String category = 'Food & Dining';
    bool isExpense = true;
    final dateCtrl = TextEditingController(text: DateFormat('yyyy-MM-dd').format(DateTime.now()));

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text('Record Transaction', style: GoogleFonts.fraunces(fontSize: 20)),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: ChoiceChip(
                        label: const Text('Expense (-)'),
                        selected: isExpense,
                        onSelected: (val) => setDialogState(() => isExpense = true),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: ChoiceChip(
                        label: const Text('Income (+)'),
                        selected: !isExpense,
                        onSelected: (val) => setDialogState(() => isExpense = false),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: descCtrl,
                  decoration: const InputDecoration(labelText: 'Merchant / Description'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: amountCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Amount (₹)'),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: category,
                  decoration: const InputDecoration(labelText: 'Category'),
                  items: categories
                      .where((c) => c != 'ALL')
                      .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                      .toList(),
                  onChanged: (val) => setDialogState(() => category = val ?? 'Other'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: dateCtrl,
                  decoration: const InputDecoration(labelText: 'Date (YYYY-MM-DD)'),
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
                final amt = double.tryParse(amountCtrl.text) ?? 0.0;
                final finalAmt = isExpense ? -amt.abs() : amt.abs();
                await context.read<FinProvider>().addTransaction(
                  description: descCtrl.text.trim(),
                  amount: finalAmt,
                  category: category,
                  date: dateCtrl.text.trim(),
                );
                if (mounted) Navigator.pop(ctx);
              },
              child: const Text('POST TO LEDGER'),
            ),
          ],
        ),
      ),
    );
  }

  void _showCategoryCorrectionDialog(LedgerTransaction tx) {
    showDialog(
      context: context,
      builder: (ctx) => SimpleDialog(
        title: Text('Correct Category for ${tx.description}', style: GoogleFonts.fraunces(fontSize: 16)),
        children: categories
            .where((c) => c != 'ALL')
            .map(
              (c) => SimpleDialogOption(
                onPressed: () async {
                  await context.read<FinProvider>().correctCategory(tx.id, c);
                  if (mounted) Navigator.pop(ctx);
                },
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Text(c, style: GoogleFonts.inter(fontSize: 14)),
                ),
              ),
            )
            .toList(),
      ),
    );
  }

  void _showCsvImportDialog() {
    final csvCtrl = TextEditingController(
      text: '''Date,Description,Amount,Category\n2026-08-01,Swiggy Delivery,-450,Food & Dining\n2026-08-02,Salary Credit,85000,Income\n2026-08-03,Uber Ride,-240,Transport''',
    );
    List<LedgerTransaction> previewList = [];

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text('Import Bank Statement (CSV)', style: GoogleFonts.fraunces(fontSize: 20)),
          content: SizedBox(
            width: 550,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'Paste CSV content or bank statement rows:',
                    style: GoogleFonts.inter(fontSize: 12),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: csvCtrl,
                    maxLines: 5,
                    style: GoogleFonts.ibmPlexMono(fontSize: 11),
                    decoration: InputDecoration(
                      hintText: 'Date,Description,Amount,Category...',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(4)),
                    ),
                  ),
                  const SizedBox(height: 12),
                  ElevatedButton(
                    onPressed: () {
                      final parsed = CsvStatementParser.parseCsv(csvCtrl.text);
                      setDialogState(() {
                        previewList = parsed;
                      });
                    },
                    child: Text('PARSE CSV STATEMENT (${previewList.length} parsed)'),
                  ),
                  if (previewList.isNotEmpty) ...[
                    const SizedBox(height: 14),
                    Text(
                      'Preview Entries to Commit:',
                      style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 6),
                    SizedBox(
                      height: 140,
                      child: ListView.builder(
                        itemCount: previewList.length,
                        itemBuilder: (context, idx) {
                          final p = previewList[idx];
                          return ListTile(
                            dense: true,
                            title: Text(p.description, style: GoogleFonts.inter(fontSize: 12)),
                            subtitle: Text('${p.date} • ${p.category}'),
                            trailing: Text(
                              '₹${p.amount.toStringAsFixed(0)}',
                              style: GoogleFonts.ibmPlexMono(fontWeight: FontWeight.bold),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('CANCEL'),
            ),
            if (previewList.isNotEmpty)
              ElevatedButton(
                onPressed: () async {
                  await context.read<FinProvider>().commitCsvTransactions(previewList);
                  if (mounted) Navigator.pop(ctx);
                },
                child: Text('COMMIT ALL (${previewList.length})'),
              ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final fin = context.watch<FinProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final currencyFormatter = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);

    final filtered = fin.transactions.where((t) {
      final matchesSearch = t.description.toLowerCase().contains(searchTerm.toLowerCase()) ||
          t.category.toLowerCase().contains(searchTerm.toLowerCase());
      final matchesCat = selectedCategory == 'ALL' || t.category == selectedCategory;
      return matchesSearch && matchesCat;
    }).toList();

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
      child: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 1200),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header Controls
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'TRANSACTION LEDGER',
                        style: GoogleFonts.ibmPlexMono(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.5,
                          color: isDark ? FinColors.darkGold : FinColors.lightGold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Passbook Records (${filtered.length})',
                        style: GoogleFonts.fraunces(
                          fontSize: 24,
                          fontWeight: FontWeight.w600,
                          color: isDark ? Colors.white : FinColors.lightInkText,
                        ),
                      ),
                    ],
                  ),
                  Row(
                    children: [
                      OutlinedButton.icon(
                        onPressed: _showCsvImportDialog,
                        icon: const Icon(Icons.upload_file, size: 16),
                        label: Text(
                          'IMPORT CSV',
                          style: GoogleFonts.ibmPlexMono(fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ),
                      const SizedBox(width: 10),
                      ElevatedButton.icon(
                        onPressed: _showAddTransactionDialog,
                        icon: const Icon(Icons.add, size: 16),
                        label: Text(
                          'RECORD ENTRY',
                          style: GoogleFonts.ibmPlexMono(fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // Search & Category Chips
              TextField(
                decoration: InputDecoration(
                  hintText: 'Search ledger by merchant, notes, category...',
                  prefixIcon: const Icon(Icons.search, size: 18),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(4)),
                ),
                onChanged: (val) => setState(() => searchTerm = val),
              ),
              const SizedBox(height: 14),

              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: categories.map((cat) {
                    final isSel = selectedCategory == cat;
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: FilterChip(
                        label: Text(cat),
                        selected: isSel,
                        onSelected: (val) => setState(() => selectedCategory = cat),
                        labelStyle: GoogleFonts.inter(
                          fontSize: 11,
                          fontWeight: isSel ? FontWeight.bold : FontWeight.normal,
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),
              const SizedBox(height: 20),

              // Ledger Table Container
              Container(
                decoration: BoxDecoration(
                  color: isDark ? FinColors.darkInkRaised : FinColors.lightInkRaised,
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(
                    color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.2),
                  ),
                ),
                child: filtered.isEmpty
                    ? Padding(
                        padding: const EdgeInsets.all(40),
                        child: Center(
                          child: Text(
                            'No transactions match your current search/filters.',
                            style: GoogleFonts.inter(color: isDark ? FinColors.darkMist : FinColors.lightMist),
                          ),
                        ),
                      )
                    : ListView.separated(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        itemCount: filtered.length,
                        separatorBuilder: (context, idx) => Divider(
                          height: 1,
                          color: (isDark ? Colors.white : Colors.black).withOpacity(0.06),
                        ),
                        itemBuilder: (context, index) {
                          final tx = filtered[index];
                          final isCredit = tx.amount > 0;
                          final amountColor = isCredit
                              ? (isDark ? FinColors.darkSage : FinColors.lightSage)
                              : (isDark ? FinColors.darkCoral : FinColors.lightCoral);

                          return InkWell(
                            onTap: () => _showCategoryCorrectionDialog(tx),
                            child: Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                              child: Row(
                                children: [
                                  // Date
                                  SizedBox(
                                    width: 85,
                                    child: Text(
                                      tx.date,
                                      style: GoogleFonts.ibmPlexMono(
                                        fontSize: 11,
                                        color: isDark ? FinColors.darkMist : FinColors.lightMist,
                                      ),
                                    ),
                                  ),
                                  // Description + Category badge
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          children: [
                                            Text(
                                              tx.description,
                                              style: GoogleFonts.inter(
                                                fontSize: 13,
                                                fontWeight: FontWeight.w600,
                                              ),
                                            ),
                                            if (tx.isAnomaly) ...[
                                              const SizedBox(width: 8),
                                              StampBadge(
                                                text: 'ANOMALY',
                                                type: StampType.coral,
                                                icon: Icons.warning_amber_rounded,
                                              ),
                                            ],
                                          ],
                                        ),
                                        const SizedBox(height: 4),
                                        Row(
                                          children: [
                                            StampBadge(text: tx.category, type: StampType.gold),
                                            const SizedBox(width: 6),
                                            Text(
                                              tx.status,
                                              style: GoogleFonts.inter(
                                                fontSize: 10,
                                                color: isDark ? FinColors.darkMist : FinColors.lightMist,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ],
                                    ),
                                  ),
                                  // Amount
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.end,
                                    children: [
                                      Text(
                                        '${isCredit ? "+" : "-"} ${currencyFormatter.format(tx.amount.abs())}',
                                        style: GoogleFonts.ibmPlexMono(
                                          fontSize: 14,
                                          fontWeight: FontWeight.bold,
                                          color: amountColor,
                                        ),
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        'Bal: ${currencyFormatter.format(tx.balanceAfter)}',
                                        style: GoogleFonts.ibmPlexMono(
                                          fontSize: 10,
                                          color: isDark ? FinColors.darkMist : FinColors.lightMist,
                                        ),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
