/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export type Category = 'Salary' | 'Investment' | 'Housing' | 'Food' | 'Utilities' | 'Transport' | 'Shopping' | 'Entertainment' | 'Others';

export interface Transaction {
  id: string;
  date: string; // YYYY-MM-DD
  description: string;
  amount: number; // positive for income, negative for expense
  category: Category;
  status: 'AI-assigned' | 'user-corrected';
  isAnomaly: boolean;
  balanceAfter: number;
}

export interface Anomaly {
  id: string;
  transactionId: string;
  date: string;
  merchant: string;
  amount: number;
  severity: 'Low' | 'Medium' | 'High';
  explanation: string;
}

export interface Subscription {
  id: string;
  merchant: string;
  amount: number;
  cadence: string;
  nextChargeDate: string;
  creepScore: number; // 0 to 100
}

export interface ForecastPoint {
  date: string; // Month/Day or Year-Month-Day
  projected: number;
  confidenceMin: number;
  confidenceMax: number;
}

export interface Goal {
  id: string;
  name: string;
  targetAmount: number;
  currentAmount: number;
  targetDate: string;
  category: string;
}

export interface GoalRecommendationItem {
  id: string;
  type: string;
  title: string;
  message: string;
  impact: string;
  monthly_savings: number;
  priority: string;
  badge: string;
}

export interface GoalRecommendationData {
  goal_id: number | string;
  goal_name: string;
  remaining_amount: number;
  current_timeline_months: number;
  optimized_timeline_months: number;
  months_saved: number;
  acceleration_pct: number;
  recommendations: GoalRecommendationItem[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: string;
  toolCalls?: string[]; // e.g. ["Checked 3 anomalies", "Searched knowledge base"]
}

export interface DashboardSummary {
  totalBalance: number;
  thisMonthSpend: number;
  savingsRate: number; // percentage
  anomaliesCount: number;
}

export interface KycData {
  kyc_status: 'pending' | 'pan_verified' | 'verified';
  pan_number?: string;
  pan_verified: boolean;
  aadhaar_masked?: string;
  digilocker_verified: boolean;
  monthly_income: number;
  kyc_completed_at?: string;
}

export interface UserProfile {
  id?: number;
  name: string;
  email: string;
  monthly_income?: number;
  currency?: string;
  kyc_status?: 'pending' | 'pan_verified' | 'verified';
  digilocker_verified?: boolean;
  pan_verified?: boolean;
}

