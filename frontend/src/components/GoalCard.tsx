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
    <div className="bg-ink-raised border border-white/10 p-5 rounded-2xl flex flex-col justify-between hover:border-white/20 transition-all duration-200 relative overflow-hidden shadow-lg shadow-black/20">
      
      {/* Category Pill Tag */}
      <div className="absolute top-4 right-4 bg-blue-500/10 border border-blue-500/20 text-[10px] font-semibold text-blue-300 px-2.5 py-0.5 rounded-full">
        {goal.category}
      </div>

      <div>
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
            <Target className="w-4 h-4" />
          </div>
          <h4 className="text-base text-white font-semibold">
            {goal.name}
          </h4>
        </div>

        {/* Progress figures */}
        <div className="mt-4 flex items-baseline justify-between text-xs">
          <span className="text-mist">Saved: <strong className="text-white font-bold">{formatValue(goal.currentAmount)}</strong></span>
          <span className="text-mist">Target: {formatValue(goal.targetAmount)}</span>
        </div>

        {/* Progress Bar (Emerald fill) */}
        <div className="mt-2 h-2 w-full bg-ink rounded-full overflow-hidden">
          <div 
            className={`h-full transition-all duration-500 ease-out rounded-full ${
              percentage >= 100 ? 'bg-emerald-400' : 'bg-gradient-to-r from-blue-500 to-emerald-400'
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>

        <div className="mt-2 flex items-center justify-between text-xs">
          <span className="text-emerald-400 font-semibold">{percentage}% saved</span>
          <span className="text-mist text-[11px]">Target: {goal.targetDate}</span>
        </div>
      </div>

      {/* Contribute Actions */}
      <div className="mt-5 pt-4 border-t border-white/5">
        {success ? (
          <div className="py-1 text-center text-xs font-medium text-emerald-400 flex items-center justify-center space-x-1.5 animate-pulse">
            <CheckCircle2 className="w-4 h-4" />
            <span>Savings recorded successfully!</span>
          </div>
        ) : !isContributing ? (
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center space-x-1.5">
              {[500, 1000, 5000].map((preset) => (
                <button
                  key={preset}
                  onClick={() => handleQuickPreset(preset)}
                  disabled={isSubmitting}
                  className="px-2.5 py-1 text-xs font-mono font-medium rounded-lg bg-ink hover:bg-emerald-600 hover:text-white text-mist border border-white/10 transition-all cursor-pointer"
                >
                  +₹{preset}
                </button>
              ))}
            </div>

            <button
              onClick={() => setIsContributing(true)}
              disabled={isSubmitting}
              className="px-3 py-1 bg-emerald-600/10 hover:bg-emerald-600 text-emerald-400 hover:text-white text-xs font-medium border border-emerald-500/20 transition-all flex items-center space-x-1 rounded-lg cursor-pointer ml-auto"
            >
              <span>+ Custom</span>
              <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex items-center gap-2 animate-[fadeIn_0.15s_ease-out]">
            <div className="relative flex-1">
              <span className="absolute left-2.5 top-1/2 -translate-y-1/2 font-mono text-xs text-emerald-400">₹</span>
              <input
                type="number"
                placeholder="Amount"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
                disabled={isSubmitting}
                className="w-full bg-ink border border-white/10 text-white pl-6 pr-2 py-1 text-xs font-mono rounded-lg focus:outline-none focus:border-emerald-500 placeholder:text-mist/60"
              />
            </div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition-all rounded-lg cursor-pointer shadow-md shadow-emerald-600/20"
            >
              Save
            </button>
            <button
              type="button"
              onClick={() => setIsContributing(false)}
              className="px-2 py-1 border border-white/10 text-mist hover:text-white text-xs rounded-lg cursor-pointer"
            >
              Cancel
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
