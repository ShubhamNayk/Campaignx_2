# 🚀 CampaignX — Multi-Agent AI Marketing Automation

CampaignX is a Streamlit-powered marketing automation platform built for the **CampaignX hackathon**. It uses **5 AI agents** to segment audiences, draft emails, send campaigns, monitor performance, and iteratively optimize email content — all from a single dashboard.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red) ![LLM](https://img.shields.io/badge/LLM-Llama_3.3_70B-purple) ![Observability](https://img.shields.io/badge/Observability-Langfuse-orange)

---

## ✨ Features

- **AI-Powered Audience Segmentation** — LLM dynamically generates scoring logic based on the campaign brief and ranks customers.
- **AI Copywriting** — Generates email drafts with subject lines, body content, CTA placement, and strategy reasoning.
- **Human-in-the-Loop Review** — Preview, edit, approve, or reject campaign content before launch.
- **One-Click Campaign Launch** — Schedule emails via the CampaignX API with quick send or custom time in IST.
- **Real-Time Monitoring** — Fetch open rate and click rate analytics for any campaign.
- **Iterative Optimization Loop** — AI generates 5 optimized email variants using different strategies: Urgency, Curiosity, Social Proof, Emotional, and Data-Driven.
- **Comparison Dashboard** — Side-by-side performance comparison after each optimization round with full history table.
- **Langfuse Observability** — All agent calls are traced for debugging, monitoring, and evaluation.

---

## 🏗️ Architecture

```text
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
|-----------|------------|
| Frontend | Streamlit |
| LLM | Groq - Llama 3.3 70B |
| API Execution | Dynamic API Executor |
| Observability | Langfuse |
| Language | Python 3.10+ |

---

## 📁 Project Structure

```text
Campaignx_2/
├── app.py                  # Main Streamlit app: Input, Review, Monitor, Pick Variant, Compare
├── tools.py                # Dynamic API executor
├── monitoring.py           # Langfuse setup
├── requirements.txt        # Dependencies
├── .streamlit/
│   └── secrets.toml        # API keys - not committed
└── agents/
    ├── __init__.py
    ├── segmentation.py     # Segmentation Agent
    ├── copywriter.py       # Copywriter Agent and Optimizer Agent
    ├── execution.py        # Execution Agent
    └── reporting.py        # Reporting Agent
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Groq API Key](https://console.groq.com)
- [Langfuse Account](https://cloud.langfuse.com) for observability
- CampaignX Hackathon API Key

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

Make sure `.streamlit/secrets.toml` is added to `.gitignore`.

### Run Locally

```bash
streamlit run app.py
```

---

## 📖 How It Works

### 1. 📋 Input — Create Campaign

Enter a campaign brief, for example:

> "Launch XDeposit for female senior citizens and optimize for open and click rates."

Set the maximum audience size. The AI agents will:

- Fetch the customer cohort from the CampaignX API
- Generate scoring logic based on the brief
- Rank and select the most relevant customers
- Draft the first email campaign

### 2. ✍️ Review & Send

Preview the AI-generated email, edit it if needed, and schedule the campaign with quick send or custom time in IST.

### 3. 📊 Monitor

Fetch campaign performance data, including open rate and click rate. View campaign health and decide whether optimization is needed.

### 4. ⚡ Optimize

Click **Generate 5 Optimized Emails**. The AI creates 5 variants using different strategies:

| Variant | Strategy |
|---------|----------|
| V1 | 🔥 Urgency & Scarcity |
| V2 | 🔮 Curiosity & Mystery |
| V3 | 🤝 Social Proof & Trust |
| V4 | 💙 Personal & Emotional |
| V5 | 📊 Data-Driven & Logical |

### 5. 🎯 Pick & Launch

Select the best variant, schedule it, and send it to the selected audience.

### 6. 📈 Compare

A dedicated comparison page shows:

- Previous vs current open rate
- Previous vs current click rate
- Delta arrows for improvement or decline
- Verdict: improved, partially improved, or not improved
- Full optimization history table across all rounds

From here, you can **optimize again** or stop.

---

## ✅ Rulebook Alignment

| Requirement | Status |
|------------|--------|
| Web app UI | ✅ Streamlit dashboard |
| Natural-language campaign brief | ✅ Supported |
| Customer cohort API usage | ✅ Implemented |
| AI-based segmentation | ✅ Implemented |
| AI email generation | ✅ Implemented |
| Human approval before launch | ✅ Implemented |
| Campaign execution through API | ✅ Implemented |
| Report fetching | ✅ Implemented |
| Open/click analysis | ✅ Implemented |
| Optimization loop | ✅ Implemented |

---

## ☁️ Deploy to Streamlit Cloud

1. Push code to GitHub. Make sure `secrets.toml` is in `.gitignore`.
2. Go to [share.streamlit.io](https://share.streamlit.io).
3. Click **New app** and select your repository.
4. Set the main file path to `app.py`.
5. Add secrets in **Advanced Settings**.
6. Click **Deploy**.

---

## 👥 Team

Built by Team **[Your Team Name]** for the CampaignX hackathon.

---

## 📄 License

This project is for educational and hackathon purposes.
