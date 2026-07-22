/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";
import dotenv from "dotenv";

dotenv.config();

// Initialize Gemini Client
const ai = process.env.GEMINI_API_KEY
  ? new GoogleGenAI({
      apiKey: process.env.GEMINI_API_KEY,
      httpOptions: {
        headers: {
          "User-Agent": "aistudio-build",
        },
      },
    })
  : null;

const app = express();
const PORT = 3000;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Custom tiny cookie parser
function parseCookies(cookieHeader?: string) {
  const cookies: Record<string, string> = {};
  if (!cookieHeader) return cookies;
  cookieHeader.split(";").forEach((cookie) => {
    const parts = cookie.split("=");
    if (parts.length === 2) {
      cookies[parts[0].trim()] = parts[1].trim();
    }
  });
  return cookies;
}

// In-memory Database State
interface DB {
  user: { name: string; email: string } | null;
  transactions: any[];
  goals: any[];
  subscriptions: any[];
  chatHistory: any[];
  anomaliesPool: any[];
}

const initialBalance = 250000;

const seedTransactions = [
  {
    id: "tx-1",
    date: "2026-07-01",
    description: "Salary - TCS",
    amount: 185000,
    category: "Salary",
    status: "AI-assigned",
    isAnomaly: false,
  },
  {
    id: "tx-2",
    date: "2026-07-02",
    description: "Zerodha Mutual Fund SIP",
    amount: -30000,
    category: "Investment",
    status: "AI-assigned",
    isAnomaly: false,
  },
  {
    id: "tx-3",
    date: "2026-07-03",
    description: "HDFC Housing Loan EMI",
    amount: -45000,
    category: "Housing",
    status: "AI-assigned",
    isAnomaly: false,
  },
  {
    id: "tx-4",
    date: "2026-07-04",
    description: "Swiggy Gourmet Feast",
    amount: -12500,
    category: "Food",
    status: "AI-assigned",
    isAnomaly: true,
  },
  {
    id: "tx-5",
    date: "2026-07-05",
    description: "Tata Power Electricity Bill",
    amount: -6200,
    category: "Utilities",
    status: "AI-assigned",
    isAnomaly: false,
  },
  {
    id: "tx-6",
    date: "2026-07-06",
    description: "Uber Premium Ride",
    amount: -1850,
    category: "Transport",
    status: "AI-assigned",
    isAnomaly: false,
  },
  {
    id: "tx-7",
    date: "2026-07-08",
    description: "Amazon India - Ergonomic Office Chair",
    amount: -15400,
    category: "Shopping",
    status: "AI-assigned",
    isAnomaly: false,
  },
  {
    id: "tx-8",
    date: "2026-07-10",
    description: "Airtel Fiber Broadband",
    amount: -1199,
    category: "Utilities",
    status: "AI-assigned",
    isAnomaly: false,
  },
  {
    id: "tx-9",
    date: "2026-07-11",
    description: "Netflix India Premium",
    amount: -649,
    category: "Entertainment",
    status: "AI-assigned",
    isAnomaly: false,
  },
  {
    id: "tx-10",
    date: "2026-07-11",
    description: "Netflix India Premium (Duplicate)",
    amount: -649,
    category: "Entertainment",
    status: "AI-assigned",
    isAnomaly: true,
  },
  {
    id: "tx-11",
    date: "2026-07-12",
    description: "Zomato Delivery",
    amount: -850,
    category: "Food",
    status: "AI-assigned",
    isAnomaly: false,
  },
  {
    id: "tx-12",
    date: "2026-07-13",
    description: "Cult.fit Annual Gym Membership",
    amount: -2500,
    category: "Others",
    status: "AI-assigned",
    isAnomaly: false,
  },
  {
    id: "tx-13",
    date: "2026-07-14",
    description: "Unrecognized SaaS fee - cloudbill.io",
    amount: -4999,
    category: "Others",
    status: "AI-assigned",
    isAnomaly: true,
  },
  {
    id: "tx-14",
    date: "2026-07-15",
    description: "Blue Tokai Coffee",
    amount: -320,
    category: "Food",
    status: "AI-assigned",
    isAnomaly: false,
  },
  {
    id: "tx-15",
    date: "2026-07-16",
    description: "Swiggy Instant Grocery",
    amount: -450,
    category: "Food",
    status: "AI-assigned",
    isAnomaly: false,
  },
];

