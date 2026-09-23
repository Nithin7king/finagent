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
    { text: 'How much did I spend on food this month?', icon: Sparkles },
    { text: 'What active subscriptions am I paying for?', icon: AlertCircle },
    { text: 'How can I save ₹5,000 next month?', icon: BookOpen },
    { text: 'Give me a summary of my recent expenses', icon: MessageSquare },
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
    const digestText = await getWeeklyDigest();
    await sendChatMessage(`Please summarize my weekly financial health and spending highlights.`);
  };

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col justify-between border border-white/10 bg-ink-raised rounded-2xl overflow-hidden shadow-2xl animate-[fadeIn_0.2s_ease-out]">
      
      {/* Chat header panel */}
      <div className="px-6 py-4 bg-ink/70 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <Sparkles className="w-4.5 h-4.5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">AI Financial Assistant</h3>
            <div className="text-xs text-emerald-400 font-medium flex items-center space-x-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block animate-pulse" />
              <span>Connected to your verified transactions</span>
            </div>
          </div>
        </div>

        {/* Action button to trigger digest */}
        <button
          onClick={triggerDigestAsMessage}
          disabled={isChatLoading}
          className="text-xs border border-white/10 hover:border-blue-500/40 text-mist hover:text-white bg-ink/50 hover:bg-ink py-1.5 px-3.5 rounded-xl transition-all cursor-pointer font-medium"
        >
          Weekly Summary
        </button>
      </div>

      {/* Chat message flow container */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {chatHistory.map((msg) => (
          <ChatBubble key={msg.id} message={msg} />
        ))}

        {/* AI thinking state */}
        {isChatLoading && (
          <div className="flex justify-start mb-4">
            <div className="flex items-start space-x-2.5">
              <div className="w-8 h-8 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shrink-0">
                <Sparkles className="w-4 h-4 animate-spin" />
              </div>
              <div className="py-2.5 px-4 bg-ink border border-white/10 rounded-2xl rounded-tl-sm flex items-center space-x-2">
                <span className="text-xs text-mist">Reviewing your transactions</span>
                <div className="flex items-center space-x-1 pl-1">
                  <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce [animation-delay:300ms]" />
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Bottom controls & input tray */}
      <div className="p-4 bg-ink/70 border-t border-white/10 space-y-3 shrink-0">
        
        {/* Suggested chips above input */}
        {chatHistory.length <= 2 && !isChatLoading && (
          <div className="flex flex-wrap gap-2">
            {suggestedChips.map((chip, idx) => {
              const Icon = chip.icon;
              return (
                <button
                  key={idx}
                  onClick={() => handleChipClick(chip.text)}
                  className="px-3 py-1.5 bg-ink hover:bg-ink-tertiary border border-white/10 hover:border-blue-500/40 text-mist hover:text-white text-xs rounded-xl flex items-center space-x-2 transition-all cursor-pointer"
                >
                  <Icon className="w-3.5 h-3.5 text-blue-400" />
                  <span>{chip.text}</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSend} className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about your expenses, bank statements, savings, or bills..."
            disabled={isChatLoading}
            className="flex-1 bg-ink border border-white/10 text-white py-2.5 px-4 text-sm rounded-xl focus:outline-none focus:border-blue-500 placeholder:text-mist/60"
          />
          <button
            type="submit"
            disabled={!input.trim() || isChatLoading}
            className={`p-2.5 rounded-xl flex items-center justify-center transition-all cursor-pointer ${
              input.trim() && !isChatLoading
                ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-600/25'
                : 'bg-white/5 text-mist/40 cursor-not-allowed'
            }`}
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
