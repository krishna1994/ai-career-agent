# 🚀 AI Career Agent - Comprehensive User Guide

AI Career Agent is a Python-based automation tool designed to help you apply for "Easy Apply" jobs on LinkedIn efficiently.

---

## 🖥️ Desktop App (Recommended)

The easiest way to use AI Career Agent is through its desktop GUI — no Python/YAML editing required.

```bash
pip install -r requirements.txt
python gui_app.py
```

The app has four tabs:

1. **🏠 Dashboard** — Click **"🔐 Log in to LinkedIn"** once to open a Chrome window and
   authenticate (email/password, Google sign-in, or any method). Your session is saved as a
   cookie so you won't need to log in again on future runs. Then click **"▶️ Start Run"** to
   launch the bot — a prominent banner shows whether Dry Run is ON (safe, default) or OFF
   (submits real applications). Watch live stats and a scrolling log in real time, and click
   **"⏹ Stop"** at any time to halt the bot gracefully at the next safe checkpoint (it won't be
   killed mid-click).
2. **⚙️ Settings** — Every filter and option available in `config.py`, organized into groups:
   - **🔑 Account & Browser:** email/password, headless mode, Chrome profile path.
   - **📄 Resume:** browse for a local resume file to upload (used on Easy Apply forms that show
     a file-upload step), pick your "Preferred CV #" among resumes already on your LinkedIn
     profile, and optionally paste your plain-text resume content (used only by the AI
     features below, separate from the uploaded file).
   - **🤖 AI Features:** enable AI-powered ATS scoring, resume tailoring, and question
     answering for both LinkedIn and Indeed runs. Requires the plain-text resume above to be
     filled in. When enabled, each job is scored (1-5) against your resume before applying;
     jobs below "Minimum ATS Score" are automatically skipped and logged to
     `data/applications.db`. AI is also used as a fallback to answer custom application
     questions not already covered in the My Answers tab. Leave disabled (default) for the
     bot's original keyword-only behavior.
   - **🎯 Job Search Filters:** keywords, search locations, allowed countries (the real filter
     that prevents applying to unrelated countries), experience level, date posted, job type,
     remote preference, minimum salary tier, sort order, company/title blacklists, auto-follow
     companies, and phone number.

     > ⚠️ **About the salary filter:** LinkedIn defines 9 fixed salary *tiers* internally
     > (Tier 1 - Tier 9). The dropdown shows each as e.g. "Tier 3 (reference: $80,000+ USD)" —
     > the `$X,000+ USD` part is only a reference label for which tier it is, **not** a literal
     > dollar figure. LinkedIn automatically resolves the tier to the **local currency of your
     > search location** at filter/display time — e.g. Tier 3 will filter/display as a EUR
     > amount for an Ireland/EU search, or GBP for a UK search. This was verified empirically:
     > searching Ireland with Tier 3 returned a job advertised at **€100K**, not $100K. If you
     > need an exact currency amount, check the salary shown on the job postings LinkedIn
     > actually returns for your target search location.
   - **🧪 Safety & Limits:** Dry Run toggle, max applications per run, max jobs to process,
     verbose warnings.

   All of this used to require hand-editing `config.py` — now it's all form fields. Click
   **"💾 Save Settings"** when done.
3. **📝 My Answers** — Shows **every answer the bot currently knows how to give**, loaded
   directly from `additionalQuestions.yaml` (typically 150-200+ rows across text/yes-no/dropdown
   answers), fully editable in simple tables — not a blank slate. Edit any existing row, add new
   ones, or remove ones you don't need. Click **"💾 Save My Answers"** to persist your changes
   to `my_answers.yaml`, which is layered on top of the original reference file at runtime (your
   answers always win on a match, and the original file is never modified). Use
   **"🔄 Reload All"** to refresh the view if you've edited `additionalQuestions.yaml` by hand.
4. **📸 Screenshots** — Browse every screenshot the bot captured (Easy Apply modal + pre-submit
   state) for each job it processed, so you can visually verify exactly what it saw and filled
   in, without hunting through the `screenshots/` folder manually.

> Settings/answers entered in the app are stored in `user_config.json` / `my_answers.yaml`
> (both gitignored) and override `config.py` / `additionalQuestions.yaml` defaults — the
> original files are never modified, so command-line usage (`python linkedin.py`) and the GUI
> can be used interchangeably.