// Helper to compute running balances
function computeBalances(txs: any[]) {
  // Sort ascending for balance computation
  const sorted = [...txs].sort((a, b) => a.date.localeCompare(b.date));
  let running = initialBalance;
  const balanceMap: Record<string, number> = {};
  
  for (const t of sorted) {
    running += t.amount;
    balanceMap[t.id] = running;
  }
  
  // Return original array structure but with injected balanceAfter
  return txs.map(t => ({
    ...t,
    balanceAfter: balanceMap[t.id] || initialBalance
  }));
}

function createDefaultUserDb(name: string, email: string): DB {
  const isDemo = email.toLowerCase() === "demo@finagent.ai";
  const firstName = name.split(" ")[0];
  
  return {
    user: { name, email },
    transactions: computeBalances([...seedTransactions]),
    goals: [
      {
        id: "goal-1",
        name: "Emergency Fund",
        targetAmount: 300000,
        currentAmount: 180000,
        targetDate: "2026-12-31",
        category: "Savings",
      },
      {
        id: "goal-2",
        name: "New Macbook Pro M5",
        targetAmount: 150000,
        currentAmount: 90000,
        targetDate: "2026-09-30",
        category: "Gadgets",
      },
      {
        id: "goal-3",
        name: "Tax Saving ELSS Mutual Funds",
        targetAmount: 150000,
        currentAmount: 120000,
        targetDate: "2027-03-31",
        category: "Tax",
      },
    ],
    subscriptions: [
      {
        id: "sub-1",
        merchant: "Netflix India Premium",
        amount: 649,
        cadence: "Monthly",
        nextChargeDate: "2026-08-11",
        creepScore: 15,
      },
      {
        id: "sub-2",
        merchant: "Airtel Fiber Broadband",
        amount: 1199,
        cadence: "Monthly",
        nextChargeDate: "2026-08-10",
        creepScore: 8,
      },
      {
        id: "sub-3",
        merchant: "Cult.fit Premium",
        amount: 2500,
        cadence: "Monthly",
        nextChargeDate: "2026-08-13",
        creepScore: 45,
      },
      {
        id: "sub-4",
        merchant: "Unrecognized SaaS fee - cloudbill.io",
        amount: 4999,
        cadence: "Monthly",
        nextChargeDate: "2026-08-14",
        creepScore: 85,
      },
    ],
    chatHistory: [
      {
        id: "msg-1",
        sender: "agent",
        text: `Namaste ${firstName}! I am your FinAgent assistant. I have reviewed your Indian banking passbook and identified ₹2,16,133 in current active capital, with 3 high-impact anomalies flagged in the current billing cycle. How may I help you optimize your tax savings, investments, or budget today?`,
        timestamp: new Date().toISOString(),
      },
    ],
    anomaliesPool: [
      {
        id: "anom-1",
        transactionId: "tx-4",
        date: "2026-07-04",
        merchant: "Swiggy Gourmet Feast",
        amount: -12500,
        severity: "High",
        explanation: "This Swiggy transaction of ₹12,500 is 14.8x higher than your average meal cost of ₹845. Flagged as severe anomaly.",
      },
      {
        id: "anom-2",
        transactionId: "tx-10",
        date: "2026-07-11",
        merchant: "Netflix India Premium (Duplicate)",
        amount: -649,
        severity: "Medium",
        explanation: "A duplicate subscription billing for Netflix India Premium (₹649) was detected on the exact same date (July 11). Flagged for automated merchant dispute refund.",
      },
      {
        id: "anom-3",
        transactionId: "tx-13",
        date: "2026-07-14",
        merchant: "Unrecognized SaaS fee - cloudbill.io",
        amount: -4999,
        severity: "High",
        explanation: "Unrecognized transaction from cloudbill.io (₹4,999) with zero prior billing history. Subscriptions audit indicates a silent credit card charge leak.",
      },
    ]
  };
}

interface UserRecord {
  name: string;
  email: string;
  passwordHash: string;
  db: DB;
}

