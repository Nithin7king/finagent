import '../models/transaction.dart';

class CsvStatementParser {
  static List<LedgerTransaction> parseCsv(String csvContent) {
    final lines = csvContent.trim().split(RegExp(r'\r?\n'));
    if (lines.isEmpty) return [];

    final headerLine = lines.removeAt(0);
    final headers = headerLine
        .split(',')
        .map((h) => h.trim().toLowerCase().replaceAll('"', ''))
        .toList();

    final dateIndex = headers.indexWhere((h) => h.contains('date'));
    final descIndex = headers.indexWhere((h) => h.contains('desc') || h.contains('merchant') || h.contains('narration'));
    final amountIndex = headers.indexWhere((h) => h.contains('amount') || h.contains('debit') || h.contains('credit'));
    final catIndex = headers.indexWhere((h) => h.contains('category') || h.contains('tag'));

    final List<LedgerTransaction> parsedList = [];
    int index = 0;

    for (final line in lines) {
      if (line.trim().isEmpty) continue;
      final values = line
          .split(',')
          .map((v) => v.trim().replaceAll('"', ''))
          .toList();

      if (values.length <= dateIndex || values.length <= amountIndex) continue;

      final dateStr = dateIndex != -1 && dateIndex < values.length ? values[dateIndex] : '';
      final descStr = descIndex != -1 && descIndex < values.length ? values[descIndex] : 'Imported transaction';
      final amountVal = amountIndex != -1 && amountIndex < values.length ? double.tryParse(values[amountIndex]) : null;
      final catStr = catIndex != -1 && catIndex < values.length ? values[catIndex] : 'Other';

      if (dateStr.isNotEmpty && amountVal != null) {
        parsedList.add(
          LedgerTransaction(
            id: 'preview-$index',
            date: dateStr,
            description: descStr,
            amount: amountVal,
            category: catStr.isNotEmpty ? catStr : 'Other',
            status: 'AI-assigned',
            isAnomaly: false,
          ),
        );
        index++;
      }
    }

    return parsedList;
  }
}
