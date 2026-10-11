# 🏦 NexusBank AI — Multi-Agent Banking System

A **simulated real-time banking application** powered by multiple AI agents that collaborate to handle diverse banking operations — from account inquiries to fraud detection and loan processing.

Built with **Google Gemini**, **LangGraph**, and **FastAPI**.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-blueviolet)
![Gemini](https://img.shields.io/badge/Google-Gemini-orange?logo=google)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green?logo=fastapi)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────┐
│              Web UI (Chat Interface)             │
│         HTML / CSS / JavaScript                  │
└──────────────────────┬──────────────────────────┘
                       │  HTTP POST /api/chat
┌──────────────────────▼──────────────────────────┐
│               FastAPI Server                     │
│         Session Management + API Layer           │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│         LangGraph StateGraph Workflow            │
│                                                  │
│  ┌─────────────────────────────────────────────┐ │
│  │         🤖 Supervisor / Orchestrator         │ │
│  │    Intent Classification → Agent Routing     │ │
│  └────┬──────────────┬──────────────┬──────────┘ │
│       │              │              │            │
│  ┌────▼─────┐  ┌─────▼─────┐  ┌────▼──────┐    │
│  │ 🏦 Cust. │  │ 🛡️ Risk/  │  │ 💳 Credit │    │
│  │  Agent   │  │   Fraud   │  │  / Loan   │    │
│  │          │  │  Agent    │  │   Agent   │    │
│  └────┬─────┘  └─────┬─────┘  └────┬──────┘    │
│       │              │              │            │
│  ┌────▼──────────────▼──────────────▼──────┐    │
│  │       Simulated Banking APIs (Tools)     │    │
│  │    In-memory data store with 5 customers │    │
│  └──────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

### Multi-Agent Design

| Agent | Responsibility | Tools |
|-------|----------------|-------|
| **Supervisor** | Intent classification, request routing | Route-to-agent decision |
| **Customer Agent** | Account info, balances, transactions | `get_customer_profile`, `get_account_balance`, `get_account_details`, `get_transaction_history`, `search_customer_by_name` |
| **Risk/Fraud Agent** | Fraud detection, risk scoring | `analyze_transaction_fraud`, `get_customer_risk_score`, `get_suspicious_transactions`, `report_suspicious_activity` |
| **Credit/Loan Agent** | Loan eligibility, EMI, products | `check_loan_eligibility`, `get_loan_status`, `get_loan_products`, `calculate_emi` |

---

## 🎯 Working Use Cases

| # | Use Case | Agent | Example Query |
|---|----------|-------|---------------|
| 1 | **Account Balance Check** | Customer | "Show me Rajesh Kumar's account balance" |
| 2 | **Transaction History** | Customer | "Show recent transactions for account ACC001" |
| 3 | **Fraud Detection** | Risk | "Are there suspicious transactions on Amit Patel's accounts?" |
| 4 | **Loan Eligibility** | Credit | "Is Priya Sharma eligible for a personal loan of 5 lakhs?" |
| 5 | **Loan Status** | Credit | "What is the status of loan LOAN001?" |
| 6 | **EMI Calculation** | Credit | "Calculate EMI for a home loan of 50 lakhs at 8.5% for 20 years" |
| 7 | **Risk Assessment** | Risk | "What is the risk score for customer CUST003?" |
| 8 | **Customer Search** | Customer | "Find customer Sneha Reddy" |

---

## 🚀 Setup & Run

### Prerequisites

- Python 3.10+
- Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### 1. Clone & Navigate

```bash
cd banking-multi-agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
copy .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 5. Run the Application

```bash
python run.py
```

### 6. Open in Browser

Navigate to **http://localhost:8000**

---

## 📁 Project Structure

```
banking-multi-agent/
├── run.py                        # Entry point
├── requirements.txt              # Dependencies
├── .env.example                  # Environment template
├── app/
│   ├── main.py                   # FastAPI server + API endpoints
│   ├── config.py                 # Configuration management
│   ├── data/
│   │   └── bank_data.py          # Simulated banking data (5 customers, 7 accounts, 20 txns, 5 loans)
│   ├── tools/
│   │   ├── customer_tools.py     # Customer/Account API tools
│   │   ├── risk_tools.py         # Fraud/Risk API tools
│   │   └── credit_tools.py       # Loan/Credit API tools
│   ├── agents/
│   │   ├── state.py              # LangGraph shared state definition
│   │   ├── supervisor.py         # Supervisor/Orchestrator agent
│   │   ├── customer.py           # Customer banking agent
│   │   ├── risk.py               # Risk & fraud agent
│   │   └── credit.py             # Credit & loan agent
│   └── graph/
│       └── workflow.py           # LangGraph StateGraph definition
└── static/
    ├── index.html                # Chat UI
    ├── style.css                 # Styling
    └── app.js                    # Frontend logic
```

---

## 🔧 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **LLM** | Google Gemini (gemini-2.0-flash) | Natural language understanding + tool calling |
| **Orchestration** | LangGraph (StateGraph) | Multi-agent workflow with conditional routing |
| **Agent Framework** | LangChain Core | Tool definitions, message types, LLM interface |
| **Backend** | FastAPI + Uvicorn | REST API, session management, static serving |
| **Frontend** | Vanilla HTML/CSS/JS | Premium chat interface with glassmorphism design |
| **Data** | In-memory Python dicts | Simulated banking database |

---

## 🧠 How It Works

1. **User sends a message** via the chat interface
2. **FastAPI** receives the request and passes it to the LangGraph workflow
3. **Supervisor Agent** analyzes the intent using Gemini and decides which specialized agent should handle it
4. **Conditional routing** directs the request to the chosen agent (Customer, Risk, or Credit)
5. **Specialized agent** uses Gemini with bound tools in a **ReAct loop** (Reason → Act → Observe) to:
   - Call simulated banking APIs
   - Process the results
   - Generate a natural language response
6. **Response flows back** through the graph → API → UI with agent attribution

### LangGraph Workflow

```
START → Supervisor → [conditional edge] → Customer Agent → END
                                        → Risk Agent    → END
                                        → Credit Agent  → END
                                        → FINISH (direct response) → END
```

---

## 📊 Simulated Data

The system includes realistic banking data:

- **5 Customers** — Rajesh Kumar, Priya Sharma, Amit Patel, Sneha Reddy, Vikram Singh
- **7 Accounts** — Savings and Current accounts with realistic balances
- **20 Transactions** — Including legitimate and suspicious transactions
- **5 Loans** — Active, closed, and overdue loans
- **5 Loan Products** — Home, Personal, Car, Business, Education loans

> Amit Patel (CUST003) has intentionally suspicious transactions for fraud detection demos.

---