---

## ⚠️ IMPORTANT: Safety & Risk Warning
**Use this bot at your own risk.** 
- **Terms of Service:** Automating applications may violate LinkedIn's Terms of Service.
- **Account Ban Risk:** Applying to too many jobs too quickly can trigger security flags. 
- **Recommendation:** 
    - Always start with `dryRun = True` to verify your settings.
    - Do not apply to more than **100-200 jobs per day**.
    - Use the `botSpeed` constant to keep delays realistic.

---

## 🛠️ Installation

### Option 1: Manual Installation (Windows/Mac/Linux)
1. **Install Python:** Ensure Python 3.8+ is installed.
2. **Enter the project directory:**
   ```bash
   cd AI_Career_Agent
   ```
3. **Install Dependencies:**
   ```bash
   pip install selenium webdriver_manager selenium-stealth pyyaml
   ```
   *(If you encounter SSL errors, use: `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt`)*
4. **Run the Bot:**
   ```bash
   python linkedin.py
   ```

### Option 2: Docker Installation (Recommended)
1. **Enter the project directory** (`AI_Career_Agent`).
2. **Configure:** Edit `config.py` with your credentials.
3. **Run:**
   ```bash
   docker-compose up --build
   ```

---

## ⚙️ Configuration Guide

All settings are managed in `config.py`. **Do not commit this file to public repositories after adding your password.**

### 🔑 Account & Browser
| Variable | Description | Example/Value |
| :--- | :--- | :--- |
| `email` | Your LinkedIn login email | `"user@email.com"` |
| `password` | Your LinkedIn password | `"your_password"` |
| `headless` | Run without opening a browser window | `False` |
| `chromeProfilePath` | Path to your Chrome profile to skip login | `r"C:\Users\...\User Data\Default"` |

### 🎯 Job Search Preferences
| Variable | Description | Example/Value |
| :--- | :--- | :--- |
| `location` | Cities or Continents to search in | `["NorthAmerica", "Europe"]` |
| `keywords` | Job titles or skills to search for | `["react", "python", "frontend"]` |
| `experienceLevels`| Experience level filter | `["Entry level", "Associate"]` |
| `datePosted` | How recent the job must be | `["Past Week"]` |
| `jobType` | Type of employment | `["Full-time", "Remote"]` |
| `remote` | Work location preference | `["Remote", "Hybrid"]` |
| `salary` | Minimum salary filter | `["$80,000+"]` |
| `sort` | Sort by "Recent" or "Relevant" | `["Recent"]` |

### 🚫 Filtering & Safety
| Variable | Description | Example/Value |
| :--- | :--- | :--- |
| `blacklistCompanies`| Companies the bot will skip | `["Company A", "Company B"]` |
| `blackListTitles` | Job titles the bot will skip | `["Manager", "Senior"]` |
| `dryRun` | **CRITICAL:** If `True`, bot logs but DOES NOT apply | `True` (Recommended for testing) |
| `maxApplicationsPerRun`| Stop after X successful applications | `50` |
| `followCompanies` | Follow the company after applying | `False` |

### 📝 Custom Questions (`additionalQuestions.yaml`)
The bot uses `additionalQuestions.yaml` to answer common application questions (e.g., "How many years of experience do you have with Python?").
- Open the file and add your answers under the `inputField` section.
- The bot will look for keywords in the question and match them to your provided answers.

---

## 📈 Monitoring Results
The bot creates a `data/` folder. Inside, you will find:
- **`urlData.txt`**: The search URLs the bot is currently processing.
- **`Applied Jobs DATA - YYYYMMDD.txt`**: A detailed log of every job the bot encountered, whether it applied, skipped (blacklisted), or failed.

---

## ❓ Troubleshooting
- **`WinError 193` / Driver Issues:** The bot uses `webdriver_manager` to handle drivers automatically. If it fails, ensure your Chrome browser is up to date.
- **Login Failures:** If LinkedIn triggers a CAPTCHA, the bot will fail. Log in manually in your browser first, then use the `chromeProfilePath` to let the bot use your existing session.
- **SSL Errors during pip install:** Use the `--trusted-host` flags mentioned in the installation section.