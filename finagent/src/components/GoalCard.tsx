/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Goal } from '../types';
import { useFin } from '../FinContext';
import { PlusCircle, Target, ArrowUpRight, CheckCircle2 } from 'lucide-react';

interface GoalCardProps {
  goal: Goal;
}

export const GoalCard: React.FC<GoalCardProps> = ({ goal }) => {
  const { contributeToGoal } = useFin();
  const [isContributing, setIsContributing] = useState(false);
  const [amount, setAmount] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const percentage = Math.min(100, Math.round((goal.currentAmount / goal.targetAmount) * 100));

  // Currency formats
  const formatValue = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const handleQuickPreset = async (val: number) => {
    setIsSubmitting(true);
    await contributeToGoal(goal.id, val);
    setIsSubmitting(false);
    triggerSuccess();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const num = Number(amount);
    if (isNaN(num) || num <= 0) return;
    
    setIsSubmitting(true);
    await contributeToGoal(goal.id, num);
    setIsSubmitting(false);
    setAmount('');
    setIsContributing(false);
    triggerSuccess();
  };

  const triggerSuccess = () => {
    setSuccess(true);
    setTimeout(() => setSuccess(false), 2000);
  };

  return (
    <div className="bg-ink-raised border border-gold/10 p-6 rounded-sm flex flex-col justify-between hover:border-gold/30 transition-all duration-300 relative overflow-hidden">
      
      {/* Decorative Stamp Tag */}
      <div className="absolute top-4 right-4 bg-gold/5 border border-gold/15 text-[9px] font-mono font-medium text-gold px-2 py-0.5 uppercase rounded-sm select-none">
        {goal.category}
      </div>

      <div>
        <div className="flex items-center space-x-2.5">
          <Target className="w-4.5 h-4.5 text-gold" />
          <h4 className="font-display text-base text-white tracking-wide font-medium">
            {goal.name}
          </h4>
        </div>

        {/* Amount Progress Monospace Row */}
        <div className="mt-5 flex items-baseline justify-between text-xs font-mono">
          <span className="text-mist">Saved: <strong className="text-white font-bold">{formatValue(goal.currentAmount)}</strong></span>
          <span className="text-mist/50">Target: {formatValue(goal.targetAmount)}</span>
        </div>

        {/* Progress Bar (Gold Fill) */}
        <div className="mt-2.5 h-1.5 w-full bg-ink rounded-sm overflow-hidden border border-gold/5">
          <div 
            className="h-full bg-gold transition-all duration-500 ease-out"
            style={{ width: `${percentage}%` }}
          />
        </div>

        <div className="mt-2 flex items-center justify-between text-[10px] font-mono">
          <span className="text-gold font-bold">{percentage}% Completed</span>
          <span className="text-mist/60">Date: {goal.targetDate}</span>
        </div>
      </div>

      {/* Contribute Actions */}
      <div className="mt-6 pt-5 border-t border-gold/10">
        {success ? (
          <div className="py-1 text-center text-xs font-mono text-sage flex items-center justify-center space-x-1.5 animate-pulse">
            <CheckCircle2 className="w-4 h-4" />
            <span>Contribution Logged Successfully!</span>
          </div>
        ) : !isContributing ? (
          <div className="flex items-center justify-between gap-2.5">
            {/* Quick allocation presets */}
            <div className="flex items-center space-x-1.5">
              <button 
                onClick={() => handleQuickPreset(5000)}
                disabled={isSubmitting}
                className="px-2 py-1 bg-ink border border-gold/10 rounded-sm text-[10px] font-mono text-mist hover:text-white hover:border-gold/35 transition-all cursor-pointer"
              >
                +₹5K
              </button>
              <button 
                onClick={() => handleQuickPreset(10000)}
                disabled={isSubmitting}
                className="px-2 py-1 bg-ink border border-gold/10 rounded-sm text-[10px] font-mono text-mist hover:text-white hover:border-gold/35 transition-all cursor-pointer"
              >
                +₹10K
              </button>
            </div>

            <button
              onClick={() => setIsContributing(true)}
              disabled={isSubmitting}
              className="px-3.5 py-1.5 bg-gold/10 hover:bg-gold text-gold hover:text-ink text-xs font-mono border border-gold/20 font-bold transition-all flex items-center space-x-1.5 rounded-sm cursor-pointer ml-auto"
            >
              <span>Custom</span>
              <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex items-center gap-2 animate-[fadeIn_0.15s_ease-out]">
            <div className="relative flex-1">
              <span className="absolute left-2.5 top-1/2 -translate-y-1/2 font-mono text-xs text-gold">₹</span>
              <input
                type="number"
                placeholder="Amount"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
                disabled={isSubmitting}
                className="w-full bg-ink border border-gold/25 text-white pl-6 pr-2 py-1 text-xs font-mono rounded-sm focus:border-gold placeholder:text-mist/30"
              />
            </div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-3 py-1.5 bg-gold text-ink text-xs font-mono font-bold hover:brightness-110 transition-all rounded-sm cursor-pointer"
            >
              Post
            </button>
            <button
              type="button"
              onClick={() => setIsContributing(false)}
              className="px-2 py-1.5 border border-gold/10 text-mist hover:text-white text-xs font-mono rounded-sm cursor-pointer"
            >
              Cancel
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
