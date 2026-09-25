/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { useFin } from '../FinContext';
import { GoalCard } from './GoalCard';
import { Plus, X, Landmark, Compass, Target, ArrowRight, Sparkles } from 'lucide-react';

export const GoalsPage: React.FC = () => {
  const { goals, createGoal } = useFin();
  const [showModal, setShowModal] = useState(false);

  // New goal form state
  const [name, setName] = useState('');
  const [targetAmount, setTargetAmount] = useState('');
  const [currentAmount, setCurrentAmount] = useState('');
  const [targetDate, setTargetDate] = useState('');
  const [category, setCategory] = useState('Emergency Fund');

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !targetAmount || !targetDate) return;
    
    setIsSubmitting(true);
    await createGoal({
      name,
      targetAmount: Number(targetAmount),
      currentAmount: Number(currentAmount || 0),
      targetDate,
      category,
    });
    
    // Clear & close
    setName('');
    setTargetAmount('');
    setCurrentAmount('');
    setTargetDate('');
    setCategory('Emergency Fund');
    setIsSubmitting(false);
    setShowModal(false);
  };

  return (
    <div className="space-y-6 animate-[fadeIn_0.2s_ease-out]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-white/5">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Savings Goals
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Track and achieve your financial targets — emergency fund, vehicle, vacation, or investments.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="flex items-center space-x-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm rounded-xl shadow-lg shadow-emerald-600/25 transition-all cursor-pointer self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Create New Goal</span>
        </button>
      </div>

      {/* Goals grid list */}
      {goals.length === 0 ? (
        <div className="p-12 border border-white/10 rounded-2xl text-center bg-ink-raised backdrop-blur-sm">
          <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto mb-4">
            <Target className="w-7 h-7" />
          </div>
          <div className="text-white text-lg font-semibold">No active savings goals yet</div>
          <p className="text-sm text-mist max-w-md mx-auto mt-2 leading-relaxed">
            Setting clear targets helps you save consistently. Create an emergency fund, save for a gadget, or plan your next vacation.
          </p>
          <button
            onClick={() => setShowModal(true)}
            className="mt-6 inline-flex items-center space-x-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm rounded-xl transition-all cursor-pointer shadow-lg shadow-emerald-600/20"
          >
            <Plus className="w-4 h-4" />
            <span>Create First Goal</span>
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="p-3.5 rounded-2xl bg-gradient-to-r from-emerald-500/10 via-blue-500/10 to-purple-500/5 border border-emerald-500/20 flex items-center space-x-3 text-xs">
            <div className="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="text-slate-300">
              <strong className="text-white font-semibold">AI Recommender Agent Active: </strong>
              Each goal analyzes your transactions to calculate early milestone completion. Click <strong className="text-emerald-300">AI Goal Accelerator</strong> on any goal to view and apply recommendations.
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
            {goals.map((goal) => (
              <GoalCard key={goal.id} goal={goal} />
            ))}
          </div>
        </div>
      )}

      {/* New Goal Modal Dialog */}
      {showModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-ink-raised border border-white/10 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden animate-[fadeIn_0.2s_ease-out]">
            
            {/* Modal Header */}
            <div className="p-5 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  <Target className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Create Savings Goal</h3>
                  <p className="text-xs text-mist">Define what you are saving for</p>
                </div>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-mist hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleSubmit} className="p-5 space-y-4 text-sm">
              
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Goal Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. MacBook Pro M3 or Emergency Fund"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full bg-ink border border-white/10 text-white py-2 px-3.5 rounded-xl focus:outline-none focus:border-emerald-500 placeholder:text-mist/60 text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Target Amount (₹)
                  </label>
                  <input
                    type="number"
                    placeholder="100000"
                    value={targetAmount}
                    onChange={(e) => setTargetAmount(e.target.value)}
                    required
                    min="100"
                    className="w-full bg-ink border border-white/10 text-white py-2 px-3.5 rounded-xl focus:outline-none focus:border-emerald-500 placeholder:text-mist/60 font-mono text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Already Saved (₹)
                  </label>
                  <input
                    type="number"
                    placeholder="0"
                    value={currentAmount}
                    onChange={(e) => setCurrentAmount(e.target.value)}
                    min="0"
                    className="w-full bg-ink border border-white/10 text-white py-2 px-3.5 rounded-xl focus:outline-none focus:border-emerald-500 placeholder:text-mist/60 font-mono text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Target Date
                  </label>
                  <input
                    type="date"
                    value={targetDate}
                    onChange={(e) => setTargetDate(e.target.value)}
                    required
                    className="w-full bg-ink border border-white/10 text-white py-2 px-3.5 rounded-xl focus:outline-none focus:border-emerald-500 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full bg-ink border border-white/10 text-white py-2 px-3.5 rounded-xl focus:outline-none focus:border-emerald-500 text-sm"
                  >
                    <option value="Emergency Fund">Emergency Fund</option>
                    <option value="Travel">Travel & Vacation</option>
                    <option value="Gadgets">Gadgets & Electronics</option>
                    <option value="Vehicle">Vehicle / Bike</option>
                    <option value="Home">Home & Renovation</option>
                    <option value="Investments">Mutual Funds / Stocks</option>
                    <option value="Savings">General Savings</option>
                    <option value="Others">Others</option>
                  </select>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 flex items-center justify-end space-x-3 border-t border-white/10 mt-6">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-white/10 text-mist hover:text-white rounded-xl text-sm font-medium hover:bg-white/5 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-sm flex items-center space-x-1.5 rounded-xl transition-all cursor-pointer disabled:opacity-50 shadow-lg shadow-emerald-600/25"
                >
                  <span>{isSubmitting ? 'Saving...' : 'Save Goal'}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>

            </form>
          </div>
        </div>
      )}
    </div>
  );
};
