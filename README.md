# 🤖 AI Career Agent

The AI Career Agent is a professional-grade, autonomous job application system that combines high-speed browser automation with deep AI intelligence to maximize your interview conversion rate.

## 🌟 Core Value Proposition
Unlike traditional bots that "spray and pray," the AI Career Agent acts as a strategic partner. It doesn't just apply to jobs; it analyzes them, scores your fit, tailors your professional narrative, and tracks your entire funnel.

---

## 🚀 Key Features

### 1. Deterministic Skill Gap Analysis
Powered by a custom state-machine, the agent extracts required skills from Job Descriptions and classifies them into three buckets:
- **Existing:** Skills explicitly listed in your CV.
- **Supported:** Skills mentioned in your experience prose.
- **Gaps:** Missing skills that need to be addressed.

### 2. AI-Powered Precision
- **ATS Scoring:** Every job is scored (1-5) using LLMs before any action is taken.
- **Surgical Tailoring:** The AI rewrites specific bullet points in your resume to bridge identified skill gaps.
- **Contextual Answering:** Generates professional, truthful answers to custom application questions based on your actual experience.

### 3. Modular Efficiency Modes
Choose your strategy based on your current goal:
- **SPEED:** Maximum volume, zero AI cost.
- **BALANCED:** Smart filtering with AI scoring. (Recommended)
- **PRECISION:** Deep analysis, tailored resumes, and company research.

### 4. Professional Infrastructure
- **SQLite Tracking:** A structured database (`data/applications.db`) replaces messy text logs.
- **Stealth Automation:** Uses `selenium-stealth` and human-like delays to protect your account.
- **Cost Control:** Real-time tracking of API spend to prevent surprises.

---

## 🛠️ Quick Start

1. **Install Dependencies:**
   ```bash
   pip install selenium webdriver_manager selenium-stealth pyyaml requests
   ```

2. **Configure:**
   Edit `config_advanced.py` with your LinkedIn credentials and OpenAI API key.

3. **Run:**
   ```bash
   python linkedin.py
   ```

---

## 📚 Documentation
For detailed instructions, please refer to the guides in this directory:
- **[START_HERE.md](./START_HERE.md)** - Quick start and index.
- **[USER_GUIDE.md](./USER_GUIDE.md)** - Full setup and configuration.
- **[AI_INTEGRATION_GUIDE.md](./AI_INTEGRATION_GUIDE.md)** - Technical deep-dive into AI features.
- **[SKILL_GAP_ANALYSIS.md](./SKILL_GAP_ANALYSIS.md)** - How the matching logic works.
- **[EFFICIENCY_MODES_GUIDE.md](./EFFICIENCY_MODES_GUIDE.md)** - Strategy guide for modes.
- **[PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md)** - Steps to go live.

---

## ⚠️ Disclaimer
This tool is for educational and productivity purposes. Please use it responsibly and adhere to the Terms of Service of the platforms you interact with.