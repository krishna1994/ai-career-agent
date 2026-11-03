# 🎯 Live Test Instructions

The simulation has proven the AI logic works correctly end-to-end. Here's how to run a **real test** on LinkedIn.

---

## ⚠️ Before You Start

**IMPORTANT SAFETY MEASURES:**
1. Set `dryRun = True` for your first run (the bot will NOT submit applications, just log what it would do).
2. Set `maxApplicationsPerRun = 1` to limit to just one job.
3. Have your LinkedIn 2FA/CAPTCHA ready in case LinkedIn asks for verification.

---

## 📋 Step-by-Step Setup

### Step 1: Get an OpenAI API Key
1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)
5. **Cost:** ~$0.005 per job application with GPT-4o

### Step 2: Configure the Bot
Open `config.py` and update:

```python
# --- AI ENHANCEMENTS ---
use_ai_features = True
ai_api_key = "sk-YOUR_ACTUAL_KEY_HERE"  # Paste your OpenAI key
ai_model = "gpt-4o"
min_ats_score = 4  # Only apply to jobs scoring 4 or 5
enable_resume_tailoring = True

# LinkedIn Credentials
email = "your_linkedin_email@example.com"
password = "your_linkedin_password"

# Job Search Preferences (Customize for your search)
location = ["Ireland", "Remote"]
keywords = ["Senior Software Engineer", "AI Engineer", "Python Developer"]
experienceLevels = ["Mid-Senior level", "Director"]
datePosted = ["Past Week"]
jobType = ["Full-time"]
remote = ["Remote", "Hybrid"]
salary = ["$80,000+"]

# SAFETY SETTINGS
dryRun = True  # ⚠️ KEEP THIS TRUE FOR FIRST TEST
maxApplicationsPerRun = 1  # Only process 1 job
```

### Step 3: Upload Your Resume to LinkedIn
1. Log into LinkedIn manually
2. Go to Settings → Job Application Settings
3. Upload your resume as your default resume
4. Make sure it's set as your "preferred" resume

### Step 4: Run the Bot (Dry Run)
```bash
cd AI_Career_Agent
python linkedin.py
```

**What will happen:**
- Chrome will open and log into LinkedIn
- The bot will search for jobs matching your criteria
- For each job, it will:
  - Extract the job description
  - Send it + your resume to OpenAI for scoring
  - If score ≥ 4, it will log: `🧪 DRY RUN - Would apply to this job: [URL]`
  - Save everything to `data/applications.db`

### Step 5: Review the Results
Check the database:
```bash
sqlite3 data/applications.db "SELECT job_title, company, ats_score, ats_reason FROM applications"
```

Or check the text log:
```bash
type data\Applied Jobs DATA - YYYYMMDD.txt
```

### Step 6: Go Live (Optional)
If you're satisfied with the dry run results:
1. Open `config.py`
2. Change `dryRun = False`
3. Run `python linkedin.py` again
4. The bot will now **actually submit** applications

---

## 🔍 What to Expect

### Example Output:
```
🤖 Thanks for using AI Career Agent.
🌐 Bot will run in Chrome browser and log in Linkedin for you.
🔄 Trying to log in Linkedin...
✅ Apply urls are created successfully

Category: Senior Software Engineer, Location: Ireland, Applying 47 jobs.

🔍 Step 1: AI is analyzing job...
✅ AI Score: 5/5 - Perfect match for Python, FastAPI, and OpenAI experience
🎯 Decision: High Match! Proceeding...
✍️ Step 2: Tailoring resume...
🧪 DRY RUN - Would apply to this job: https://linkedin.com/jobs/12345
```

---

## 💰 Cost Estimate

For your profile (Senior Software Engineer with AI experience):
- **Dry Run:** $0 (no API calls if you keep `use_ai_features = False` initially)
- **Live Run with AI (1 job):** ~$0.005
- **Live Run with AI (100 jobs):** ~$0.50

---

## 🛑 Troubleshooting

### "Could not log in Linkedin"
- LinkedIn detected automation. Try:
  1. Log in manually first in Chrome
  2. Use `chromeProfilePath` in config to reuse your session

### "AI API Key not configured"
- You forgot to replace `"YOUR_API_KEY_HERE"` with your actual key

### "Rate Limit Error"
- You hit OpenAI's rate limit. Wait 1 minute or upgrade your API tier.

---

## ✅ Success Criteria

After the dry run, you should see:
1. ✅ Chrome opened and logged into LinkedIn
2. ✅ Jobs were found and scored by AI
3. ✅ High-scoring jobs were marked as "Would apply"
4. ✅ Database contains entries with `ats_score` and `ats_reason`

---

## 📞 Need Help?

If you encounter issues, check:
- `data/Applied Jobs DATA - YYYYMMDD.txt` for detailed logs
- `data/applications.db` for structured data
- The terminal output for error messages