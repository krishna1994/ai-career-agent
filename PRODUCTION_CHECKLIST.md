# ✅ Production Checklist - What You Need to Run This Live

This is a step-by-step checklist of everything you need to provide to run AI Career Agent on real LinkedIn jobs.

---

## 🔑 1. LinkedIn Credentials

**What you need:**
- Your LinkedIn email address
- Your LinkedIn password

**Where to add it:**
Open `config.py` and update:
```python
email = "your_actual_linkedin_email@example.com"
password = "your_actual_linkedin_password"
```

**Security Note:** 
- Never commit this file to a public repository after adding your password.
- Consider using a Chrome profile instead (see Advanced Setup below).

---

## 🤖 2. OpenAI API Key (Required for AI Features)

**What you need:**
- An OpenAI API key (starts with `sk-...`)

**How to get it:**
1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key

**Where to add it:**
Open `config.py` and update:
```python
ai_api_key = "sk-proj-YOUR_ACTUAL_KEY_HERE"
```

**Cost Estimate:**
- ~$0.005 per job with GPT-4o
- Applying to 100 jobs ≈ $0.50

**Alternative (Free but less accurate):**
If you don't want to use AI features, set:
```python
use_ai_features = False
```
The bot will still work but without ATS scoring and resume tailoring.

---

## 📄 3. Your Resume

**What you need:**
- Your resume uploaded to LinkedIn as your default resume

**How to verify:**
1. Log into LinkedIn manually
2. Go to Settings → Job Application Settings
3. Ensure your latest resume is uploaded and set as "preferred"

**Note:** The bot will use whatever resume LinkedIn has on file. Make sure it's up to date.

---

## 🎯 4. Job Search Preferences

**What you need:**
Your job search criteria (location, keywords, experience level, etc.)

**Where to configure:**
Open `config.py` and update the job search section:

```python
# Example:
location = ["Ireland", "Remote", "Europe"]
keywords = ["Senior Software Engineer", "AI Engineer", "Python Developer", "Backend Engineer"]
experienceLevels = ["Mid-Senior level", "Director"]
datePosted = ["Past Week"]
jobType = ["Full-time"]
remote = ["Remote", "Hybrid"]
salary = ["$80,000+"]
```

**Tip:** Start narrow (e.g., just one location + one job title) for your first run to test.

---

## ⚙️ 5. Safety Settings (Critical)

**What you need:**
Confirmation that you want to start with a **dry run**.

**Where to configure:**
Open `config.py` and ensure the safety settings are set to:

```python
dryRun = True  # ⚠️ KEEP THIS TRUE FOR FIRST RUN
maxApplicationsPerRun = 1  # Only process 1 job to test
```

**What this does:**
- The bot will browse jobs and score them
- It will NOT actually submit applications
- You can review the results before going live

---

## 🧪 6. Test Run Confirmation

**What will happen during a dry run:**
1. Chrome will open on your screen
2. The bot will log into LinkedIn
3. It will search for jobs matching your criteria
4. It will extract each job description
5. It will score it using AI (if enabled)
6. It will log: `🧪 DRY RUN - Would apply to this job: [URL]`
7. It will save the result to `data/applications.db`

**Expected duration:** 2-3 minutes for a single job.

---

## 📋 Summary: What to Provide Before Going Live

1. ✅ Your LinkedIn credentials (or use the Chrome profile method below)
2. ✅ Your OpenAI API key (or confirm you want to run without AI)
3. ✅ Your job search preferences
4. ✅ A completed dry-run test with no errors

---

## 🚀 Advanced Setup (Optional)

### Option A: Use a Chrome Profile (Recommended for Security)

Instead of storing your password in `config.py`, you can use your existing Chrome session:

1. Open Chrome and type `chrome://version/` in the address bar
2. Copy the "Profile Path" (e.g., `C:\Users\<you>\AppData\Local\Google\Chrome\User Data\Default`)
3. Update `config.py`:
   ```python
   chromeProfilePath = r"C:\Users\<you>\AppData\Local\Google\Chrome\User Data\Default"
   email = ""  # Leave empty
   password = ""  # Leave empty
   ```

### Option B: Docker Setup (Cleanest)

If you prefer to run everything in a container:
```bash
cd AI_Career_Agent
docker-compose up --build
```

---

## ❓ What Happens After the Test?

After the dry run, you'll see:
1. A log file: `data/Applied Jobs DATA - YYYYMMDD.txt`
2. A database: `data/applications.db`
3. Terminal output showing the AI score and decision

If you're satisfied, you can then:
1. Set `dryRun = False`
2. Set `maxApplicationsPerRun` to your preferred limit (e.g. 50)
3. Run again to start applying for real

---

## 🆘 Need Help?

If you encounter any issues during setup, check:
- `USER_GUIDE.md` for detailed installation instructions
- `LIVE_TEST_INSTRUCTIONS.md` for a step-by-step testing guide
- `AI_INTEGRATION_GUIDE.md` for AI feature troubleshooting