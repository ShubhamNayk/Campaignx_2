# 🚀 CampaignX — Multi-Agent AI Marketing Automation

CampaignX is a Streamlit-powered marketing automation platform that uses **5 AI agents** to segment audiences, draft emails, send campaigns, monitor performance, and iteratively optimize email content — all from a single dashboard.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red) ![LLM](https://img.shields.io/badge/LLM-Llama_3.3_70B-purple) ![Observability](https://img.shields.io/badge/Observability-Langfuse-orange)

---

## ✨ Features

- **AI-Powered Audience Segmentation** — LLM dynamically generates scoring logic based on your campaign brief and ranks customers.
- **AI Copywriting** — Generates email drafts with subject lines, body content, and strategy reasoning.
- **One-Click Campaign Launch** — Schedule emails via API with quick send (1 min) or custom time (IST).
- **Real-Time Monitoring** — Fetch live open rate and click rate analytics for any campaign.
- **Iterative Optimization Loop** — AI generates 5 optimized email variants using different strategies (Urgency, Curiosity, Social Proof, Emotional, Data-Driven). Pick one, send it, and compare results.
- **Comparison Dashboard** — Side-by-side performance comparison after each optimization round with full history table.
- **Langfuse Observability** — All agent calls are traced for debugging and monitoring.

---

## 🏗️ Architecture

```
User → [Streamlit UI]
            │
            ├── Segmentation Agent → Scores & ranks customers
            ├── Copywriter Agent   → Writes initial email
            ├── Execution Agent    → Sends campaign via API
            ├── Reporting Agent    → Fetches open/click metrics
            └── Optimizer Agent    → Generates 5 optimized variants
                    │
                    └── Loop: Pick → Send → Compare → Optimize Again
```

**Tech Stack:**
| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| LLM | Groq (Llama 3.3 70B) |
| API Execution | Dynamic API Executor (LLM reads API docs → formulates requests) |
| Observability | Langfuse |
| Language | Python 3.10+ |

---

## 📁 Project Structure

```
campaignx_v2/
├── app.py                  # Main Streamlit app (5 pages: Input, Review, Monitor, Pick Variant, Compare)
├── tools.py                # Dynamic API executor (LLM-powered HTTP request builder)
├── monitoring.py           # Langfuse setup
├── requirements.txt        # Dependencies
├── .streamlit/
│   └── secrets.toml        # API keys (not committed)
└── agents/
    ├── __init__.py
    ├── segmentation.py     # Segmentation Agent — scores customers with AI-generated logic
    ├── copywriter.py       # Copywriter Agent — drafts emails & Optimizer Agent — generates 5 variants
    ├── execution.py        # Execution Agent — sends campaigns via API
    └── reporting.py        # Reporting Agent — fetches campaign analytics
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Groq API Key](https://console.groq.com)
- [Langfuse Account](https://cloud.langfuse.com) (for observability)
- Campaign API access (Hackathon API Key)

### Installation

```bash
git clone https://github.com/ShubhamNayk/Campaignx_2.git
cd Campaignx_2
pip install -r requirements.txt
```

### Configuration

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "your-groq-api-key"
HACKATHON_API_KEY = "your-hackathon-api-key"
LANGFUSE_PUBLIC_KEY = "your-langfuse-public-key"
LANGFUSE_SECRET_KEY = "your-langfuse-secret-key"
LANGFUSE_HOST = "https://us.cloud.langfuse.com"
```

### Run Locally

```bash
streamlit run app.py
```

---

## 📖 How It Works

### 1. 📋 Input — Create Campaign
Enter a campaign brief (e.g., *"Launch XDeposit for female senior citizens"*) and set the max audience size. AI agents will:
- Fetch all customers from the database
- Generate a scoring formula based on your brief
- Rank and select the top customers
- Draft the first email

### 2. ✍️ Review & Send
Preview the AI-drafted email, rewrite if needed, and schedule the campaign (quick 1-minute send or custom time in IST).

### 3. 📊 Monitor
Fetch real-time open rate and click rate. See a health banner and decide whether to optimize.

### 4. ⚡ Optimize (Loop)
Click "Generate 5 Optimized Emails" — the AI creates 5 variants with different strategies:
| Variant | Strategy |
|---------|----------|
| V1 | 🔥 Urgency & Scarcity |
| V2 | 🔮 Curiosity & Mystery |
| V3 | 🤝 Social Proof & Trust |
| V4 | 💙 Personal & Emotional |
| V5 | 📊 Data-Driven & Logical |

### 5. 🎯 Pick & Launch
Select the best variant, schedule it, and send to the same audience.

### 6. 📈 Compare
A dedicated comparison page shows:
- Previous vs Current rates (side-by-side)
- Delta arrows (▲ improvement / ▼ decline)
- Verdict (both improved / partial / no improvement)
- Full optimization history table across all rounds

From here, you can **optimize again** (loops back to step 4) or stop.

---

## ☁️ Deploy to Streamlit Cloud

1. Push code to GitHub (make sure `secrets.toml` is in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select your repo → set main file path to `app.py`
4. Add secrets in **Advanced Settings** (paste your TOML keys)
5. Click **Deploy**


## 📄 License

This project is for educational and hackathon purposes.
