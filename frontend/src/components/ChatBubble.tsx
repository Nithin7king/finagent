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

  // Helper to render basic markdown elements (bold, lists, tables) safely
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
          return <strong key={index} className="font-semibold text-white">{part}</strong>;
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
          <div key={`table-${index}`} className="my-3 overflow-x-auto border border-white/10 rounded-xl">
            <table className="w-full text-left border-collapse text-xs bg-slate-950/60">
              <thead>
                <tr className="border-b border-white/10 bg-white/5 text-slate-300 font-semibold">
                  {tableRows[0].map((col, idx) => (
                    <th key={idx} className="py-2.5 px-3.5">{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {tableRows.slice(1).map((row, rowIdx) => (
                  <tr key={rowIdx} className="hover:bg-white/[0.02]">
                    {row.map((col, colIdx) => (
                      <td key={colIdx} className="py-2 px-3.5 text-slate-200">{col}</td>
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
          <li key={`li-${index}`} className="list-disc ml-5 text-sm text-slate-200 mb-1 leading-relaxed">
            {parseInlineBold(itemText)}
          </li>
        );
        return;
      } else if (inList && !trimmed.startsWith('* ') && !trimmed.startsWith('- ') && trimmed !== '') {
        inList = false;
      }

      // Standard Paragraph
      if (trimmed === '') {
        elements.push(<div key={`spacer-${index}`} className="h-2" />);
      } else {
        elements.push(
          <p key={`p-${index}`} className="text-sm leading-relaxed mb-1 text-slate-200">
            {parseInlineBold(trimmed)}
          </p>
        );
      }
    });

    // Cleanup remaining table if any
    if (inTable && tableRows.length > 0) {
      elements.push(
        <div key="table-end" className="my-3 overflow-x-auto border border-white/10 rounded-xl">
          <table className="w-full text-left border-collapse text-xs bg-slate-950/60">
            <thead>
              <tr className="border-b border-white/10 bg-white/5 text-slate-300 font-semibold">
                {tableRows[0].map((col, idx) => (
                  <th key={idx} className="py-2.5 px-3.5">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {tableRows.slice(1).map((row, rowIdx) => (
                <tr key={rowIdx} className="hover:bg-white/[0.02]">
                  {row.map((col, colIdx) => (
                    <td key={colIdx} className="py-2 px-3.5 text-slate-200">{col}</td>
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
    <div className={`flex w-full ${isAgent ? 'justify-start' : 'justify-end'} mb-4 animate-[fadeIn_0.15s_ease-out]`}>
      <div className={`max-w-[88%] md:max-w-[75%] flex items-start space-x-2.5 ${!isAgent ? 'flex-row-reverse space-x-reverse' : ''}`}>
        
        {/* Avatar */}
        {isAgent ? (
          <div className="w-8 h-8 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shrink-0 mt-0.5">
            <Bot className="w-4 h-4" />
          </div>
        ) : (
          <div className="w-8 h-8 rounded-xl bg-ink-tertiary border border-white/10 flex items-center justify-center text-mist shrink-0 mt-0.5">
            <User className="w-4 h-4" />
          </div>
        )}

        <div className="flex flex-col space-y-1.5 flex-1 min-w-0">
          
          {/* Tool Calls Expansion strip (collapsible reasoning) */}
          {isAgent && message.toolCalls && message.toolCalls.length > 0 && (
            <div className="bg-ink border border-white/10 p-2.5 rounded-xl text-xs text-mist select-none">
              <button 
                onClick={() => setShowReasoning(!showReasoning)}
                className="flex items-center justify-between w-full font-medium cursor-pointer hover:text-white transition-colors"
              >
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Checked {message.toolCalls.length} account source{message.toolCalls.length > 1 ? 's' : ''}</span>
                </div>
                {showReasoning ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>
              
              {showReasoning && (
                <div className="mt-2 pt-2 border-t border-white/5 space-y-1 text-mist text-xs">
                  {message.toolCalls.map((t, idx) => (
                    <div key={idx} className="flex items-center space-x-2">
                      <span className="text-emerald-400">✓</span>
                      <span>{t}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Core Bubble Content */}
          <div 
            className={`p-4 rounded-2xl text-sm ${
              isAgent 
                ? 'bg-ink border border-white/10 text-white rounded-tl-sm shadow-sm' 
                : 'bg-blue-600 text-white rounded-tr-sm shadow-md shadow-blue-600/20'
            }`}
          >
            {formatText(message.text)}
          </div>

          {/* Timestamp */}
          <span className={`text-[10px] text-slate-500 px-1 select-none ${!isAgent ? 'text-right' : 'text-left'}`}>
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    </div>
  );
};
