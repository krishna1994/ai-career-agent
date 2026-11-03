"""
Advanced Configuration - Modular Feature Control
This file allows you to enable/disable specific features and choose efficiency levels.
"""

# ============================================================================
# EFFICIENCY MODES (Choose ONE)
# ============================================================================
# These are preset combinations of features optimized for different goals.
# You can override individual features below if you want custom control.

EFFICIENCY_MODE = "BALANCED"  # Options: "SPEED", "BALANCED", "PRECISION", "CUSTOM"

# Mode Descriptions:
# - SPEED: Maximum applications per hour. Minimal AI usage. Good for casting a wide net.
# - BALANCED: Moderate speed with AI scoring. Best for most users.
# - PRECISION: Slow but surgical. Deep analysis, tailored resumes, follow-ups. Quality over quantity.
# - CUSTOM: Ignore presets and use the individual feature flags below.

# ============================================================================
# FEATURE FLAGS (Individual Control)
# ============================================================================
# Only applies if EFFICIENCY_MODE = "CUSTOM"

# --- Core Features (Always Available) ---
ENABLE_BROWSER_AUTOMATION = True  # If False, bot won't run at all
ENABLE_DATABASE_LOGGING = True    # Log applications to SQLite

# --- AI Features ---
ENABLE_AI_SCORING = True           # Use LLM to score job fit (1-5)
ENABLE_SKILL_GAP_ANALYSIS = True   # Deterministic skill extraction and gap detection
ENABLE_AI_RESUME_TAILORING = True  # Dynamically rewrite resume for each job
ENABLE_AI_FORM_FILLING = True      # Use AI to answer custom application questions

# --- Advanced Filtering ---
ENABLE_ATS_VENDOR_DETECTION = False  # Detect which ATS system the company uses
ENABLE_COMPANY_RESEARCH = False      # Look up company funding, size, etc. before applying
ENABLE_SALARY_GAP_ANALYSIS = False   # Compare your expected salary vs job posting

# --- Follow-Up & Tracking ---
ENABLE_AUTOMATED_FOLLOWUPS = False   # Send follow-up messages after X days
ENABLE_INTERVIEW_PREP = False        # Generate interview questions based on JD
ENABLE_FUNNEL_ANALYTICS = False      # Track conversion rates (Applied → Interview → Offer)

# --- Stealth & Safety ---
ENABLE_STEALTH_MODE = True           # Use selenium-stealth to avoid detection
ENABLE_HUMAN_DELAYS = True           # Random delays between actions (2-5 seconds)
ENABLE_CAPTCHA_DETECTION = True      # Pause if CAPTCHA is detected

# --- Resume Strategy ---
RESUME_FORMAT = "LINKEDIN_DEFAULT"   # Options: "LINKEDIN_DEFAULT", "LATEX_PDF", "HTML_TAILORED"
# - LINKEDIN_DEFAULT: Use whatever resume is on your LinkedIn profile
# - LATEX_PDF: Generate a professional LaTeX PDF for each job (requires LaTeX installed)
# - HTML_TAILORED: Generate an HTML resume with dynamic sections

# ============================================================================
# EFFICIENCY MODE PRESETS (Auto-Applied)
# ============================================================================
# These override the individual flags above unless EFFICIENCY_MODE = "CUSTOM"

if EFFICIENCY_MODE == "SPEED":
    ENABLE_AI_SCORING = False
    ENABLE_SKILL_GAP_ANALYSIS = False
    ENABLE_AI_RESUME_TAILORING = False
    ENABLE_AI_FORM_FILLING = False
    ENABLE_COMPANY_RESEARCH = False
    ENABLE_AUTOMATED_FOLLOWUPS = False
    ENABLE_HUMAN_DELAYS = False
    RESUME_FORMAT = "LINKEDIN_DEFAULT"
    
elif EFFICIENCY_MODE == "BALANCED":
    ENABLE_AI_SCORING = True
    ENABLE_SKILL_GAP_ANALYSIS = True
    ENABLE_AI_RESUME_TAILORING = False  # Too slow for balanced mode
    ENABLE_AI_FORM_FILLING = True
    ENABLE_COMPANY_RESEARCH = False
    ENABLE_AUTOMATED_FOLLOWUPS = False
    ENABLE_HUMAN_DELAYS = True
    RESUME_FORMAT = "LINKEDIN_DEFAULT"
    
