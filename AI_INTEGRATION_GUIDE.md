# 🤖 AI Integration Guide

This guide explains the AI-powered features built into AI Career Agent.

---

## 🎯 Features

The bot includes three major AI enhancements:

### 1. **ATS Scoring** 
Before applying to a job, the bot uses AI to score how well your resume matches the job description (1-5 scale). Jobs below your threshold are automatically skipped.

### 2. **Resume Tailoring**
The bot can dynamically rewrite your resume to emphasize skills and experiences relevant to each specific job.

### 3. **AI-Powered Question Answering**
Instead of relying on a static YAML file, the bot uses AI to generate contextual answers to application questions based on your resume and the job description.

---

## ⚙️ Configuration

All AI settings are in `config.py`:

```python
# --- AI ENHANCEMENTS ---
use_ai_features = True  # Master switch for all AI features
ai_api_key = "YOUR_API_KEY_HERE"  # Your OpenAI API key
ai_model = "gpt-4o"  # Model to use (gpt-4o, gpt-4-turbo, etc.)
min_ats_score = 3  # Minimum score (1-5) to apply
enable_resume_tailoring = True  # Tailor resume for each job
resumeText = ""  # REQUIRED for AI features to activate: paste your plain-text resume here
                 # (separate from the PDF/DOCX uploaded to LinkedIn/Indeed via resumePath)
```

> Both `linkedin.py` and `indeed.py` gate the entire AI step on `use_ai_features` being
> `True` **and** `resumeText` being non-empty. If either is missing, the bot behaves
> exactly as it did before AI support was added (no API calls, no scoring, no skipping).

### Getting an API Key

1. **OpenAI:** Visit [platform.openai.com](https://platform.openai.com/api-keys) and create an API key.
2. **Anthropic (Claude):** Visit [console.anthropic.com](https://console.anthropic.com/) for Claude API access.
   - Note: If using Claude, you'll need to modify `ai_engine.py` to use Anthropic's API format.

---

## 📊 New Database Tracking

Applications are now logged to `data/applications.db` (SQLite) instead of just text files.

### Database Schema
```sql
CREATE TABLE applications (
    id INTEGER PRIMARY KEY,
    job_id TEXT,
    job_title TEXT,
    company TEXT,
    location TEXT,
    url TEXT,
    ats_score INTEGER,
    ats_reason TEXT,
    status TEXT,  -- "Applied", "Skipped", "Failed"
    date_applied TEXT,
    tailored_resume_used BOOLEAN
)
```

### Viewing Your Data
You can query the database using any SQLite client:
```bash
sqlite3 data/applications.db "SELECT * FROM applications WHERE ats_score >= 4"
```

Or use Python:
```python
from db_manager import DBManager
db = DBManager()
print(db.get_stats())  # Get application statistics
```

---

## 🚀 How It Works

**AI features now work for BOTH `linkedin.py` and `indeed.py`.** The same `AIEngine`/`SkillAnalyzer`/`DBManager` are used by both bots.

### Workflow with AI Enabled

1. **Job Discovery:** Bot finds "Easy Apply" jobs on LinkedIn/Indeed (same as before).
2. **🆕 ATS Scoring:** Bot extracts the job description from the page and sends it + your plain-text resume (`config.resumeText`, set via `config.py` or the GUI's Settings tab) to the AI.
   - AI returns a score (1-5) and reasoning.
   - If `score < min_ats_score`, the job is skipped and logged to the database with status "Skipped".
   - This step is entirely skipped (bot behaves exactly as before) if `use_ai_features` is `False` or `resumeText` is empty.
3. **🆕 Skill Gap Check (Optional):** If the job passes the ATS score gate, `SkillAnalyzer` compares skills mentioned in the JD against your resume text; jobs with more than `max_skill_gaps` missing skills are also skipped.
4. **Application:** Bot fills out the form (resume upload/selection, phone number, custom questions).
5. **🆕 AI Question Answering:** For any text question with no match in `additionalQuestions.yaml`/`my_answers.yaml`, the bot falls back to asking the AI for an answer based on your resume text + the job description.
6. **🆕 Database Logging:** Applied/Skipped/Dry Run outcomes (with ATS score + reason) are saved to `data/applications.db`, in addition to the usual `data/Applied Jobs DATA...txt` log.

> Note: `enable_resume_tailoring` currently only produces rewritten resume *text* (via `tailor_resume()`) -- it is not yet automatically converted into a new PDF/DOCX file and re-uploaded to LinkedIn/Indeed's file input. The existing `resumePath`/`preferredCv` resume used for the actual file upload is unaffected.

---

## 💰 Cost Considerations

Using AI features incurs API costs:
- **OpenAI GPT-4o:** ~$0.005 per job (scoring + tailoring + 2-3 questions)
- **OpenAI GPT-4-turbo:** ~$0.01 per job
- **Anthropic Claude 3.5 Sonnet:** ~$0.003 per job

**Example:** Applying to 100 jobs with GPT-4o ≈ $0.50

### Cost Optimization Tips
1. Set `enable_resume_tailoring = False` if you don't need it (saves ~40% of API calls).
2. Use `min_ats_score = 4` to only apply to high-fit jobs (reduces total applications).
3. Use `dryRun = True` first to test without spending money.

---

## 🧪 Testing the Integration

### Step 1: Dry Run with AI
```python
# In config.py
use_ai_features = True
ai_api_key = "sk-..."  # Your real API key
dryRun = True  # Don't actually submit applications
min_ats_score = 3
```

Run the bot:
```bash
python linkedin.py
```

Check the output. You should see:
```
🤖 ATS Score: 4/5 - Strong match for React skills
🧪 DRY RUN - Would apply to this job: https://...
```

### Step 2: Check the Database
```bash
sqlite3 data/applications.db "SELECT job_title, ats_score, status FROM applications LIMIT 10"
```

### Step 3: Live Run
Once satisfied, set `dryRun = False` and run again.

---

## 🛠️ Troubleshooting

### "AI API Key not configured"
- Make sure you've replaced `"YOUR_API_KEY_HERE"` in `config.py` with your actual API key.

### "AI Engine Error: 401 Unauthorized"
- Your API key is invalid or expired. Generate a new one.

### "AI Engine Error: 429 Rate Limit"
- You've hit the API rate limit. Wait a few minutes or upgrade your API plan.

### ATS Scoring / Resume Tailoring Not Working
- Ensure `use_ai_features = True` **and** `resumeText` is non-empty in `config.py` (or via the
  GUI's Settings tab) -- both are required, not just `enable_resume_tailoring`.
- Confirm the bot can extract the job description from the page: if `getJobDescription()`
  (linkedin.py) or `_get_job_description()` (indeed.py) returns an empty string for a given
  posting, the AI step is skipped for that job only (logged via `displayWarnings`).

---

## 📈 Future Enhancements

Potential additions for the next version:
- **Dashboard:** A web UI to visualize your application stats from the database.
- **Follow-up Reminders:** Automated emails to hiring managers 7 days after applying.
- **Interview Prep:** AI-generated interview questions based on the job description.

---

## 🤝 Contributing

If you improve the AI integration, please consider contributing back to the project!

---

## ⚠️ Disclaimer

Using AI to tailor resumes and answer questions is a gray area. Always review AI-generated content before submitting. The bot is a tool to assist you, not replace your judgment.