/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';

interface StatCardProps {
  id: string;
  title: string;
  value: number;
  format: 'currency' | 'percentage' | 'integer';
  trend?: {
    type: 'positive' | 'negative' | 'neutral';
    label: string;
  };
}

export const StatCard: React.FC<StatCardProps> = ({ id, title, value, format, trend }) => {
  const [displayValue, setDisplayValue] = useState(0);

  // Counter animation
  useEffect(() => {
    let start = 0;
    const end = value;
    if (end === 0) {
      setDisplayValue(0);
      return;
    }
    
    const duration = 600; // ms
    const increment = end / (duration / 16); // ~60fps
    let current = start;

    const timer = setInterval(() => {
      current += increment;
      if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
        clearInterval(timer);
        setDisplayValue(end);
      } else {
        setDisplayValue(Math.floor(current));
      }
    }, 16);

    return () => clearInterval(timer);
  }, [value]);

  const formatValue = (val: number) => {
    if (format === 'currency') {
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0,
      }).format(val);
    } else if (format === 'percentage') {
      return `${val}%`;
    } else {
      return val.toString();
    }
  };

  return (
    <div 
      id={id}
      className="bg-ink-raised border border-gold/10 rounded-sm p-6 flex flex-col justify-between hover:border-gold/30 transition-all duration-300"
    >
      <div className="text-[10px] uppercase font-mono tracking-widest text-mist">
        {title}
      </div>
      <div className="mt-4 flex items-baseline justify-between">
        <span className="text-2xl font-mono font-bold text-white tabular-nums tracking-tight">
          {formatValue(displayValue)}
        </span>
        
        {trend && (
          <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-sm flex items-center space-x-1 border ${
            trend.type === 'positive' 
              ? 'text-sage bg-sage/5 border-sage/20' 
              : trend.type === 'negative' 
                ? 'text-coral bg-coral/5 border-coral/20' 
                : 'text-gold bg-gold/5 border-gold/20'
          }`}>
            <span>{trend.type === 'positive' ? '▲' : trend.type === 'negative' ? '▼' : '●'}</span>
            <span className="tabular-nums">{trend.label}</span>
          </span>
        )}
      </div>
    </div>
  );
};
