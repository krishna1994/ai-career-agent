# AI Career Agent - bot configuration
# Edit the values below to match your job search. Do not commit this file
# after entering real credentials or API keys.

# --- AI settings ---
# Set to True to enable AI-powered scoring, tailoring, and answering
use_ai_features = False
# Your OpenAI or Anthropic API Key. Leave as "YOUR_API_KEY_HERE" to fall back
# to the local AI provider instead.
ai_api_key = "YOUR_API_KEY_HERE"
# Model to use (e.g., "gpt-4o", "claude-3-5-sonnet")
ai_model = "gpt-4o"
# Minimum ATS score (1-5) to apply. Jobs below this will be skipped.
min_ats_score = 3
# If True, the bot will attempt to tailor the resume for each job
enable_resume_tailoring = True
# Plain-text content of your resume, used ONLY for AI ATS scoring, resume
# tailoring, and AI-generated question answers (ai_engine.py / local_ai_
# provider.py). This is separate from the actual resume file uploaded to
# LinkedIn (see preferredCv / resumePath below) because the AI needs
# plain text and no PDF/DOCX parsing library is bundled. Leave empty to
# disable AI ATS scoring/tailoring for LinkedIn even if use_ai_features
# is True (the bot will skip the AI step and apply normally).
resumeText = ""

# --- Login / browser settings ---
# LinkedIn credentials
email = ""
password = ""

# Optional! Run browser in headless mode (no visible window). Works in background.
headless = False
# Optional! Chrome profile directory to reuse a logged-in session and avoid
# re-authenticating every run. Get this path from chrome://version/ or point
# it at a dedicated bot profile (recommended, avoids "SessionNotCreated"
# errors if your main Chrome window is already open).
chromeProfilePath = r""

# --- Job search criteria ---
# location you want to search the jobs - ex: ["Poland", "Singapore", "New York City Metropolitan Area"]
# continent locations: ["Europe", "Asia", "Australia", "NorthAmerica", "SouthAmerica", "Africa"]
# NOTE: LinkedIn's search-level location filter only narrows results when
# using a recognized continent name above, or a location string LinkedIn
# itself can geo-resolve via autocomplete (e.g. "Ireland", "Dublin,
# Ireland"). Generic/ambiguous values like "Remote" are NOT resolved by
# LinkedIn's search and will NOT filter results by country. Because of
# this, `allowedCountries` below is used as an additional, more reliable
# safety net that actually excludes jobs outside your target countries.
location = ["Europe", "Remote", "Ireland"]

# Countries you're actually willing to work in/relocate to. After
# LinkedIn returns search results, the bot reads each job posting's
# displayed location text (e.g. "London Area, United Kingdom") and SKIPS
# any job whose location doesn't contain one of these strings. This is
# what prevents "applying to any random country" when the search-level
# location filter above can't narrow things down precisely enough.
# Use country names as they'd appear on a LinkedIn job posting.
# Leave as an empty list [] to disable this filter entirely (not
# recommended - you'll get jobs from anywhere in the world).
allowedCountries = ["Ireland", "United Kingdom", "Remote"]
# keywords related with your job search
keywords = ["Software Engineer", "Python", "Developer", "AI"]
# job experience level - ex: ["Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"]
experienceLevels = ["Mid-Senior level", "Director"]
# job posted date - ex: ["Any Time", "Past Month", "Past Week", "Past 24 hours"] - select only one
datePosted = ["Past Week"]
# job type - ex: ["Full-time", "Part-time", "Contract", "Temporary", "Volunteer", "Intership", "Other"]
jobType = ["Full-time", "Part-time", "Contract"]
# remote preference - ex: ["On-site", "Remote", "Hybrid"]
remote = ["On-site", "Remote", "Hybrid"]
# Minimum salary tier - LinkedIn defines 9 fixed tiers (numbered 1-9
# internally). IMPORTANT: these are NOT literal USD amounts -- LinkedIn
# auto-resolves each tier to the LOCAL currency of wherever you're
# searching (e.g. tier 3 shows as "~€X,XXX+" for an Ireland/EU search,
# "~£X,XXX+" for a UK search, "~$X,XXX+" for a US search). The dollar
# labels below are just how LinkedIn's own UI happens to label them for
# a US-based search -- verified empirically: searching Ireland with tier
# 3 returned a job advertised at "€100K", not "$100K".
# ex: ["$40,000+", "$60,000+", "$80,000+", ... , "$200,000+"] - select only one
salary = ["$80,000+"]
# sort order - ex: ["Recent"] or ["Relevent"] - select only one
sort = ["Recent"]
# blacklist companies you don't want to apply to - ex: ["Apple", "Google"]
blacklistCompanies = []
# blacklist keywords in job title - ex: ["manager", ".Net"]
blackListTitles = []
# follow companies automatically after a successful application
followCompanies = False

# --- Resume / contact details ---
# If you have multiple CVs uploaded to LinkedIn, choose which one the bot
# should select (1 = first in the list, 2 = second, etc.)
preferredCv = 1
# Your phone number, used to auto-fill phone fields during application forms.
Phone = ""

# --- Debugging & safety ---
# Set to True to print verbose warning messages during a run.
displayWarnings = False
# If True, the bot will NOT submit any applications. Instead, it will
# navigate as usual but only log which jobs it *would* apply to.
dryRun = True
# Optional cap: stop after this many successful applications in one run.
# 0 = no limit. Example: 50 or 100 to avoid applying too many jobs in a
# single session (LinkedIn recommends staying under 200/day).
maxApplicationsPerRun = 5
# Optional cap: stop after processing (viewing/evaluating) this many job
# postings in one run, regardless of apply outcome. Useful for small test
# runs. 0 = no limit.
maxJobsToProcess = 5

# --- GUI integration ---
# If AI Career Agent's desktop app (gui_app.py) has been used to change
# any settings, those changes are stored separately in user_config.json
# so this file's comments/defaults are never overwritten. Applying them
# here (as the very last step) means every setting above acts as the
# "factory default" and user_config.json values win when present -- the
# app and this file can be used interchangeably without conflicting.
try:
    import sys as _sys
    import app_config_store as _app_config_store
    _app_config_store.apply_overrides_to_config(_sys.modules[__name__])
except Exception:
    pass