elif EFFICIENCY_MODE == "PRECISION":
    ENABLE_AI_SCORING = True
    ENABLE_SKILL_GAP_ANALYSIS = True
    ENABLE_AI_RESUME_TAILORING = True
    ENABLE_AI_FORM_FILLING = True
    ENABLE_ATS_VENDOR_DETECTION = True
    ENABLE_COMPANY_RESEARCH = True
    ENABLE_SALARY_GAP_ANALYSIS = True
    ENABLE_AUTOMATED_FOLLOWUPS = True
    ENABLE_INTERVIEW_PREP = True
    ENABLE_FUNNEL_ANALYTICS = True
    ENABLE_HUMAN_DELAYS = True
    RESUME_FORMAT = "LATEX_PDF"

# ============================================================================
# THRESHOLDS & LIMITS
# ============================================================================

# AI Scoring Thresholds
MIN_AI_SCORE = 3              # Skip jobs scoring below this (1-5 scale)
MIN_SKILL_COVERAGE = 0.6      # Skip if less than 60% of required skills are covered
MAX_SKILL_GAPS = 5            # Skip if more than 5 critical skills are missing

# Application Limits (Safety)
MAX_APPLICATIONS_PER_RUN = 50  # Stop after this many successful applications
MAX_APPLICATIONS_PER_DAY = 100 # Hard daily limit (tracked in database)
DRY_RUN = True                 # If True, simulate but don't actually submit

# Performance Tuning
BROWSER_HEADLESS = False       # Run browser in background (faster but harder to debug)
PARALLEL_JOBS = 1              # Number of browser instances (experimental, use 1 for safety)

# ============================================================================
# COST CONTROLS (For AI Features)
# ============================================================================

# OpenAI API Settings
AI_MODEL = "gpt-4o-mini"       # Options: "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"
# Cost per 1000 tokens: gpt-4o ($0.005), gpt-4o-mini ($0.0005), gpt-3.5-turbo ($0.0015)

MAX_AI_COST_PER_RUN = 5.0      # Stop if AI costs exceed this amount (USD)
ENABLE_COST_TRACKING = True    # Track and display AI costs in real-time

# ============================================================================
# FEATURE DEPENDENCIES (Auto-Validation)
# ============================================================================
# Some features require others to be enabled. This section auto-corrects invalid configs.

if ENABLE_AI_RESUME_TAILORING and not ENABLE_AI_SCORING:
    print("⚠️ Warning: AI Resume Tailoring requires AI Scoring. Enabling AI Scoring.")
    ENABLE_AI_SCORING = True

if ENABLE_SKILL_GAP_ANALYSIS and not ENABLE_AI_SCORING:
    print("⚠️ Warning: Skill Gap Analysis works best with AI Scoring. Consider enabling it.")

if ENABLE_AUTOMATED_FOLLOWUPS and not ENABLE_DATABASE_LOGGING:
    print("⚠️ Warning: Automated Follow-ups require Database Logging. Enabling Database Logging.")
    ENABLE_DATABASE_LOGGING = True

if RESUME_FORMAT == "LATEX_PDF":
    try:
        import subprocess
        subprocess.run(["pdflatex", "--version"], capture_output=True, check=True)
    except:
        print("⚠️ Warning: LaTeX not found. Falling back to LINKEDIN_DEFAULT.")
        RESUME_FORMAT = "LINKEDIN_DEFAULT"

# ============================================================================
# SUMMARY (Displayed on Startup)
# ============================================================================

def print_config_summary():
    print("\n" + "="*60)
    print("🚀 AI Career Agent")
    print("="*60)
    print(f"Mode: {EFFICIENCY_MODE}")
    print(f"Dry Run: {'✅ ENABLED (Safe)' if DRY_RUN else '❌ DISABLED (Live Applications)'}")
    print(f"Max Applications: {MAX_APPLICATIONS_PER_RUN} per run, {MAX_APPLICATIONS_PER_DAY} per day")
    print("\nActive Features:")
    if ENABLE_AI_SCORING: print("  ✅ AI Scoring")
    if ENABLE_SKILL_GAP_ANALYSIS: print("  ✅ Skill Gap Analysis")
    if ENABLE_AI_RESUME_TAILORING: print("  ✅ AI Resume Tailoring")
    if ENABLE_AI_FORM_FILLING: print("  ✅ AI Form Filling")
    if ENABLE_COMPANY_RESEARCH: print("  ✅ Company Research")
    if ENABLE_AUTOMATED_FOLLOWUPS: print("  ✅ Automated Follow-ups")
    if ENABLE_INTERVIEW_PREP: print("  ✅ Interview Prep")
    print(f"\nResume Strategy: {RESUME_FORMAT}")
    print(f"AI Model: {AI_MODEL}")
    if ENABLE_COST_TRACKING:
        print(f"Max AI Cost: ${MAX_AI_COST_PER_RUN} per run")
    print("="*60 + "\n")