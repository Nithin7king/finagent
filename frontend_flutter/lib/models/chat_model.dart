class ChatMessage {
  final String id;
  final String sender; // 'user' | 'agent'
  final String text;
  final String timestamp;
  final List<String> toolCalls;
  final List<String> sources;

  ChatMessage({
    required this.id,
    required this.sender,
    required this.text,
    required this.timestamp,
    this.toolCalls = const [],
    this.sources = const [],
  });

  bool get isUser => sender == 'user';

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: json['id']?.toString() ?? DateTime.now().millisecondsSinceEpoch.toString(),
      sender: json['sender'] ?? (json['role'] == 'user' ? 'user' : 'agent'),
      text: json['text'] ?? json['content'] ?? json['response'] ?? '',
      timestamp: json['timestamp'] ?? DateTime.now().toIso8601String(),
      toolCalls: (json['toolCalls'] as List<dynamic>?)?.map((e) => e.toString()).toList() ??
                 (json['tool_calls_made'] as List<dynamic>?)?.map((e) => e.toString()).toList() ??
                 const [],
      sources: (json['sources'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? const [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'sender': sender,
      'text': text,
      'timestamp': timestamp,
      'toolCalls': toolCalls,
      'sources': sources,
    };
  }
}
