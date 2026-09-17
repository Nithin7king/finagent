import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import '../models/chat_message.dart';
import '../theme/fin_theme.dart';
import 'stamp_badge.dart';

class ChatBubble extends StatelessWidget {
  final ChatTurn turn;

  const ChatBubble({super.key, required this.turn});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final timeStr = DateFormat('hh:mm a').format(turn.timestamp);

    if (turn.isUser) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.end,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              timeStr,
              style: GoogleFonts.ibmPlexMono(
                fontSize: 9,
                color: isDark ? FinColors.darkMist : FinColors.lightMist,
              ),
            ),
            const SizedBox(width: 8),
            Flexible(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.12),
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(8),
                    topRight: Radius.circular(8),
                    bottomLeft: Radius.circular(8),
                  ),
                  border: Border.all(
                    color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.3),
                  ),
                ),
                child: Text(
                  turn.text,
                  style: GoogleFonts.inter(
                    fontSize: 13,
                    color: isDark ? Colors.white : FinColors.lightInkText,
                    height: 1.4,
                  ),
                ),
              ),
            ),
          ],
        ),
      );
    }

    // Agent Turn
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.1),
              borderRadius: BorderRadius.circular(4),
              border: Border.all(
                color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.3),
              ),
            ),
            child: Center(
              child: Text(
                '💎',
                style: const TextStyle(fontSize: 14),
              ),
            ),
          ),
          const SizedBox(width: 10),
          Flexible(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'MYFY.AI AGENT',
                      style: GoogleFonts.ibmPlexMono(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 1.2,
                        color: isDark ? FinColors.darkGold : FinColors.lightGold,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      timeStr,
                      style: GoogleFonts.ibmPlexMono(
                        fontSize: 9,
                        color: isDark ? FinColors.darkMist : FinColors.lightMist,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                  decoration: BoxDecoration(
                    color: isDark ? FinColors.darkInkRaised : FinColors.lightInkRaised,
                    borderRadius: const BorderRadius.only(
                      topLeft: Radius.circular(2),
                      topRight: Radius.circular(8),
                      bottomRight: Radius.circular(8),
                      bottomLeft: Radius.circular(8),
                    ),
                    border: Border.all(
                      color: (isDark ? FinColors.darkGold : FinColors.lightGold).withOpacity(0.18),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        turn.text,
                        style: GoogleFonts.inter(
                          fontSize: 13,
                          color: isDark ? Colors.white.withOpacity(0.9) : FinColors.lightInkText,
                          height: 1.5,
                        ),
                      ),
                      if (turn.toolCalls.isNotEmpty) ...[
                        const SizedBox(height: 10),
                        Wrap(
                          spacing: 6,
                          runSpacing: 4,
                          children: turn.toolCalls.map((tc) {
                            return StampBadge(
                              text: '🔧 $tc',
                              type: StampType.neutral,
                            );
                          }).toList(),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
