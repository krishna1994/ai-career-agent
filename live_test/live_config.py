"""
Live Test Configuration
This file is used for real-world testing and should NOT be committed to version control.
"""

# ── Chrome Profile (Secure Method) ──
chromeProfilePath = r"C:\Users\krissing\AppData\Local\Google\Chrome\User Data\Default"

# ── Credentials (Leave empty when using Chrome Profile) ──
email = ""
password = ""

# ── AI Configuration ──
use_ai_features = True
ai_api_key = "YOUR_API_KEY_HERE"  # Replace with your actual OpenAI key
ai_model = "gpt-4o-mini"

# ── Job Search Preferences ──
location = ["Ireland", "Remote"]
keywords = ["Senior Software Engineer", "AI Engineer", "Python Developer"]
experienceLevels = ["Mid-Senior level", "Director"]
datePosted = ["Past Week"]
jobType = ["Full-time"]
remote = ["Remote", "Hybrid"]

# ── Safety Settings (DRY RUN) ──
dryRun = True  # ⚠️ KEEP THIS TRUE FOR TESTING
maxApplicationsPerRun = 1  # Only test 1 job

# ── AI Thresholds ──
min_ats_score = 3
max_skill_gaps = 5

# ── Display Settings ──
displayWarnings = True