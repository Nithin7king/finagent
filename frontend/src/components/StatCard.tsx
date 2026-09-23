import React, { useState, useEffect } from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  id: string;
  title: string;
  value: number;
  format: 'currency' | 'percentage' | 'integer';
  subtitle?: string;
  icon?: LucideIcon;
  colorScheme?: 'blue' | 'indigo' | 'emerald' | 'rose' | 'amber';
  trend?: {
    type: 'positive' | 'negative' | 'neutral';
    label: string;
  };
}

export const StatCard: React.FC<StatCardProps> = ({ 
  id, 
  title, 
  value, 
  format, 
  subtitle,
  icon: Icon,
  colorScheme = 'blue',
  trend 
}) => {
  const [displayValue, setDisplayValue] = useState(0);

  // Counter animation
  useEffect(() => {
    let start = 0;
    const end = value;
    if (end === 0) {
      setDisplayValue(0);
      return;
    }
    
    const duration = 500; // ms
    const increment = end / (duration / 16);
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

  const iconColors = {
    blue: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    indigo: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    rose: 'text-rose-400 bg-rose-500/10 border-rose-500/20',
    amber: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  };

  return (
    <div 
      id={id}
      className="bg-ink-raised border border-white/10 rounded-2xl p-5 flex flex-col justify-between hover:border-white/20 transition-all duration-200 shadow-lg shadow-black/20"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-mist">
          {title}
        </span>
        {Icon && (
          <div className={`w-8 h-8 rounded-xl border flex items-center justify-center ${iconColors[colorScheme]}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="mt-4">
        <div className="text-2xl font-bold text-white tracking-tight tabular-nums">
          {formatValue(displayValue)}
        </div>
        
        <div className="mt-2 flex items-center justify-between text-xs">
          {subtitle && (
            <span className="text-mist text-[11px] truncate">
              {subtitle}
            </span>
          )}

          {trend && (
            <span className={`inline-flex items-center gap-1 font-medium px-2 py-0.5 rounded-full text-[11px] ${
              trend.type === 'positive' 
                ? 'text-emerald-400 bg-emerald-500/10' 
                : trend.type === 'negative' 
                  ? 'text-rose-400 bg-rose-500/10' 
                  : 'text-amber-400 bg-amber-500/10'
            }`}>
              <span>{trend.type === 'positive' ? '↑' : trend.type === 'negative' ? '↓' : '•'}</span>
              <span>{trend.label}</span>
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
