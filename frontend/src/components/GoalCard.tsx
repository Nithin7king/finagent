/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Goal, GoalRecommendationData, GoalRecommendationItem } from '../types';
import { useFin } from '../FinContext';
import { 
  Target, 
  ArrowUpRight, 
  CheckCircle2, 
  Sparkles, 
  Zap, 
  ChevronDown, 
  ChevronUp, 
  Utensils, 
  Repeat, 
  Wallet, 
  Lightbulb, 
  Loader2, 
  TrendingUp,
  Clock,
  Trash2
} from 'lucide-react';

interface GoalCardProps {
  goal: Goal;
}

export const GoalCard: React.FC<GoalCardProps> = ({ goal }) => {
  const { contributeToGoal, deleteGoal, fetchGoalRecommendations } = useFin();
  const [isContributing, setIsContributing] = useState(false);
  const [amount, setAmount] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  // AI Recommender state
  const [isExpanded, setIsExpanded] = useState(false);
  const [recommendations, setRecommendations] = useState<GoalRecommendationData | null>(null);
  const [isLoadingRecs, setIsLoadingRecs] = useState(false);

  // Delete state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const percentage = Math.min(100, Math.round((goal.currentAmount / goal.targetAmount) * 100));

  // Currency format
  const formatValue = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const handleToggleRecs = async () => {
    const nextState = !isExpanded;
    setIsExpanded(nextState);

    if (nextState && !recommendations) {
      setIsLoadingRecs(true);
      const data = await fetchGoalRecommendations(goal.id);
      setRecommendations(data);
      setIsLoadingRecs(false);
    }
  };

  const handleQuickPreset = async (val: number) => {
    setIsSubmitting(true);
    await contributeToGoal(goal.id, val);
    setIsSubmitting(false);
    triggerSuccess();
    // Refresh recommendations if open
    if (isExpanded) {
      const data = await fetchGoalRecommendations(goal.id);
      setRecommendations(data);
    }
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
    // Refresh recommendations if open
    if (isExpanded) {
      const data = await fetchGoalRecommendations(goal.id);
      setRecommendations(data);
    }
  };

  const triggerSuccess = () => {
    setSuccess(true);
    setTimeout(() => setSuccess(false), 2500);
  };

  const getRecIcon = (type: string) => {
    switch (type) {
      case 'spending_cut':
        return <Utensils className="w-4 h-4 text-amber-400" />;
      case 'subscription_audit':
        return <Repeat className="w-4 h-4 text-blue-400" />;
      case 'salary_sweep':
        return <Wallet className="w-4 h-4 text-emerald-400" />;
      default:
        return <Lightbulb className="w-4 h-4 text-purple-400" />;
    }
  };

  const getBadgeStyle = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high':
        return 'bg-amber-500/10 text-amber-300 border-amber-500/30';
      case 'medium':
        return 'bg-blue-500/10 text-blue-300 border-blue-500/30';
      default:
        return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30';
    }
  };

  return (
    <div className={`bg-ink-raised border rounded-2xl flex flex-col justify-between transition-all duration-300 relative overflow-hidden shadow-xl shadow-black/25 ${
      isExpanded ? 'border-emerald-500/40 ring-1 ring-emerald-500/20' : 'border-white/10 hover:border-white/20'
    }`}>
      
      {/* Category Pill Tag & Delete Action */}
      <div className="absolute top-4 right-4 flex items-center space-x-1.5 z-10">
        <div className="bg-blue-500/10 border border-blue-500/20 text-[10px] font-semibold text-blue-300 px-2.5 py-0.5 rounded-full">
          {goal.category}
        </div>
        <button
          type="button"
          onClick={() => setShowDeleteConfirm(true)}
          title="Delete goal"
          className="p-1 rounded-lg text-mist/60 hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Delete Confirmation Overlay */}
      {showDeleteConfirm && (
        <div className="absolute inset-0 bg-ink/95 backdrop-blur-md z-30 p-5 flex flex-col justify-center items-center text-center animate-[fadeIn_0.15s_ease-out]">
          <div className="w-10 h-10 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 flex items-center justify-center mb-2">
            <Trash2 className="w-5 h-5" />
          </div>
          <div className="text-white font-semibold text-sm">Delete "{goal.name}"?</div>
          <p className="text-xs text-mist mt-1 max-w-[220px]">
            Are you sure you want to remove this goal? This cannot be undone.
          </p>
          <div className="flex items-center gap-2 mt-4">
            <button
              type="button"
              onClick={() => setShowDeleteConfirm(false)}
              disabled={isDeleting}
              className="px-3 py-1.5 rounded-lg border border-white/10 text-mist hover:text-white text-xs cursor-pointer transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={async () => {
                setIsDeleting(true);
                await deleteGoal(goal.id);
                setIsDeleting(false);
                setShowDeleteConfirm(false);
              }}
              disabled={isDeleting}
              className="px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-semibold shadow-md shadow-red-600/30 transition-all cursor-pointer flex items-center gap-1.5"
            >
              {isDeleting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
              <span>Delete Goal</span>
            </button>
          </div>
        </div>
      )}

      <div className="p-5">
        <div className="flex items-center space-x-2.5 pr-28">
          <div className="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center flex-shrink-0">
            <Target className="w-4 h-4" />
          </div>
          <h4 className="text-base text-white font-semibold truncate">
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

        {/* AI Goal Accelerator Banner Toggle */}
        <div className="mt-4">
          <button
            type="button"
            onClick={handleToggleRecs}
            className={`w-full p-2.5 rounded-xl border text-left flex items-center justify-between transition-all cursor-pointer ${
              isExpanded 
                ? 'bg-gradient-to-r from-emerald-500/15 via-blue-500/10 to-transparent border-emerald-500/30' 
                : 'bg-ink/70 hover:bg-ink border-white/10 hover:border-emerald-500/30'
            }`}
          >
            <div className="flex items-center space-x-2 min-w-0">
              <div className="w-6 h-6 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center flex-shrink-0">
                <Sparkles className="w-3.5 h-3.5 animate-pulse" />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-white flex items-center gap-1.5">
                  <span>AI Goal Accelerator</span>
                  {recommendations && recommendations.months_saved > 0 && (
                    <span className="text-[10px] bg-emerald-500/20 text-emerald-300 font-bold px-1.5 py-0.2 rounded-md">
                      ⚡ -{recommendations.months_saved} mos
                    </span>
                  )}
                </div>
                <div className="text-[10px] text-mist truncate">
                  Reach milestone earlier based on transaction patterns
                </div>
              </div>
            </div>

            <div className="text-mist hover:text-white flex items-center pl-2 flex-shrink-0">
              {isExpanded ? <ChevronUp className="w-4 h-4 text-emerald-400" /> : <ChevronDown className="w-4 h-4" />}
            </div>
          </button>
        </div>

        {/* Expanded Recommendations Content */}
        {isExpanded && (
          <div className="mt-3 space-y-2.5 pt-3 border-t border-white/5 animate-[fadeIn_0.2s_ease-out]">
            {isLoadingRecs ? (
              <div className="py-6 flex flex-col items-center justify-center text-center space-y-2">
                <Loader2 className="w-5 h-5 text-emerald-400 animate-spin" />
                <p className="text-xs text-mist">
                  Analyzing transaction history & recurring expenses...
                </p>
              </div>
            ) : recommendations ? (
              <>
                {/* Acceleration Metric Banner */}
                <div className="p-3 rounded-xl bg-ink/90 border border-emerald-500/20 flex flex-col gap-1.5">
                  <div className="flex items-center space-x-2 text-xs font-semibold text-white">
                    <Clock className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                    <span>
                      Optimized Timeline: <strong className="text-emerald-300">~{recommendations.optimized_timeline_months} months</strong>
                      <span className="text-mist font-normal"> (currently ~{recommendations.current_timeline_months} mos)</span>
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-300 pl-5.5 leading-relaxed">
                    You can achieve this target <strong className="text-emerald-400 font-semibold">{recommendations.months_saved} months sooner</strong> ({recommendations.acceleration_pct}% faster) with these transaction-grounded adjustments:
                  </div>
                </div>

                {/* Individual Recommendations */}
                <div className="space-y-2">
                  {recommendations.recommendations.map((rec: GoalRecommendationItem) => (
                    <div 
                      key={rec.id}
                      className="p-3 rounded-xl bg-ink/60 border border-white/5 hover:border-white/15 transition-all text-xs"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center space-x-2 min-w-0">
                          <div className="p-1 rounded-lg bg-white/5 flex-shrink-0">
                            {getRecIcon(rec.type)}
                          </div>
                          <span className="font-semibold text-white truncate text-xs">
                            {rec.title}
                          </span>
                        </div>
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border flex-shrink-0 ${getBadgeStyle(rec.priority)}`}>
                          {rec.badge}
                        </span>
                      </div>

                      <p className="mt-1.5 text-[11px] text-mist leading-relaxed pl-7">
                        {rec.message}
                      </p>

                      <div className="mt-2.5 pt-2 border-t border-white/5 flex items-center justify-between text-[11px] pl-7">
                        <span className="text-emerald-400 font-semibold flex items-center gap-1">
                          <TrendingUp className="w-3 h-3" />
                          <span>+{formatValue(rec.monthly_savings)}/mo</span>
                          <span className="text-mist font-normal">({rec.impact})</span>
                        </span>

                        <button
                          type="button"
                          onClick={() => {
                            setAmount(rec.monthly_savings.toString());
                            setIsContributing(true);
                          }}
                          className="px-2 py-0.5 rounded bg-emerald-500/10 hover:bg-emerald-500 text-emerald-300 hover:text-white border border-emerald-500/25 transition-all text-[10px] font-medium cursor-pointer"
                        >
                          Deposit ₹{rec.monthly_savings}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="p-3 text-center text-xs text-mist">
                No recommendations available. Try adding more transactions!
              </div>
            )}
          </div>
        )}
      </div>

      {/* Contribute Actions */}
      <div className="p-5 pt-0">
        <div className="pt-3 border-t border-white/5">
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
    </div>
  );
};
