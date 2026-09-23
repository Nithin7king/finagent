import React, { useState, useRef, useEffect } from 'react';
import { useFin } from '../FinContext';
import { Category } from '../types';
import { 
  Check, 
  ChevronDown, 
  Utensils, 
  ShoppingBag, 
  Briefcase, 
  Zap, 
  Car, 
  Home, 
  TrendingUp, 
  Film, 
  Tag, 
  AlertCircle 
} from 'lucide-react';

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

const categoryMeta: Record<Category, { bg: string; text: string; border: string; icon: React.FC<{ className?: string }> }> = {
  Salary: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', icon: Briefcase },
  Investment: { bg: 'bg-teal-500/10', text: 'text-teal-400', border: 'border-teal-500/20', icon: TrendingUp },
  Housing: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20', icon: Home },
  Food: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20', icon: Utensils },
  Utilities: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20', icon: Zap },
  Transport: { bg: 'bg-cyan-500/10', text: 'text-cyan-400', border: 'border-cyan-500/20', icon: Car },
  Shopping: { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/20', icon: ShoppingBag },
  Entertainment: { bg: 'bg-pink-500/10', text: 'text-pink-400', border: 'border-pink-500/20', icon: Film },
  Others: { bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-slate-500/20', icon: Tag },
};

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

  const currentMeta = categoryMeta[category] || categoryMeta.Others;
  const CategoryIcon = currentMeta.icon;

  return (
    <div ref={containerRef} className="relative inline-flex items-center gap-1.5 text-left">
      <button
        onClick={() => interactive && setIsOpen(!isOpen)}
        disabled={!interactive}
        title={interactive ? 'Click to change category' : undefined}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-all ${
          currentMeta.bg
        } ${currentMeta.text} ${currentMeta.border} ${
          interactive ? 'hover:brightness-110 cursor-pointer shadow-sm' : ''
        }`}
      >
        <CategoryIcon className="w-3 h-3 flex-shrink-0" />
        <span>{category}</span>
        {interactive && (
          <ChevronDown className="w-2.5 h-2.5 opacity-60 ml-0.5" />
        )}
      </button>

      {/* Flagged Anomaly Badge */}
      {isAnomaly && (
        <span 
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30 animate-pulse"
          title="This expense is unusually high compared to your typical spending"
        >
          <AlertCircle className="w-3 h-3" />
          <span>Unusual</span>
        </span>
      )}

      {/* Category Adjustment Popover */}
      {isOpen && (
        <div className="absolute left-0 top-full mt-1.5 w-48 bg-ink-raised border border-white/10 rounded-xl shadow-2xl z-50 py-1.5 overflow-hidden animate-[fadeIn_0.15s_ease-out]">
          <div className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-mist border-b border-white/5">
            Change Category
          </div>
          <div className="max-h-56 overflow-y-auto p-1 space-y-0.5">
            {CATEGORIES.map((cat) => {
              const isSelected = cat === category;
              const meta = categoryMeta[cat] || categoryMeta.Others;
              const Icon = meta.icon;
              return (
                <button
                  key={cat}
                  onClick={() => handleSelect(cat)}
                  className={`w-full text-left px-2.5 py-1.5 text-xs rounded-lg flex items-center justify-between transition-colors ${
                    isSelected 
                      ? 'bg-blue-600 text-white font-semibold' 
                      : 'text-slate-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Icon className="w-3.5 h-3.5" />
                    <span>{cat}</span>
                  </div>
                  {isSelected && <Check className="w-3.5 h-3.5 text-white" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
