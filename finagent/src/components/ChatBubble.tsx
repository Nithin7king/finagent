/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { ChatMessage } from '../types';
import { ChevronDown, ChevronUp, Bot, User, CheckCircle2 } from 'lucide-react';

interface ChatBubbleProps {
  message: ChatMessage;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message }) => {
  const isAgent = message.sender === 'agent';
  const [showReasoning, setShowReasoning] = useState(false);

  // Elegant helper to render basic markdown elements (bold, lists, tables) safely
  const formatText = (txt: string) => {
    const lines = txt.split('\n');
    let inList = false;
    let inTable = false;
    let tableRows: string[][] = [];

    const elements: React.ReactNode[] = [];

    const parseInlineBold = (input: string): React.ReactNode[] => {
      const parts = input.split('**');
      return parts.map((part, index) => {
        if (index % 2 === 1) {
          return <strong key={index} className="text-gold font-bold">{part}</strong>;
        }
        return part;
      });
    };

    lines.forEach((line, index) => {
      const trimmed = line.trim();

      // Table handling
      if (trimmed.startsWith('|')) {
        inTable = true;
        // Ignore header separator row e.g. |:---|
        if (trimmed.includes('---')) return;
        
        const cols = trimmed.split('|').map(c => c.trim()).filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);
        tableRows.push(cols);
        return;
      } else if (inTable) {
        // End of table, compile it
        inTable = false;
        elements.push(
          <div key={`table-${index}`} className="my-3 overflow-x-auto border border-gold/15 rounded-sm">
            <table className="w-full text-left border-collapse text-xs font-mono bg-ink/40">
              <thead>
                <tr className="border-b border-gold/15 bg-gold/5 text-gold font-semibold">
                  {tableRows[0].map((col, idx) => (
                    <th key={idx} className="py-2 px-3">{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tableRows.slice(1).map((row, rowIdx) => (
                  <tr key={rowIdx} className="border-b border-gold/5 hover:bg-gold/5">
                    {row.map((col, colIdx) => (
                      <td key={colIdx} className="py-2 px-3 text-white/95 tabular-nums">{col}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        tableRows = [];
      }

      // Bullet List Handling
      if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
        const itemText = trimmed.substring(2);
        if (!inList) {
          inList = true;
        }
        elements.push(
          <li key={`li-${index}`} className="list-disc ml-5 text-sm text-mist/95 mb-1 leading-relaxed">
            {parseInlineBold(itemText)}
          </li>
        );
        return;
      } else if (inList && !trimmed.startsWith('* ') && !trimmed.startsWith('- ') && trimmed !== '') {
        inList = false;
      }

      // Standard Paragraph
      if (trimmed === '') {
        elements.push(<div key={`spacer-${index}`} className="h-2.5" />);
      } else {
        elements.push(
          <p key={`p-${index}`} className="text-sm text-mist/95 leading-relaxed mb-1.5">
            {parseInlineBold(trimmed)}
          </p>
        );
      }
    });

    // Cleanup remaining table if any
    if (inTable && tableRows.length > 0) {
      elements.push(
        <div key="table-end" className="my-3 overflow-x-auto border border-gold/15 rounded-sm">
          <table className="w-full text-left border-collapse text-xs font-mono bg-ink/40">
            <thead>
              <tr className="border-b border-gold/15 bg-gold/5 text-gold font-semibold">
                {tableRows[0].map((col, idx) => (
                  <th key={idx} className="py-2 px-3">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableRows.slice(1).map((row, rowIdx) => (
                <tr key={rowIdx} className="border-b border-gold/5 hover:bg-gold/5">
                  {row.map((col, colIdx) => (
                    <td key={colIdx} className="py-2 px-3 text-white/95 tabular-nums">{col}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    return elements;
  };

  return (
    <div className={`flex w-full ${isAgent ? 'justify-start' : 'justify-end'} mb-5 animate-[fadeIn_0.15s_ease-out]`}>
      <div className={`max-w-[85%] md:max-w-[70%] flex items-start space-x-3`}>
        {isAgent && (
          <div className="w-7 h-7 bg-gold/10 border border-gold/30 flex items-center justify-center rounded-sm shrink-0">
            <Bot className="w-4 h-4 text-gold" />
          </div>
        )}

        <div className="flex flex-col space-y-1.5">
          {/* Tool Calls Expansion strip (collapsible reasoning) */}
          {isAgent && message.toolCalls && message.toolCalls.length > 0 && (
            <div className="bg-ink border border-gold/10 p-2 rounded-sm text-[10px] font-mono text-gold/80 select-none">
              <button 
                onClick={() => setShowReasoning(!showReasoning)}
                className="flex items-center justify-between w-full font-medium cursor-pointer hover:text-white transition-colors"
              >
                <div className="flex items-center space-x-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-sage" />
                  <span>Verified {message.toolCalls.length} Agent Tasks</span>
                </div>
                {showReasoning ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
              
              {showReasoning && (
                <div className="mt-1.5 pt-1.5 border-t border-gold/5 space-y-1 text-mist/85 font-sans pl-5 list-decimal list-inside">
                  {message.toolCalls.map((t, idx) => (
                    <div key={idx} className="flex items-center space-x-1.5 text-[9px]">
                      <span className="text-gold">✔</span>
                      <span>{t}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Core Bubble Content */}
          <div 
            className={`p-4.5 rounded-sm ${
              isAgent 
                ? 'bg-ink-raised border border-gold/10 text-white' 
                : 'bg-gold/5 border border-gold/20 text-white'
            }`}
          >
            {formatText(message.text)}
          </div>

          {/* Message Timestamp */}
          <span className="text-[9px] font-mono text-mist/40 px-1 self-start select-none">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        {!isAgent && (
          <div className="w-7 h-7 bg-gold/10 border border-gold/20 flex items-center justify-center rounded-sm shrink-0">
            <User className="w-4 h-4 text-gold" />
          </div>
        )}
      </div>
    </div>
  );
};
