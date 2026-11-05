# Enterprise Secure Mobile Application & Backend API

A production-ready, decoupled mobile application and backend architecture built with **Python**, **Flet (Flutter engine)**, **FastAPI**, and **MySQL 8.0**.

---

## 1. System Architecture

```
┌────────────────────────────────────────────────────────┐
│             Mobile Device (Android / iOS)              │
│       Python + Flet (Flutter UI Engine) Client         │
│   • Secure Token Storage (Keychain / EncryptedPrefs)   │
│   • Tabs: Masters, Transactions, Registers, Reports    │
│   • Dynamic Real-Time Operational Dashboard            │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTPS / TLS 1.3
                           │ JSON Payloads + Bearer JWT
                           ▼
┌────────────────────────────────────────────────────────┐
│              Backend Application Server                │
│             FastAPI + Pydantic + Uvicorn               │
│   • Rate Limiting & Cooldown Protection                │
│   • OTP Generation, Hashing & Verification Engine      │
│   • Role-Based Access Control (RBAC) & Audit Logs      │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
               │ SMS Delivery API         │ Connection Pooling
               ▼                          ▼
    ┌──────────────────────┐    ┌──────────────────────┐
    │ Third-Party Gateway  │    │    MySQL 8.0 DB      │
    │ (Twilio / AWS SNS)   │    │ (Private Subnet/VPC) │
    └──────────────────────┘    └──────────────────────┘
```

---

## 2. Directory Structure

```
secure_mobile_app/
├── .env.example              # Sample environment template
├── .env                      # Active runtime environment configuration
├── requirements.txt          # Python dependency specifications
├── README.md                 # Complete documentation & startup guide
│
├── database/
│   ├── schema.sql            # Full MySQL 8.0 production DDL schema
│   └── seed_data.sql         # Initial baseline demonstration seed data
│
├── backend/
│   ├── config.py             # Typed configuration loading from .env via Pydantic
│   ├── database.py           # Engine & scoped session management (MySQL + SQLite)
│   ├── models.py             # SQLAlchemy ORM models (Users, OTP, Masters, Invoices)
│   ├── schemas.py            # Pydantic validation & response serialization
│   ├── security.py           # JWT signing/decoding & Role-Based Access Control
│   ├── otp_service.py        # OTP lifecycle, rate limiting, hashing, and SMS dispatch
│   ├── main.py               # FastAPI application, routers & auto-seeding
│   ├── routers/
│   │   ├── auth.py           # /api/v1/auth (request-otp, verify-otp, refresh, me)
│   │   ├── masters.py        # /api/v1/masters (Customers, Vendors, Products)
│   │   ├── transactions.py   # /api/v1/transactions (Sales Invoices, Purchases)
│   │   ├── registers.py      # /api/v1/registers (Sales, Purchases, Stock Log)
│   │   ├── reports.py        # /api/v1/reports (P&L, Aging, Tax summaries)
│   │   └── dashboard.py      # /api/v1/dashboard (KPI summaries & revenue trends)
│   └── tests/
│       ├── test_auth.py      # OTP security, cooldown & lockout verification
│       └── test_masters_and_tx.py # Masters, Invoices, Stock & Dashboard tests
│
└── mobile/
    ├── config.py             # Mobile theme palette & API base URL
    ├── api_client.py         # Authenticated HTTP client with token handling
    ├── main.py               # Mobile application entry point (Flet UI)
    └── views/
        ├── login_view.py     # Phone entry & 6-digit OTP verification screen
        ├── dashboard_view.py # Dynamic dashboard with KPI cards & revenue charts
        ├── masters_view.py   # Masters directory (Customers, Vendors, Products)
        ├── transactions_view.py # Invoices & Bills creation & history
        ├── registers_view.py # Operational & audit registers with running totals
        └── reports_view.py   # P&L statement, Overdue Aging & Tax summaries
```

---

## 3. Quickstart & Setup Guide

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` and configure your credentials:
```bash
cp .env.example .env
```
*Note: In development mode, if Twilio credentials are blank, generated OTPs are printed directly to the backend terminal log for immediate testing.*

### Step 3: Run the Automated Test Suite
Verify that all unit and integration tests pass:
```bash
python -m pytest -p no:flet backend/tests
```

### Step 4: Start the Backend API Server
```bash
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
*Interactive Swagger documentation will be available at:* `http://127.0.0.1:8000/docs`

### Step 5: Launch the Mobile Application
In a separate terminal window:
```bash
cd mobile
python main.py
```

---

## 4. Mobile Application Features

| Section | Key Capabilities |
| :--- | :--- |
| **Authentication Flow** | • E.164 phone number input (e.g., `+14155552671`)<br>• 6-digit cryptographic OTP generation<br>• 60-second cooldown enforcement & attempt lockout protection<br>• Bearer JWT issuance and local session management |
| **Dynamic Dashboard** | • Real-time KPI summary cards (Revenue, Receivables, Low-Stock items, Cash balance)<br>• Interactive date filters (`Today`, `This Week`, `This Month`, `All Time`)<br>• Visual bar chart representing revenue performance<br>• Top selling products ranking |
| **Masters Tab** | • Sub-tabs for **Products**, **Customers**, and **Vendors**<br>• Live inventory indicators (`IN STOCK` vs `LOW STOCK`)<br>• Incremental search filter<br>• Modal dialogs to add new items or parties |
| **Transactions Tab** | • Filter invoices by payment status (`PAID` vs `UNPAID`)<br>• "New Transaction" dialog with live customer selection, line items, and tax calculation<br>• Automatic inventory deduction on sales invoices |
| **Registers Tab** | • **Sales Register**: Chronological list of issued invoices with tax breakdowns<br>• **Purchase Register**: Supplier bills and input tax credit credits<br>• **Stock Movement Log**: Inward/outward movement history with reference IDs |
| **Reports Tab** | • **Profit & Loss Statement**: Gross sales, Cost of Goods Sold, and Gross Profit Margin %<br>• **Aging Analysis**: Overdue receivables & payables categorized by 0-30, 31-60, and 60+ days<br>• **Tax Summary (GST/VAT)**: Output tax collected vs Input tax credit claimed |

---

## 5. Security Architecture

1. **Why No Direct MySQL Connection**:
   - Mobile applications can be easily decompiled (`apktool`/`jadx`). Storing MySQL credentials on a client exposes the entire database to unauthorized queries.
   - A direct connection exposes port 3306 to the internet, bypasses server-side validation and business rules, and rapidly exhausts MySQL connection pools when mobile devices sleep or drop connections.
2. **OTP Hardening**:
   - Uses `secrets.randbelow()` (CSPRNG) instead of predictable pseudo-random number generators.
   - OTPs are stored in the database as SHA-256 hashes; plaintext codes are never persisted.
   - Enforces 60-second resend cooldowns and limits verification to 3 failed attempts before permanent invalidation.
3. **OWASP Best Practices**:
   - SQLAlchemy parameterized queries eliminate SQL Injection vulnerabilities.
   - Strict Pydantic validation sanitizes all incoming payloads.
   - Short-lived JWT access tokens (15–30 min) paired with refresh tokens.
