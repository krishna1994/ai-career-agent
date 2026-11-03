# 🚀 Welcome to AI Career Agent

This project is an AI-powered automation tool designed to help you find and apply for "Easy Apply" jobs on LinkedIn with high precision.

---

## ⚡ Quick Start (3-Minute Setup)

If you want to get the bot running as quickly as possible, follow these steps:

### 1. Install Dependencies
Open your terminal and run:
```bash
pip install selenium webdriver_manager selenium-stealth pyyaml requests
```

### 2. Configure Your Account
Open `config.py` and fill in:
- `email` & `password`: Your LinkedIn credentials.
- `ai_api_key`: Your OpenAI API key (required for AI scoring and tailoring).
- `location` & `keywords`: What you are looking for (e.g., `["Ireland"]`, `["AI Engineer"]`).

### 3. Run a Safe Test (Dry Run)
**Crucial:** Ensure `dryRun = True` in `config.py` so you don't accidentally apply to jobs while testing.
```bash
python linkedin.py
```

---

## 📚 Detailed Documentation

I have provided three detailed guides to help you master the bot:

1. **[USER_GUIDE.md](./USER_GUIDE.md)** 📖
   - Full installation instructions.
   - Detailed explanation of every setting in `config.py`.
   - Troubleshooting common errors.

2. **[AI_INTEGRATION_GUIDE.md](./AI_INTEGRATION_GUIDE.md)** 🤖
   - How the ATS Scoring works.
   - How the AI tailors your resume.
   - Cost estimates for using the OpenAI API.

3. **[LIVE_TEST_INSTRUCTIONS.md](./LIVE_TEST_INSTRUCTIONS.md)** 🎯
   - A personalized step-by-step checklist for your first live run.
   - How to verify the results in the database.

---

## 🛠️ Core Features at a Glance

| Feature | What it does | Benefit |
| :--- | :--- | :--- |
| **ATS Scoring** | AI scores your resume vs Job Description | Stop wasting time on low-match jobs |
| **Resume Tailoring** | AI rewrites your CV for each job | Higher chance of passing HR filters |
| **AI Form Filling** | AI answers custom application questions | No more manual typing for every app |
| **SQLite Tracking** | Logs every app to a database | Professional tracking of your job hunt |
| **Stealth Mode** | Mimics human browser behavior | Reduces risk of account detection |

---

## ⚠️ Final Reminder
**Use responsibly.** LinkedIn has strict limits on automation. We recommend applying to no more than **100-200 jobs per day** and always using `dryRun` first to verify your filters.