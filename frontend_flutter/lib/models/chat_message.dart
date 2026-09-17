class ChatTurn {
  final String id;
  final String sender; // 'user' or 'agent'
  final String text;
  final DateTime timestamp;
  final List<String> toolCalls;

  ChatTurn({
    required this.id,
    required this.sender,
    required this.text,
    required this.timestamp,
    this.toolCalls = const [],
  });

  bool get isUser => sender == 'user';
}