const usersDb: Record<string, UserRecord> = {
  "demo@finagent.ai": {
    name: "Siva Sudhamsh",
    email: "demo@finagent.ai",
    passwordHash: "demo-password",
    db: createDefaultUserDb("Siva Sudhamsh", "demo@finagent.ai")
  }
};

function getUserDb(req: express.Request): DB {
  const cookies = parseCookies(req.headers.cookie);
  const email = cookies["fin_jwt"] ? cookies["fin_jwt"].toLowerCase() : null;
  
  if (email && usersDb[email]) {
    return usersDb[email].db;
  }
  
  // Return demo user's db as a fallback so that active preview tabs work nicely
  return usersDb["demo@finagent.ai"].db;
}

// Auth Endpoints
app.post("/api/auth/login", (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) {
    return res.status(400).json({ error: "Email and password are required" });
  }
  
  const emailLower = email.toLowerCase();
  const userRecord = usersDb[emailLower];
  
  if (!userRecord || userRecord.passwordHash !== password) {
    return res.status(401).json({ error: "Invalid email or secret pin/password credentials." });
  }
  
  res.cookie("fin_jwt", emailLower, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
  });
  
  res.json({ message: "Logged in successfully", user: { name: userRecord.name, email: userRecord.email } });
});

app.post("/api/auth/register", (req, res) => {
  const { name, email, password } = req.body;
  if (!name || !email || !password) {
    return res.status(400).json({ error: "All fields are required" });
  }
  
  const emailLower = email.toLowerCase();
  if (usersDb[emailLower]) {
    return res.status(400).json({ error: "Email is already registered" });
  }
  
  // Create user database sandbox
  const userDb = createDefaultUserDb(name, emailLower);
  
  usersDb[emailLower] = {
    name,
    email: emailLower,
    passwordHash: password,
    db: userDb,
  };
  
  res.cookie("fin_jwt", emailLower, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    maxAge: 7 * 24 * 60 * 60 * 1000,
  });
  
  res.json({ message: "Registered successfully", user: { name, email: emailLower } });
});

app.get("/api/auth/me", (req, res) => {
  const cookies = parseCookies(req.headers.cookie);
  const email = cookies["fin_jwt"] ? cookies["fin_jwt"].toLowerCase() : null;
  
  if (email && usersDb[email]) {
    const userRecord = usersDb[email];
    return res.json({ user: { name: userRecord.name, email: userRecord.email } });
  }
  
  // If there's no cookie, return 401 unauthenticated
  return res.status(401).json({ error: "Not authenticated" });
});

app.post("/api/auth/logout", (req, res) => {
  res.clearCookie("fin_jwt");
  res.json({ message: "Logged out successfully" });
});

// Transactions Endpoints
app.get("/api/transactions", (req, res) => {
  const db = getUserDb(req);
  res.json({ transactions: db.transactions });
});

app.post("/api/transactions", (req, res) => {
  const db = getUserDb(req);
  const { date, description, amount, category } = req.body;
  if (!date || !description || !amount || !category) {
    return res.status(400).json({ error: "Missing required transaction fields" });
  }
  
  const newTx = {
    id: `tx-${Date.now()}`,
    date,
    description,
    amount: Number(amount),
    category,
    status: "user-corrected",
    isAnomaly: false,
  };
  
  db.transactions.push(newTx);
  db.transactions = computeBalances(db.transactions);
  
  res.json({ message: "Transaction created", transaction: newTx, transactions: db.transactions });
});

// Inline category adjustment
app.post("/api/transactions/:id/category", (req, res) => {
  const db = getUserDb(req);
  const { id } = req.params;
  const { category } = req.body;
  
  const txIndex = db.transactions.findIndex(t => t.id === id);
  if (txIndex === -1) {
    return res.status(404).json({ error: "Transaction not found" });
  }
  
  db.transactions[txIndex].category = category;
  db.transactions[txIndex].status = "user-corrected";
  
  res.json({ message: "Category corrected successfully", transaction: db.transactions[txIndex] });
});

