import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/fin_provider.dart';
import '../theme/fin_theme.dart';
import '../widgets/chat_bubble.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _inputCtrl = TextEditingController();
  final _scrollCtrl = ScrollController();

  final suggestedPrompts = [
    'Explain my tax-saving options under Section 80C vs New Regime.',
    'Am I on track for my emergency fund goal?',
    'Audit my spending anomalies this month.',
  ];

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _handleSend([String? textToSend]) {
    final text = textToSend ?? _inputCtrl.text.trim();
    if (text.isEmpty) return;

    _inputCtrl.clear();
    context.read<FinProvider>().sendChatMessage(text);
    _scrollToBottom();
  }

  void _triggerWeeklyDigest() async {
    final fin = context.read<FinProvider>();
    _handleSend('Autonomous Ledger Audit: Generate Weekly Digest');
  }

  @override
  Widget build(BuildContext context) {
    final fin = context.watch<FinProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Center(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 1000),
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        decoration: BoxDecoration(
          color: isDark ? FinColors.darkInkRaised : FinColors.lightInkRaised,
          borderRadius: BorderRadius.circular(4),
          border: Border.all(
            color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.18),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.15),
              blurRadius: 16,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          children: [
            // Chat Header
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
              decoration: BoxDecoration(
                color: isDark ? FinColors.darkInk : FinColors.lightInk,
                border: Border(
                  bottom: BorderSide(
                    color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.15),
                  ),
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.1),
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(
                            color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.3),
                          ),
                        ),
                        child: Icon(
                          Icons.chat_bubble_outline,
                          size: 16,
                          color: isDark ? FinColors.darkGold : FinColors.lightGold,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Autonomous Financial Agent',
                            style: GoogleFonts.fraunces(
                              fontSize: 15,
                              fontWeight: FontWeight.w600,
                              color: isDark ? Colors.white : FinColors.lightInkText,
                            ),
                          ),
                          Row(
                            children: [
                              Container(
                                width: 6,
                                height: 6,
                                decoration: BoxDecoration(
                                  color: isDark ? FinColors.darkSage : FinColors.lightSage,
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 6),
                              Text(
                                'GROUNDED IN LEDGER (REAL-TIME RAG)',
                                style: GoogleFonts.ibmPlexMono(
                                  fontSize: 8,
                                  fontWeight: FontWeight.bold,
                                  letterSpacing: 1,
                                  color: isDark ? FinColors.darkSage : FinColors.lightSage,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ],
                  ),
                  OutlinedButton.icon(
                    onPressed: fin.isChatLoading ? null : _triggerWeeklyDigest,
                    icon: const Icon(Icons.bolt, size: 14),
                    label: Text(
                      'WEEKLY DIGEST',
                      style: GoogleFonts.ibmPlexMono(fontSize: 10, fontWeight: FontWeight.bold),
                    ),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: isDark ? FinColors.darkGold : FinColors.lightGold,
                      side: BorderSide(
                        color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.3),
                      ),
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(2)),
                    ),
                  ),
                ],
              ),
            ),

            // Message History
            Expanded(
              child: fin.chatHistory.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.auto_awesome_outlined,
                            size: 36,
                            color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.5),
                          ),
                          const SizedBox(height: 12),
                          Text(
                            'How can MYFY.AI assist your financial planning today?',
                            style: GoogleFonts.fraunces(
                              fontSize: 16,
                              fontStyle: FontStyle.italic,
                              color: isDark ? Colors.white70 : FinColors.lightInkText,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            'Ask about tax optimization, goal feasibility, or spending anomalies.',
                            style: GoogleFonts.inter(
                              fontSize: 12,
                              color: isDark ? FinColors.darkMist : FinColors.lightMist,
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView.builder(
                      controller: _scrollCtrl,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      itemCount: fin.chatHistory.length,
                      itemBuilder: (context, idx) {
                        return ChatBubble(turn: fin.chatHistory[idx]);
                      },
                    ),
            ),

            // Agent typing indicator
            if (fin.isChatLoading)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                child: Row(
                  children: [
                    SizedBox(
                      width: 14,
                      height: 14,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: isDark ? FinColors.darkGold : FinColors.lightGold,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Text(
                      'MYFY.AI multi-agent reasoning in progress...',
                      style: GoogleFonts.ibmPlexMono(
                        fontSize: 11,
                        color: isDark ? FinColors.darkMist : FinColors.lightMist,
                      ),
                    ),
                  ],
                ),
              ),

            // Prompt suggestions
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: suggestedPrompts.map((p) {
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ActionChip(
                        label: Text(p),
                        labelStyle: GoogleFonts.inter(fontSize: 11),
                        avatar: Icon(Icons.arrow_forward_ios, size: 10),
                        onPressed: fin.isChatLoading ? null : () => _handleSend(p),
                      ),
                    );
                  }).toList(),
                ),
              ),
            ),

            // Input Bar
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: isDark ? FinColors.darkInk : FinColors.lightInk,
                border: Border(
                  top: BorderSide(
                    color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.15),
                  ),
                ),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _inputCtrl,
                      style: GoogleFonts.inter(fontSize: 13),
                      decoration: InputDecoration(
                        hintText: 'Ask MYFY.AI about your expenses, budgeting, or taxes...',
                        hintStyle: GoogleFonts.inter(
                          fontSize: 13,
                          color: isDark ? FinColors.darkMist : FinColors.lightMist,
                        ),
                        border: InputBorder.none,
                      ),
                      onSubmitted: (_) => _handleSend(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    icon: Icon(
                      Icons.send_rounded,
                      color: isDark ? FinColors.darkGold : FinColors.lightGold,
                    ),
                    onPressed: fin.isChatLoading ? null : () => _handleSend(),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
