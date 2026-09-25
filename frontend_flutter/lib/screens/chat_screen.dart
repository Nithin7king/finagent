import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../config/app_theme.dart';
import '../providers/fin_provider.dart';
import '../widgets/chat_bubble.dart';
import '../widgets/passbook_app_bar.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({Key? key}) : super(key: key);

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _textController = TextEditingController();
  final _scrollController = ScrollController();

  final List<String> _suggestedChips = [
    'What active subscriptions am I paying for?',
    'How much did I spend on food this month?',
    'How can I save ₹5,000 next month?',
    'Give me a summary of my recent expenses',
  ];

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _handleSend(FinProvider fin) async {
    final text = _textController.text.trim();
    if (text.isEmpty || fin.isChatLoading) return;

    _textController.clear();
    await fin.sendChatMessage(text);
    _scrollToBottom();
  }

  Future<void> _handleChipClick(FinProvider fin, String chip) async {
    if (fin.isChatLoading) return;
    await fin.sendChatMessage(chip);
    _scrollToBottom();
  }

  @override
  Widget build(BuildContext context) {
    final fin = context.watch<FinProvider>();
    final history = fin.chatHistory;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: const PassbookAppBar(title: 'AI Financial Advisor'),
      body: Column(
        children: [
          // Chat Messages
          Expanded(
            child: history.isEmpty
                ? Center(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: AppColors.primary.withOpacity(0.12),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.auto_awesome, size: 40, color: AppColors.primary),
                          ),
                          const SizedBox(height: 16),
                          const Text(
                            'Ask Your Personal AI Advisor',
                            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            'Powered by LangGraph multi-agent financial intelligence and IsolationForest models.',
                            textAlign: TextAlign.center,
                            style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                          ),
                          const SizedBox(height: 24),
                          const Align(
                            alignment: Alignment.centerLeft,
                            child: Text(
                              'Suggested Questions:',
                              style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textMuted),
                            ),
                          ),
                          const SizedBox(height: 10),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: _suggestedChips.map((chip) {
                              return ActionChip(
                                label: Text(chip),
                                labelStyle: const TextStyle(fontSize: 11.5, color: AppColors.textPrimary),
                                backgroundColor: AppColors.cardSurface,
                                side: const BorderSide(color: AppColors.border),
                                onPressed: () => _handleChipClick(fin, chip),
                              );
                            }).toList(),
                          ),
                        ],
                      ),
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    itemCount: history.length,
                    itemBuilder: (ctx, i) {
                      return ChatBubble(message: history[i]);
                    },
                  ),
          ),

          // Loading indicator
          if (fin.isChatLoading) ...[
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: AppColors.cardSurfaceRaised,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
                        ),
                        SizedBox(width: 8),
                        Text(
                          'Reasoning across accounts & knowledge base...',
                          style: TextStyle(fontSize: 11, color: AppColors.textSecondary),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],

          // Quick Chips (when chat is active)
          if (history.isNotEmpty)
            SizedBox(
              height: 38,
              child: ListView.separated(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                scrollDirection: Axis.horizontal,
                itemCount: _suggestedChips.length,
                separatorBuilder: (_, __) => const SizedBox(width: 8),
                itemBuilder: (ctx, i) {
                  return ActionChip(
                    label: Text(_suggestedChips[i]),
                    labelStyle: const TextStyle(fontSize: 10.5, color: AppColors.textSecondary),
                    backgroundColor: AppColors.cardSurface,
                    side: const BorderSide(color: AppColors.border),
                    onPressed: () => _handleChipClick(fin, _suggestedChips[i]),
                  );
                },
              ),
            ),
          const SizedBox(height: 6),

          // Text Input Bar
          Container(
            padding: const EdgeInsets.all(12),
            decoration: const BoxDecoration(
              color: AppColors.backgroundSecondary,
              border: Border(top: BorderSide(color: AppColors.border)),
            ),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _textController,
                      textInputAction: TextInputAction.send,
                      onSubmitted: (_) => _handleSend(fin),
                      decoration: InputDecoration(
                        hintText: 'Ask about spending, taxes, SIPs, or bills...',
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(24),
                          borderSide: BorderSide.none,
                        ),
                        filled: true,
                        fillColor: AppColors.cardSurface,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  InkWell(
                    onTap: fin.isChatLoading ? null : () => _handleSend(fin),
                    borderRadius: BorderRadius.circular(24),
                    child: Container(
                      padding: const EdgeInsets.all(12),
                      decoration: const BoxDecoration(
                        color: AppColors.primary,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.send_rounded, size: 18, color: Colors.white),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