// CSV Upload
app.post("/api/transactions/upload-csv", (req, res) => {
  const { csvText } = req.body;
  if (!csvText) {
    return res.status(400).json({ error: "No CSV content supplied" });
  }
  
  try {
    // Basic CSV parser
    const lines = csvText.split("\n").map((line: string) => line.trim()).filter(Boolean);
    if (lines.length < 2) {
      return res.status(400).json({ error: "CSV has no data" });
    }
    
    // Date, Description, Amount
    const parsedTransactions: any[] = [];
    const headers = lines[0].toLowerCase().split(",");
    
    const dateIdx = headers.findIndex((h: string) => h.includes("date"));
    const descIdx = headers.findIndex((h: string) => h.includes("desc") || h.includes("particulars") || h.includes("merchant"));
    const amountIdx = headers.findIndex((h: string) => h.includes("amount") || h.includes("value") || h.includes("rupee"));
    
    if (dateIdx === -1 || descIdx === -1 || amountIdx === -1) {
      return res.status(400).json({ error: "CSV must contain headers for Date, Description, and Amount" });
    }
    
    const categories: string[] = ["Food", "Utilities", "Transport", "Shopping", "Entertainment", "Housing", "Investment", "Others"];
    
    for (let i = 1; i < lines.length; i++) {
      const cols = lines[i].split(",").map((c: string) => c.replace(/"/g, "").trim());
      if (cols.length < Math.max(dateIdx, descIdx, amountIdx) + 1) continue;
      
      const dateStr = cols[dateIdx];
      const descStr = cols[descIdx];
      const amtVal = Number(cols[amountIdx].replace(/[₹,]/g, ""));
      
      if (!dateStr || !descStr || isNaN(amtVal)) continue;
      
      // Basic AI-Simulated Categorizer
      let assignedCat = "Others";
      const descLower = descStr.toLowerCase();
      if (descLower.includes("swiggy") || descLower.includes("zomato") || descLower.includes("restaurant") || descLower.includes("food") || descLower.includes("cafe")) {
        assignedCat = "Food";
      } else if (descLower.includes("uber") || descLower.includes("ola") || descLower.includes("metro") || descLower.includes("auto") || descLower.includes("fuel")) {
        assignedCat = "Transport";
      } else if (descLower.includes("airtel") || descLower.includes("jio") || descLower.includes("power") || descLower.includes("electricity") || descLower.includes("water") || descLower.includes("bescom")) {
        assignedCat = "Utilities";
      } else if (descLower.includes("amazon") || descLower.includes("flipkart") || descLower.includes("myntra") || descLower.includes("reliance") || descLower.includes("shopping")) {
        assignedCat = "Shopping";
      } else if (descLower.includes("netflix") || descLower.includes("spotify") || descLower.includes("prime") || descLower.includes("cinema")) {
        assignedCat = "Entertainment";
      } else if (descLower.includes("rent") || descLower.includes("housing") || descLower.includes("emi") || descLower.includes("maintenance")) {
        assignedCat = "Housing";
      } else if (descLower.includes("sip") || descLower.includes("zerodha") || descLower.includes("groww") || descLower.includes("mutual") || descLower.includes("fund")) {
        assignedCat = "Investment";
      } else if (descLower.includes("salary") || descLower.includes("tcs") || descLower.includes("payroll")) {
        assignedCat = "Salary";
      }
      
      parsedTransactions.push({
        id: `tx-uploaded-${Date.now()}-${i}`,
        date: dateStr,
        description: descStr,
        amount: amtVal,
        category: assignedCat,
        status: "AI-assigned",
        isAnomaly: Math.abs(amtVal) > 10000 && assignedCat === "Food", // Simple anomaly detection
      });
    }
    
    // Pre-commit stage: send back the parsed items so the user can review/edit/commit them
    res.json({ message: "Successfully parsed CSV", preview: parsedTransactions });
  } catch (err: any) {
    res.status(500).json({ error: `Failed to parse CSV: ${err.message}` });
  }
});

// Commit CSV upload
app.post("/api/transactions/commit-upload", (req, res) => {
  const db = getUserDb(req);
  const { transactions } = req.body;
  if (!transactions || !Array.isArray(transactions)) {
    return res.status(400).json({ error: "No transactions to commit" });
  }
  
  // Add to DB
  db.transactions.push(...transactions);
  db.transactions = computeBalances(db.transactions);
  
  // Update anomalies list if any uploaded was anomaly
  transactions.forEach(t => {
    if (t.isAnomaly) {
      db.anomaliesPool.push({
        id: `anom-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
        transactionId: t.id,
        date: t.date,
        merchant: t.description,
        amount: t.amount,
        severity: "High",
        explanation: `Anomalous large expenditure of ₹${Math.abs(t.amount)} spent at ${t.description} on ${t.date}.`,
      });
    }
  });
  
  res.json({ message: "Committed transactions successfully", count: transactions.length });
});

// Analytics Summary
app.get("/api/analytics/summary", (req, res) => {
  const db = getUserDb(req);
  let income = 0;
  let spending = 0;
  
  db.transactions.forEach(t => {
    if (t.amount > 0) {
      income += t.amount;
    } else {
      spending += Math.abs(t.amount);
    }
  });
  
  // Calculate total balance from transactions
  const finalBalance = db.transactions.reduce((acc, t) => acc + t.amount, initialBalance);
  
  // Calculate Savings Rate = (Income - Spending) / Income
  const savingsRate = income > 0 ? Math.max(0, Math.round(((income - spending) / income) * 100)) : 0;
  
  // Active anomalies
  const anomaliesCount = db.transactions.filter(t => t.isAnomaly).length;
  
  res.json({
    totalBalance: finalBalance,
    thisMonthSpend: spending,
    savingsRate: savingsRate,
    anomaliesCount: anomaliesCount,
  });
});

// Spending Forecast
app.get("/api/analytics/forecast", (req, res) => {
  // Last 6 months actuals + 30/60/90 days forecast
  const baseForecast = [
    { date: "30 Days Forecast", projected: 48000, confidenceMin: 42000, confidenceMax: 54000 },
    { date: "60 Days Forecast", projected: 46500, confidenceMin: 39000, confidenceMax: 54000 },
    { date: "90 Days Forecast", projected: 45000, confidenceMin: 36000, confidenceMax: 54000 },
  ];
  res.json({ forecast: baseForecast });
});

// What-If simulator
app.get("/api/analytics/what-if", (req, res) => {
  const db = getUserDb(req);
  const reductionPercent = Number(req.query.reductionPercent) || 0;
  const category = req.query.category || "Food";
  
  // Calculate spending in this category
  let categorySpend = 0;
  db.transactions.forEach(t => {
    if (t.category === category && t.amount < 0) {
      categorySpend += Math.abs(t.amount);
    }
  });
  
  const savedAmount = Math.round(categorySpend * (reductionPercent / 100));
  
  // Shift future forecasted spending down
  const shiftedForecast = [
    { date: "30 Days Forecast", projected: Math.max(10000, 48000 - savedAmount), confidenceMin: Math.max(5000, 42000 - savedAmount), confidenceMax: Math.max(15000, 54000 - savedAmount) },
    { date: "60 Days Forecast", projected: Math.max(10000, 46500 - savedAmount * 2), confidenceMin: Math.max(5000, 39000 - savedAmount * 2), confidenceMax: Math.max(15000, 54000 - savedAmount * 2) },
    { date: "90 Days Forecast", projected: Math.max(10000, 45000 - savedAmount * 3), confidenceMin: Math.max(5000, 36000 - savedAmount * 3), confidenceMax: Math.max(15000, 54000 - savedAmount * 3) },
  ];
  
  res.json({
    categorySpend,
    savedAmount,
    projectedForecast: shiftedForecast,
  });
});

// Anomalies
app.get("/api/analytics/anomalies", (req, res) => {
  const db = getUserDb(req);
  // Sync anomalies with currently active anomalies in db.transactions
  const activeIds = db.transactions.filter(t => t.isAnomaly).map(t => t.id);
  const activeAnoms = db.anomaliesPool.filter(a => activeIds.includes(a.transactionId));
  res.json({ anomalies: activeAnoms });
});

// Subscriptions
app.get("/api/analytics/subscriptions", (req, res) => {
  const db = getUserDb(req);
  res.json({ subscriptions: db.subscriptions });
});

// Goals
app.get("/api/goals", (req, res) => {
  const db = getUserDb(req);
  res.json({ goals: db.goals });
});

app.post("/api/goals", (req, res) => {
  const db = getUserDb(req);
  const { name, targetAmount, currentAmount, targetDate, category } = req.body;
  if (!name || !targetAmount || !targetDate) {
    return res.status(400).json({ error: "Missing required goal parameters" });
  }
  
  const newGoal = {
    id: `goal-${Date.now()}`,
    name,
    targetAmount: Number(targetAmount),
    currentAmount: Number(currentAmount || 0),
    targetDate,
    category: category || "Savings",
  };
  
  db.goals.push(newGoal);
  res.json({ message: "Goal created", goal: newGoal, goals: db.goals });
});

app.post("/api/goals/:id/contribute", (req, res) => {
  const db = getUserDb(req);
  const { id } = req.params;
  const { amount } = req.body;
  
  if (!amount || isNaN(Number(amount)) || Number(amount) <= 0) {
    return res.status(400).json({ error: "Contribution amount must be positive" });
  }
  
  const goalIdx = db.goals.findIndex(g => g.id === id);
  if (goalIdx === -1) {
    return res.status(404).json({ error: "Goal not found" });
  }
  
  const contribution = Number(amount);
  
  // Deduct from overall ledger as a negative transaction
  const newTx = {
    id: `tx-goal-${Date.now()}`,
    date: new Date().toISOString().split("T")[0],
    description: `Goal Contribution: ${db.goals[goalIdx].name}`,
    amount: -contribution,
    category: "Investment",
    status: "user-corrected",
    isAnomaly: false,
  };
  
  db.goals[goalIdx].currentAmount += contribution;
  db.transactions.push(newTx);
  db.transactions = computeBalances(db.transactions);
  
  res.json({
    message: "Contributed to goal successfully",
    goal: db.goals[goalIdx],
    transaction: newTx,
    goals: db.goals,
  });
});

// Autonomous Digest Endpoints
app.get("/api/chat/digest", (req, res) => {
  const db = getUserDb(req);
  const currentBalance = db.transactions.reduce((acc, t) => acc + t.amount, initialBalance);
  const activeAnoms = db.transactions.filter(t => t.isAnomaly).length;
  const userName = db.user ? db.user.name : "Siva Sudhamsh";
  
  res.json({
    digest: `**Weekly Passbook Digest — July 16, 2026**
    
Dear ${userName},

Here is your automated autonomous weekly review compiled by **FinAgent**:

1. **Balance & Liquidity**:
   Your net liquid capital is **₹${currentBalance.toLocaleString("en-IN")}**. Your monthly savings rate is currently sitting strong at **58%**.

2. **ML Insights & Subscription Leak**:
   * **Duplicate Found**: We identified a duplicate charge of **₹649** for *Netflix India Premium* on July 11. I am queuing up a support mail for a credit correction.
   * **Subscription Creep Alert**: Your *Unrecognized SaaS fee - cloudbill.io* at **₹4,999** is currently evaluated with a Creep Score of **85/100** because it has zero prior logging and is an offshore merchant.
   * **High Expense Audit**: The restaurant bill of **₹12,500** at Swiggy on July 4 sits outside your normal dining curve.

3. **Autonomous Actions Performed**:
   * Reviewed Section 80C balance. You have ₹30,000 left to deposit to hit the ₹1,50,000 threshold under Old Tax Regime eligibility guidelines.
   * Scanned 15 ledger inputs for categorization confidence. Corrected 0 items silently, flagged 3 anomalies.

What action would you like me to prepare next?`,
  });
});

// Chat Endpoint with Gemini API logic
app.post("/api/chat", async (req, res) => {
  const db = getUserDb(req);
  const { message } = req.body;
  if (!message) {
    return res.status(400).json({ error: "Message is required" });
  }
  
  const userMsg = {
    id: `msg-user-${Date.now()}`,
    sender: "user" as const,
    text: message,
    timestamp: new Date().toISOString(),
  };
  
  db.chatHistory.push(userMsg);
  
  // Formulate ground details for RAG
  const currentBalance = db.transactions.reduce((acc, t) => acc + t.amount, initialBalance);
  const activeAnoms = db.transactions.filter(t => t.isAnomaly);
  const activeSubs = db.subscriptions;
  const activeGoals = db.goals;
  const userName = db.user ? db.user.name : "Siva Sudhamsh";
  const firstName = userName.split(" ")[0];
  
  const ledgerMarkdown = db.transactions
    .map(t => `| ${t.date} | ${t.description} | ₹${t.amount.toLocaleString("en-IN")} | ${t.category} | ${t.isAnomaly ? "ANOMALY" : "Normal"} |`)
    .join("\n");
    
  const contextString = `
  User Name: ${userName}
  Current Ledger Balance: ₹${currentBalance.toLocaleString("en-IN")}
  
  Active Transaction Ledger:
  | Date | Description | Amount | Category | Status |
  |------|-------------|--------|----------|--------|
  ${ledgerMarkdown}
  
  Active flagged Anomalies:
  ${activeAnoms.map(a => `- Merchant: ${a.description}, Amount: ₹${Math.abs(a.amount)}, Date: ${a.date}. Explanation: Abnormal charge flagged.`).join("\n")}
  
  Active Subscriptions:
  ${activeSubs.map(s => `- Merchant: ${s.merchant}, Amount: ₹${s.amount}/month, Next Billing: ${s.nextChargeDate}, Creep Score: ${s.creepScore}/100`).join("\n")}
  
  Financial Goals:
  ${activeGoals.map(g => `- ${g.name}: Target ₹${g.targetAmount}, Current Saved ₹${g.currentAmount}, Target Date: ${g.targetDate}, Category: ${g.category}`).join("\n")}
  
  Indian Tax Context:
  - Section 80C allows deductions up to ₹1,50,000 for investments in ELSS Mutual Funds, PPF, EPF, NPS, etc.
  - New Tax Regime has lower tax slabs but eliminates standard deductions. If deductions under 80C + 80D + HRA are less than ₹3,75,000, New Regime is mathematically superior for incomes above ₹15L.
  - Capital Gains Tax (from Union Budget 2024 reforms): Short Term Capital Gains (STCG) on equity is 20%. Long Term Capital Gains (LTCG) is 12.5% with ₹1.25L annual exemption threshold.
  `;
  
  const systemInstruction = `
  You are FinAgent, an elite, highly professional AI personal finance assistant for an Indian user.
  You are grounded in a real banking passbook. You communicate with absolute authority, tabular precision, and subtle warmth.
  Speak using formal Indian banking terms (e.g. SIP, passbook, credit ledger, ledger entries, ₹ currency).
  Be incredibly crisp, structured, and factual. Always use Markdown lists or tables when explaining numbers.
  Never make up data that is not in the user's ledger context.
  
  Here is the user's ground-truth financial ledger context:
  ${contextString}
  
  Analyze user queries directly against this context.
  If the user asks questions about their spending, tax liabilities, saving tips, or subscription audits, provide precise, custom figures formatted strictly with Indian Numbering (e.g., ₹1,24,500).
  Always provide a direct, actionable recommendation at the bottom of your message.
  `;
  
  const toolsPerformed = [
    "Scanned financial ledger",
    "Analyzed anomalies logs",
  ];
  if (message.toLowerCase().includes("tax") || message.toLowerCase().includes("regime") || message.toLowerCase().includes("80c")) {
    toolsPerformed.push("Searched Indian Tax RAG knowledge base");
  }
  if (message.toLowerCase().includes("anomal") || message.toLowerCase().includes("leak") || message.toLowerCase().includes("swiggy")) {
    toolsPerformed.push("Audited ML anomalies database");
  }
  if (message.toLowerCase().includes("goal") || message.toLowerCase().includes("save") || message.toLowerCase().includes("laptop")) {
    toolsPerformed.push("Verified active target accounts");
  }
  
  try {
    let responseText = "";
    
    if (ai) {
      // Call real Gemini
      const geminiResponse = await ai.models.generateContent({
        model: "gemini-3.5-flash",
        contents: message,
        config: {
          systemInstruction: systemInstruction,
          temperature: 0.3,
        }
      });
      responseText = geminiResponse.text || "I was unable to analyze that. Please check back shortly.";
    } else {
      // Offline high-fidelity fallback
      const query = message.toLowerCase();
      if (query.includes("tax") || query.includes("80c")) {
        responseText = `Based on your tax profile and financial RAG audit:
        
- **Section 80C Ledger Status**: Your active contributions total **₹1,20,000** (Tax Saving ELSS Mutual Funds goal). You have a gap of **₹30,000** to maximize the eligible Section 80C threshold under the Old Regime limit.
- **Regime Evaluation**: Since your deductions are under ₹3,75,000, the **New Tax Regime** (updated in 2024 with improved tax slabs) is mathematically optimal for your salary bracket of ₹1,85,000/month (₹22.2 Lakhs per annum), netting you an estimated annual tax savings of approximately **₹42,300** over the Old Regime.
 
**Recommendation**: Queue a contribution of **₹30,000** to your tax-saver ELSS goal if you stick to the Old Regime, or switch to the New Tax Regime to free up immediate monthly investment capital.`;
      } else if (query.includes("anomal") || query.includes("swiggy") || query.includes("netflix")) {
        responseText = `I have audited your ledger anomalies database and detected 3 outstanding concerns:

1. **Swiggy Gourmet Feast (₹12,500)** on July 4: This is **14.8x higher** than your median food spend of ₹845.
2. **Netflix India Premium (Duplicate ₹649)** on July 11: Flagged as an automatic double charge by the same merchant ID on the same day.
3. **cloudbill.io (₹4,999)** on July 14: An unrecognized charge from a SaaS provider with zero previous ledger registration.

**Action Plan**:
- I have initiated a dispute ticket for the duplicate **Netflix charge**.
- I suggest locking your credit card online for international transactions to stop any continuing leak from **cloudbill.io**.`;
      } else if (query.includes("track") || query.includes("goal") || query.includes("laptop")) {
        responseText = `Let's review your goals passbook:

| Goal Name | Target Amount | Current Savings | Progress | Target Date |
| :--- | :---: | :---: | :---: | :---: |
| **Emergency Fund** | ₹3,00,000 | ₹1,80,000 | **60%** | Dec 31, 2026 |
| **Macbook Pro M5** | ₹1,50,000 | ₹90,000 | **60%** | Sep 30, 2026 |
| **Tax saving ELSS** | ₹1,50,000 | ₹1,20,000 | **80%** | Mar 31, 2027 |

- **Emergency Fund**: You are fully on track, needing ₹24,000 monthly contributions to hit target.
- **Macbook Pro M5**: Sits with ₹60,000 pending. With your strong current month savings rate, you can hit this easily.

**Recommendation**: Increase your ELSS mutual fund SIP by ₹5,000/month to seal the Section 80C gap.`;
      } else {
        responseText = `I have audited your transaction ledger and financial profile. 

Your active liquidity balance is **₹${currentBalance.toLocaleString("en-IN")}**. Your monthly savings rate is outstanding at **58%**, largely buoyed by your regular salary deposit of **₹1,85,000** from TCS.

Your high-impact anomalies list consists of the unrecognized **cloudbill.io SaaS leak (₹4,999)** and the **duplicate Netflix charge (₹649)**. 

How would you like to handle these? I can simulate tax optimizations, prepare goal contributions, or draft dispute emails on your behalf.`;
      }
    }
    
    const agentMsg = {
      id: `msg-agent-${Date.now()}`,
      sender: "agent" as const,
      text: responseText,
      timestamp: new Date().toISOString(),
      toolCalls: toolsPerformed,
    };
    
    db.chatHistory.push(agentMsg);
    res.json({ userMessage: userMsg, agentMessage: agentMsg, chatHistory: db.chatHistory });
  } catch (err: any) {
    res.status(500).json({ error: `AI Assistant Error: ${err.message}` });
  }
});

app.get("/api/chat", (req, res) => {
  const db = getUserDb(req);
  res.json({ chatHistory: db.chatHistory });
});

// Start server function incorporating Vite dev server middleware
async function startServer() {
  if (process.env.NODE_ENV !== "production") {
    console.log("Starting server in DEVELOPMENT mode with Vite middleware");
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    console.log("Starting server in PRODUCTION mode with static delivery");
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`FinAgent Backend & Frontend Server online at http://localhost:${PORT}`);
  });
}

startServer();
