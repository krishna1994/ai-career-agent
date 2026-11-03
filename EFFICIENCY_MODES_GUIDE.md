# ⚡ Efficiency Modes Guide - Choose Your Strategy

AI Career Agent supports **4 efficiency modes** so you can balance speed, AI cost, and application quality. Each mode is optimized for a different goal.

---

## 🎯 Quick Comparison

| Mode | Speed | Quality | AI Cost | Best For |
|:---|:---:|:---:|:---:|:---|
| **SPEED** | ⚡⚡⚡⚡⚡ | ⭐⭐ | $0 | High-volume job search, entry-level roles |
| **BALANCED** | ⚡⚡⚡ | ⭐⭐⭐⭐ | $0.50/100 jobs | Most users, mid-level roles |
| **PRECISION** | ⚡ | ⭐⭐⭐⭐⭐ | $2/100 jobs | Senior roles, FAANG, competitive markets |
| **CUSTOM** | Variable | Variable | Variable | Advanced users who want full control |

---

## 🚀 Mode 1: SPEED

**Goal:** Apply to as many jobs as possible in the shortest time.

### Features Enabled:
- ✅ Browser Automation
- ✅ Database Logging
- ✅ Stealth Mode
- ❌ AI Scoring (skipped for speed)
- ❌ Skill Gap Analysis
- ❌ Resume Tailoring
- ❌ Human Delays (faster but riskier)

### Performance:
- **Speed:** ~30-40 applications per hour
- **Cost:** $0 (no AI calls)
- **Success Rate:** 5-10% (spray and pray)

### When to Use:
- You're applying to 500+ jobs
- Entry-level or junior roles where competition is high
- You have a strong, general-purpose resume that doesn't need tailoring
- You're okay with a low response rate but want maximum reach

### Configuration:
```python
# In config_advanced.py
EFFICIENCY_MODE = "SPEED"
```

---

## ⚖️ Mode 2: BALANCED (Recommended)

**Goal:** Smart filtering with moderate speed. Best ROI for most users.

### Features Enabled:
- ✅ Browser Automation
- ✅ Database Logging
- ✅ AI Scoring (1-5 scale)
- ✅ Skill Gap Analysis (deterministic)
- ✅ AI Form Filling
- ✅ Stealth Mode
- ✅ Human Delays
- ❌ Resume Tailoring (too slow)
- ❌ Company Research

### Performance:
- **Speed:** ~10-15 applications per hour
- **Cost:** ~$0.50 per 100 jobs
- **Success Rate:** 15-25% (intelligent filtering)

### When to Use:
- You're a mid-level professional (3-7 years experience)
- You want to avoid wasting time on low-match jobs
- You have a budget for AI but want to keep costs low
- You're applying to 50-200 jobs total

### Configuration:
```python
# In config_advanced.py
EFFICIENCY_MODE = "BALANCED"
```

---

## 🎯 Mode 3: PRECISION

**Goal:** Maximum quality. Only apply to jobs where you're a near-perfect match.

### Features Enabled:
- ✅ Browser Automation
- ✅ Database Logging
- ✅ AI Scoring (1-5 scale)
- ✅ Skill Gap Analysis (deterministic)
- ✅ AI Resume Tailoring (surgical rewrites)
- ✅ AI Form Filling
- ✅ ATS Vendor Detection
- ✅ Company Research (funding, size, culture)
- ✅ Salary Gap Analysis
- ✅ Automated Follow-ups
- ✅ Interview Prep (AI-generated questions)
- ✅ Funnel Analytics
- ✅ Stealth Mode
- ✅ Human Delays
- ✅ LaTeX PDF Resume Generation

### Performance:
- **Speed:** ~3-5 applications per hour
- **Cost:** ~$2 per 100 jobs
- **Success Rate:** 30-50% (highly targeted)

### When to Use:
- You're applying to senior/staff/principal roles
- You're targeting FAANG or top-tier startups
- You have a limited number of "dream jobs" (10-50 total)
- You want to maximize your interview rate, not application count
- You're willing to invest in AI to stand out

### Configuration:
```python
# In config_advanced.py
EFFICIENCY_MODE = "PRECISION"
```

---

## 🛠️ Mode 4: CUSTOM

**Goal:** Full control. Mix and match features to create your own strategy.

### How It Works:
Set `EFFICIENCY_MODE = "CUSTOM"` and then enable/disable individual features:

```python
EFFICIENCY_MODE = "CUSTOM"

# Example: "Smart Speed" - Fast but with AI scoring
ENABLE_AI_SCORING = True
ENABLE_SKILL_GAP_ANALYSIS = True
ENABLE_AI_RESUME_TAILORING = False  # Skip this for speed
ENABLE_AI_FORM_FILLING = True
ENABLE_COMPANY_RESEARCH = False
ENABLE_HUMAN_DELAYS = False  # Faster but riskier
```

### When to Use:
- You've tested the other modes and want to optimize further
- You have specific requirements (e.g., "I want AI scoring but no resume tailoring")
- You're experimenting with different strategies

---

## 📊 Feature Breakdown

### Core Features (All Modes)
| Feature | Description | Cost |
|:---|:---|:---:|
| Browser Automation | Selenium-based LinkedIn interaction | Free |
| Database Logging | SQLite tracking of all applications | Free |
| Stealth Mode | Avoid bot detection | Free |

### AI Features (Balanced & Precision)
| Feature | Description | Cost per Job |
|:---|:---|:---:|
| AI Scoring | LLM scores your fit (1-5) | $0.002 |
| Skill Gap Analysis | Deterministic skill extraction | Free |
| AI Form Filling | Answers custom questions | $0.003 |
| AI Resume Tailoring | Rewrites resume for each job | $0.005 |

### Advanced Features (Precision Only)
| Feature | Description | Cost per Job |
|:---|:---|:---:|
| Company Research | Funding, size, culture lookup | $0.001 |
| ATS Vendor Detection | Identify Workday, Greenhouse, etc. | Free |
| Salary Gap Analysis | Compare your expectations vs posting | $0.001 |
| Interview Prep | Generate likely interview questions | $0.003 |
| Automated Follow-ups | Send messages after X days | Free |

---

## 💰 Cost Examples

### Scenario 1: Entry-Level Developer (SPEED Mode)
- **Goal:** Apply to 500 jobs
- **Mode:** SPEED
- **Time:** ~15 hours
- **Cost:** $0
- **Expected Interviews:** 25-50

### Scenario 2: Mid-Level Engineer (BALANCED Mode)
- **Goal:** Apply to 100 jobs
- **Mode:** BALANCED
- **Time:** ~8 hours
- **Cost:** $0.50
- **Expected Interviews:** 15-25

### Scenario 3: Senior Engineer Targeting Top-Tier Companies (PRECISION Mode)
- **Goal:** Apply to 30 dream jobs
- **Mode:** PRECISION
- **Time:** ~8 hours
- **Cost:** $0.60
- **Expected Interviews:** 10-15

---

## 🎛️ How to Switch Modes

1. Open `config_advanced.py`
2. Change the `EFFICIENCY_MODE` variable:
   ```python
   EFFICIENCY_MODE = "BALANCED"  # or "SPEED", "PRECISION", "CUSTOM"
   ```
3. Save the file
4. Run the bot: `python linkedin.py`

The bot will automatically display your active configuration on startup.

---

## 🧪 Recommended Testing Path

1. **Start with BALANCED + DRY_RUN:**
   ```python
   EFFICIENCY_MODE = "BALANCED"
   DRY_RUN = True
   MAX_APPLICATIONS_PER_RUN = 5
   ```
   Run this to see how the AI scores your profile against real jobs.

2. **If you get high scores (4-5), try SPEED:**
   Your resume is already strong. You don't need AI tailoring.

3. **If you get low scores (1-2), switch to PRECISION:**
   You need surgical tailoring to bridge skill gaps.

4. **Once satisfied, go live:**
   ```python
   DRY_RUN = False
   ```

---

## ⚠️ Important Notes

- **LinkedIn Limits:** Regardless of mode, do not exceed 200 applications per day to avoid account flags.
- **Cost Control:** Set `MAX_AI_COST_PER_RUN` to prevent runaway API costs.
- **Mode Switching:** You can change modes between runs. The database tracks which mode was used for each application.

---

## 🆘 Troubleshooting

**"I'm in PRECISION mode but it's too slow"**
→ Switch to BALANCED or create a CUSTOM mode with only the features you need.

**"I'm in SPEED mode but getting no interviews"**
→ Your resume might need tailoring. Try BALANCED to see your AI scores first.

**"AI costs are too high"**
→ Switch to `gpt-4o-mini` or `gpt-3.5-turbo` in the config. Or use SPEED mode.

**"I want X feature from PRECISION but Y feature from SPEED"**
→ Use CUSTOM mode and enable only the features you want.