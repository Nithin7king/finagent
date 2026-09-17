/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useRef, useEffect } from 'react';
import { useFin } from '../FinContext';
import { ChatBubble } from './ChatBubble';
import { Send, Sparkles, BookOpen, MessageSquare, AlertCircle, RefreshCw } from 'lucide-react';

export const ChatPage: React.FC = () => {
  const { chatHistory, sendChatMessage, isChatLoading, getWeeklyDigest } = useFin();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedChips = [
    { text: 'Explain my tax-saving options.', icon: BookOpen },
    { text: 'Am I on track for my goals?', icon: Sparkles },
    { text: 'Auditing swiggy & billing anomalies', icon: AlertCircle },
  ];

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, isChatLoading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || isChatLoading) return;
    
    setInput('');
    await sendChatMessage(text);
  };

  const handleChipClick = async (text: string) => {
    if (isChatLoading) return;
    await sendChatMessage(text);
  };

  const triggerDigestAsMessage = async () => {
    if (isChatLoading) return;
    // Call digest endpoint and display as an agent answer
    const digestText = await getWeeklyDigest();
    // Simulate sending it to chat
    await sendChatMessage(`Autonomous Ledger Audit: Generate Weekly Digest`);
  };

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col justify-between border border-gold/10 bg-ink-raised rounded-sm overflow-hidden shadow-2xl animate-[fadeIn_0.2s_ease-out]">
      
      {/* Chat header panel */}
      <div className="px-6 py-4.5 bg-ink border-b border-gold/10 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gold/5 border border-gold/20 flex items-center justify-center rounded-sm text-gold">
            <MessageSquare className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-display text-sm font-medium text-white">Autonomous Financial Agent</h3>
            <div className="text-[9px] font-mono text-sage font-semibold uppercase tracking-wider flex items-center space-x-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-sage inline-block animate-pulse" />
              <span>Grounded in passbook ledger (Real-Time RAG)</span>
            </div>
          </div>
        </div>

        {/* Action button to trigger Autonomous digest */}
        <button
          onClick={triggerDigestAsMessage}
          disabled={isChatLoading}
          className="text-[10px] font-mono border border-gold/15 hover:border-gold/50 text-gold bg-gold/5 hover:bg-gold/10 py-1.5 px-3.5 rounded-sm transition-all cursor-pointer font-bold select-none uppercase tracking-wide"
        >
          Dispatch Weekly Digest
        </button>
      </div>

      {/* Chat message flow container */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {chatHistory.map((msg) => (
          <ChatBubble key={msg.id} message={msg} />
        ))}

        {/* AI thinking state representation */}
        {isChatLoading && (
          <div className="flex justify-start mb-5 animate-pulse">
            <div className="flex items-start space-x-3">
              <div className="w-7 h-7 bg-gold/10 border border-gold/30 flex items-center justify-center rounded-sm shrink-0">
                <Sparkles className="w-4 h-4 text-gold animate-spin" />
              </div>
              <div className="p-4 bg-ink border border-gold/5 rounded-sm flex items-center space-x-2">
                <span className="text-xs font-mono text-gold/80 italic">MYFY.AI is auditing ledger parameters</span>
                <div className="flex items-center space-x-1 pl-1">
                  <span className="w-1.5 h-1.5 bg-gold rounded-full animate-[bounce_1s_infinite_100ms]" />
                  <span className="w-1.5 h-1.5 bg-gold rounded-full animate-[bounce_1s_infinite_200ms]" />
                  <span className="w-1.5 h-1.5 bg-gold rounded-full animate-[bounce_1s_infinite_300ms]" />
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Bottom controls & input tray */}
      <div className="p-4 bg-ink border-t border-gold/10 space-y-4 shrink-0">
        
        {/* Suggested chips above input */}
        {chatHistory.length <= 1 && !isChatLoading && (
          <div className="flex flex-wrap gap-2.5">
            {suggestedChips.map((chip, idx) => {
              const Icon = chip.icon;
              return (
                <button
                  key={idx}
                  onClick={() => handleChipClick(chip.text)}
                  className="px-3.5 py-1.5 bg-ink-raised border border-gold/15 hover:border-gold/50 text-mist hover:text-gold text-[10px] font-mono flex items-center space-x-2 transition-all rounded-sm cursor-pointer"
                >
                  <Icon className="w-3.5 h-3.5 text-gold/60" />
                  <span>{chip.text}</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSend} className="flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Query tax exemptions, forecast summaries, subscription dispute logs..."
            disabled={isChatLoading}
            className="flex-1 bg-ink-raised border border-gold/15 text-white py-3 px-4 text-xs font-mono rounded-sm focus:border-gold focus:ring-1 focus:ring-gold placeholder:text-mist/35 outline-none"
          />
          <button
            type="submit"
            disabled={!input.trim() || isChatLoading}
            className={`p-3 rounded-sm flex items-center justify-center transition-all cursor-pointer ${
              input.trim() && !isChatLoading
                ? 'bg-gold text-ink font-bold hover:brightness-110'
                : 'bg-gold/10 border border-gold/10 text-mist/30 cursor-not-allowed'
            }`}
          >
            <Send className="w-4.5 h-4.5" />
          </button>
        </form>
      </div>
    </div>
  );
};
