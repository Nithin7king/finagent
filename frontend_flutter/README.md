# MYFY.AI — Flutter Mobile Application

Autonomous Personal Finance & Wealth Management cross-platform mobile application built with **Flutter (Dart 3)**.

---

## 📱 Features

- **Authentication**: JWT login, registration with monthly income, and persistent session tokens.
- **Dashboard**: Live net balance, monthly outflow, savings rate %, IsolationForest anomaly counter, spending trend area chart, and recent passbook transactions.
- **Passbook Ledger**: Full transaction table with merchant search, category filters (`Food`, `Shopping`, `Housing`, `Transport`, etc.), type toggles, manual entry, and password-protected PDF bank statement imports (HDFC, ICICI, SBI).
- **Spending Insights & Analytics (3-in-1)**:
  1. *Anomalies*: Flagged IsolationForest transactions with severity chips and explanations.
  2. *Subscriptions*: Detected recurring bills, intervals, cadence, and subscription creep risk scoring.
  3. *What-If Simulator*: Interactive category spend reduction slider calculating compounding monthly savings.
- **Savings Goals**: Goal cards with progress percentage, saved vs target metrics, target dates, creation modal, and instant fund deposit modal.
- **AI Financial Advisor Chat**: Multi-turn conversational interface powered by FastAPI LangGraph orchestrator, suggestion chips, reasoning/tool-call badges, and weekly digests.
- **KYC Verification**: Multi-step PAN verification and Government DigiLocker Aadhaar OTP authentication.
- **Design System**: Signature dark navy banking palette (`#0A0F1D`), Indian Rupee formatting (`₹`), glassmorphic stat cards, and rotated Indian banking StampBadges.

---

## 🚀 Running the Mobile App

Ensure the backend is running (`python run.py` from repository root).

### 1. Install Dependencies
```bash
cd frontend_flutter
flutter pub get
```

### 2. Run on Chrome / Web
```bash
flutter run -d chrome
```

### 3. Run on Android Emulator
Ensure Android emulator is running, then:
```bash
flutter run -d android
```
*(The app automatically points to `http://10.0.2.2:5000` on Android)*.

### 4. Run on iOS Simulator
```bash
flutter run -d ios
```
