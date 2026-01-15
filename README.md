# Livelihood Sentinel 🛡️
AI-powered early warning system for livelihood & financial risk.

**Inversion:** Traditional finance apps track past spending.  
**Livelihood Sentinel flags “risk impacts” early** by converting policy, market, inflation, and weather signals into **personalized alerts + survival protocols**.

---

## Problem
People across diverse livelihoods (students, salaried users, farmers, gig workers, investors) often suffer losses during income shocks because:
- risk information is fragmented and technical
- there is no visibility into *financial runway*
- alerts are not personalized to their assets & liabilities

---

## Solution
Livelihood Sentinel acts as a **Financial Immune System**:
- Calculates **Survival Runway** (days of financial safety left)
- Converts signals into **actionable risk alerts**
- Generates **voice-ready briefings** for accessibility
- Supports **multi-livelihood profiles** (Student mode + Family/Farmer mode)

---

## Key Features
- **Survival Runway & Burn Rate** dashboard  
- **Personalized Alerts** (severity + urgency + “why this applies”)  
- **Gemini-based Explanation Engine** (plain-language summaries)  
- **Advice Protocols** (non-predictive, action-oriented)  
- **Voice Briefing Script** (TTS-ready accessibility layer)  
- **Student Mode**: daily limits + overspend risk  
- **Family/Farmer Mode**: crop risk + emergency planning  

> Note: Some alerts are simulated for demo clarity using official-source patterns.

---

## Tech Stack
- **Frontend:** Streamlit (Python)
- **AI:** Google Gemini
- **Database:** Firebase Firestore
- **Voice:** gTTS (TTS-ready)
- **Data Sources:** RSS feeds (e.g., SEBI/RBI) + official-source patterns

---

## Process Flow
User Input → Runway Calculation → Signal Filtering → Alert Generation → Advice + Voice Briefing

---

## Architecture
Streamlit UI → Rule Engine (Runway & Risk) → Gemini (Explanation) → Firestore (Storage) → Voice Layer

---

## Run Locally
1. Clone repo:
git clone https://github.com/akshaykumarhudedmani/livelihood-sentinel.git

cd livelihood-sentinel

2.Install dependencies:
pip install -r requirements.txt

4. Add secrets:
Create .streamlit/secrets.toml:
GEMINI_API_KEY = "YOUR_KEY"

Run the app:
streamlit run app.py

🔗 Links: 

Demo Video: https://youtu.be/4Q14jqTG-Ww?si=zcVkwy57DVy1KPLY

MVP: https://livelihood-sentinel.streamlit.app/

👥 Team Z
1.Akshay Kumar
2.Preetham B S

Lisense: MIT
