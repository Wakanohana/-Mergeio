# 🏢 Mergeio
### AI-Powered SME Acquisition Marketplace

[![Live Demo](https://img.shields.io/badge/🔗_Demo_Live-mergeio.io-brightgreen)](https://ma-plateforme-ma.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

> **Upload a P&L → Instant AI valuation score → Connect with buyers or sellers.**  
> The Bloomberg Terminal for SME acquisitions.

---

## 🎯 The Problem

The SME M&A market ($2T+/year in the US alone) is broken:

- Brokers still work **manually** — valuations take days or weeks
- Buyers have no **objective, data-driven** way to compare acquisition targets  
- Sellers can't get a credible valuation without paying a consultant **$5,000+**

## 💡 Our Solution

An AI-powered platform that analyzes a company's Profit & Loss in **seconds** and delivers:

| Output | Description |
|--------|-------------|
| 📊 **Health Score (0–100)** | Weighted across 4 financial criteria |
| 💰 **Valuation Range** | Standard EBITDA multiples methodology |
| 🏪 **Live Marketplace** | Filter, compare, and connect |

## 🚀 Live Demo

🔗 **[https://ma-plateforme-ma.onrender.com](https://ma-plateforme-ma.onrender.com)**

> _Demo credentials: `demo@mergeio.io` / `Demo1234`_

---

## ✨ Features

### 📊 AI P&L Analysis Engine
Upload any Excel P&L → instant financial health score with detailed breakdown across:
- Revenue growth & stability
- EBITDA margin quality
- Cash flow consistency  
- Debt / equity structure

### 🏪 Live Marketplace
- Filter by sector, score, region, asking price
- Company cards with financial snapshot
- Direct secure messaging with sellers

### 📈 Market Terminal
Real-time scoring dashboard — think Bloomberg Terminal for SME deals.

### 🔐 Secure Authentication
- Buyer / Seller role-based accounts
- JWT tokens + bcrypt password hashing
- Protected API endpoints

---

## 🏗️ Architecture

```
mergeio/
├── app_production.py      ← Flask server (REST API)
├── analyser_pl_v2.py      ← AI scoring & valuation engine
├── base_donnees.py        ← SQLite persistence layer
├── auth.py                ← JWT + bcrypt authentication
├── requirements.txt       ← Python dependencies
├── Procfile               ← Render.com deployment config
└── static/
    ├── login.html         ← Authentication page
    ├── dashboard_ma.html  ← P&L upload & analysis
    ├── marketplace_ma.html← Company listings & filters
    ├── terminal_ma.html   ← Live market terminal
    └── api_connector.js   ← Frontend ↔ Backend bridge
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python · Flask · SQLite → PostgreSQL ready |
| Frontend | Vanilla JS · HTML5 · CSS3 |
| AI/Data | Pandas · NumPy · Custom scoring algorithm |
| Auth | JWT · bcrypt |
| Deploy | Render.com · GitHub CI/CD |

---

## 🚀 Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/mergeio.git
cd mergeio

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env and add your JWT_SECRET_KEY

# 4. Launch the server
python app_production.py

# 5. Open in browser
# http://localhost:5000
```

---

## 📊 Business Model

| Revenue Stream | Details |
|----------------|---------|
| 💳 SaaS Subscriptions | Buyers: $99/mo · Sellers: $149/mo |
| 🤝 Transaction Fee | 1–2% of completed deal value |
| 📈 Premium Analytics | Sector benchmarks · Comparable deals |

### Market Opportunity

- 🇺🇸 US SME M&A market: **$2T+/year** (source: IBBA)
- Average broker commission: **8–12%** of deal value  
- Our platform fee: **1–2%** → **5× cheaper, 100× faster**

---

## 🗺️ Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1–7 | ✅ **Complete** | AI Engine · Dashboard · Marketplace · Terminal · API · Auth · Deployment |
| Phase 8 | 🔄 In Progress | PostgreSQL migration |
| Phase 9 | 📅 Planned | Buyer ↔ Seller messaging |
| Phase 10 | 📅 Planned | Stripe payment integration |
| Phase 11 | 📅 Planned | US market expansion |
| Phase 12 | 📅 Planned | Mobile application |

---

## 💼 For Investors

**Mergeio is raising a pre-seed round.**

- 📄 [One Pager](docs/one_pager.pdf)
- 📊 [Pitch Deck](docs/pitch_deck.pdf)
- 🔗 [Live Demo](https://ma-plateforme-ma.onrender.com)
- 📅 [Book a Meeting](https://calendly.com/YOUR_LINK)

---

## 📬 Contact

**Founder:** [Votre Nom]  
**Email:** contact@mergeio.io  
**LinkedIn:** [linkedin.com/in/votre-profil](https://linkedin.com/in/votre-profil)

---

*Built with Python, Flask, and a vision to democratize SME acquisitions.*  
*© 2026 Mergeio. All rights reserved.*
