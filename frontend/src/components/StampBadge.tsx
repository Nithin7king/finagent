/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useRef, useEffect } from 'react';
import { useFin } from '../FinContext';
import { Category } from '../types';
import { Edit2, Check } from 'lucide-react';

interface StampBadgeProps {
  id: string; // transaction ID
  category: Category;
  isAnomaly: boolean;
  status: 'AI-assigned' | 'user-corrected';
  interactive?: boolean;
}

const CATEGORIES: Category[] = [
  'Salary', 'Investment', 'Housing', 'Food', 'Utilities', 'Transport', 'Shopping', 'Entertainment', 'Others'
];

export const StampBadge: React.FC<StampBadgeProps> = ({ id, category, isAnomaly, status, interactive = true }) => {
  const { correctCategory } = useFin();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleSelect = async (cat: Category) => {
    await correctCategory(id, cat);
    setIsOpen(false);
  };

  // Base stamp classes
  const stampBaseClasses = isAnomaly ? 'coral-stamp' : 'gold-stamp';
  
  // Animation on mount for anomalies
  const animationPulse = isAnomaly 
    ? 'animate-[pulse_1.5s_cubic-bezier(0.4,0,0.6,1)_1]' 
    : '';

  return (
    <div ref={containerRef} className="relative inline-block text-left">
      <button
        onClick={() => interactive && setIsOpen(!isOpen)}
        disabled={!interactive}
        className={`${stampBaseClasses} ${animationPulse} ${
          interactive ? 'hover:brightness-125 focus:ring-1 focus:ring-gold border cursor-pointer' : ''
        } flex items-center space-x-1 font-mono transition-all duration-200`}
      >
        <span>{category}</span>
        {status === 'user-corrected' && (
          <Check className="w-2.5 h-2.5 text-sage ml-1 stroke-[3]" />
        )}
        {status === 'AI-assigned' && interactive && (
          <span className="w-1 h-1 rounded-full bg-gold/50 ml-1 inline-block animate-pulse" />
        )}
      </button>

      {/* Category Adjustment Popover */}
      {isOpen && (
        <div className="absolute left-0 mt-1 w-44 bg-ink border border-gold/30 rounded-sm shadow-2xl z-50 py-1.5 focus:outline-none">
          <div className="px-2.5 py-1 text-[9px] font-mono uppercase tracking-wider text-mist border-b border-gold/10 mb-1 flex items-center justify-between">
            <span>Re-Index Category</span>
            <Edit2 className="w-2.5 h-2.5 text-gold/60" />
          </div>
          {CATEGORIES.map((cat) => {
            const isSelected = cat === category;
            return (
              <button
                key={cat}
                onClick={() => handleSelect(cat)}
                className={`w-full text-left px-3 py-1.5 text-xs font-mono flex items-center justify-between transition-colors ${
                  isSelected 
                    ? 'text-gold bg-gold/10 font-semibold' 
                    : 'text-mist hover:text-white hover:bg-gold/5'
                }`}
              >
                <span>{cat}</span>
                {isSelected && <Check className="w-3 h-3 text-gold" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
