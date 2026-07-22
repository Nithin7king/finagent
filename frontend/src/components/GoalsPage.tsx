/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { useFin } from '../FinContext';
import { GoalCard } from './GoalCard';
import { Plus, X, Landmark, Compass, Target, ArrowRight } from 'lucide-react';

export const GoalsPage: React.FC = () => {
  const { goals, createGoal } = useFin();
  const [showModal, setShowModal] = useState(false);

  // New goal form state
  const [name, setName] = useState('');
  const [targetAmount, setTargetAmount] = useState('');
  const [currentAmount, setCurrentAmount] = useState('');
  const [targetDate, setTargetDate] = useState('');
  const [category, setCategory] = useState('Savings');

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
    setCategory('Savings');
    setIsSubmitting(false);
    setShowModal(false);
  };

  return (
    <div className="space-y-6 animate-[fadeIn_0.2s_ease-out]">
      <div className="border-b border-gold/10 pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-gold font-bold">
            ALLOCATED TARGET ACCOUNTS
          </div>
          <h2 className="text-3.5xl font-display font-medium text-white tracking-tight italic mt-1">
            Financial Goals
          </h2>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="flex items-center space-x-2 px-4.5 py-2.5 bg-gold text-ink font-sans text-xs font-bold uppercase tracking-wide hover:brightness-110 active:scale-95 transition-all rounded-sm cursor-pointer self-start sm:self-auto"
        >
          <Plus className="w-4.5 h-4.5 stroke-[2.5]" />
          <span>Establish Savings Target</span>
        </button>
      </div>

      {/* Goals grid list */}
      {goals.length === 0 ? (
        <div className="p-16 border border-gold/10 rounded-sm text-center bg-ink-raised">
          <div className="text-mist text-3xl font-display italic">No savings targets allocated</div>
          <p className="text-xs text-mist/65 max-w-sm mx-auto mt-2 leading-relaxed">
            Create an Emergency Fund or target account by clicking the savings target portal above.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {goals.map((goal) => (
            <GoalCard key={goal.id} goal={goal} />
          ))}
        </div>
      )}

      {/* New Goal custom modal dialog */}
      {showModal && (
        <div className="fixed inset-0 bg-ink/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-ink-raised border border-gold/20 w-full max-w-md rounded-sm shadow-2xl overflow-hidden animate-[fadeIn_0.2s_ease-out]">
            
            {/* Modal Header */}
            <div className="p-6 border-b border-gold/10 bg-ink flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <Target className="w-5 h-5 text-gold" />
                <h3 className="text-base font-display text-white font-medium tracking-wide">Establish Savings Target</h3>
              </div>
              <button 
                onClick={() => setShowModal(false)}
                className="text-mist hover:text-white p-1 rounded-sm"
              >
                <X className="w-4.5 h-4.5" />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleSubmit} className="p-6 space-y-4 font-mono text-xs">
              
              <div>
                <label className="block text-[10px] text-mist uppercase tracking-wider mb-1.5">Goal Description / Title</label>
                <input
                  type="text"
                  placeholder="e.g. Wedding Downpayment, New Server"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full bg-ink border border-gold/15 text-white py-2.5 px-4 rounded-sm focus:border-gold placeholder:text-mist/25"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] text-mist uppercase tracking-wider mb-1.5">Target Amount (₹)</label>
                  <input
                    type="number"
                    placeholder="e.g. 150000"
                    value={targetAmount}
                    onChange={(e) => setTargetAmount(e.target.value)}
                    required
                    className="w-full bg-ink border border-gold/15 text-white py-2.5 px-4 rounded-sm focus:border-gold placeholder:text-mist/25"
                  />
                </div>

                <div>
                  <label className="block text-[10px] text-mist uppercase tracking-wider mb-1.5">Initial Deposit (Optional)</label>
                  <input
                    type="number"
                    placeholder="e.g. 10000"
                    value={currentAmount}
                    onChange={(e) => setCurrentAmount(e.target.value)}
                    className="w-full bg-ink border border-gold/15 text-white py-2.5 px-4 rounded-sm focus:border-gold placeholder:text-mist/25"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] text-mist uppercase tracking-wider mb-1.5">Target Date</label>
                  <input
                    type="date"
                    value={targetDate}
                    onChange={(e) => setTargetDate(e.target.value)}
                    required
                    className="w-full bg-ink border border-gold/15 text-white py-2.5 px-4 rounded-sm focus:border-gold text-white"
                  />
                </div>

                <div>
                  <label className="block text-[10px] text-mist uppercase tracking-wider mb-1.5">Category Designation</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full bg-ink border border-gold/15 text-white py-2.5 px-4 rounded-sm focus:border-gold"
                  >
                    <option value="Savings">Savings</option>
                    <option value="Gadgets">Gadgets</option>
                    <option value="Tax">Tax Optimization</option>
                    <option value="Travel">Travel / Leisure</option>
                    <option value="Investments">Investments</option>
                    <option value="Others">Others</option>
                  </select>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 flex items-center justify-end space-x-3 border-t border-gold/10 mt-6">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2.5 border border-gold/15 text-mist hover:text-white rounded-sm font-mono tracking-wide"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2.5 bg-gold text-ink font-bold font-sans flex items-center space-x-1.5 rounded-sm hover:brightness-110 active:scale-95 transition-all cursor-pointer"
                >
                  <span>{isSubmitting ? 'Recording...' : 'Register Target'}</span>
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
