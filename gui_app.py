"""
gui_app.py - AI Career Agent Desktop App (PyQt6)

A user-friendly desktop front-end for the AI Career Agent LinkedIn bot.
Lets you configure your job search (every filter available in config.py),
your resume, your personal application answers (including everything
already in additionalQuestions.yaml, fully editable), run the bot with
live progress/logs, view screenshots of each attempted application, and
safely stop a run in progress -- all without touching any Python/YAML
files by hand.

Design goals (addressing every pain point hit while building this bot
from the command line):
  1. Non-destructive settings: never overwrites config.py or
     additionalQuestions.yaml -- see app_config_store.py for how GUI
     settings/answers are layered on top instead.
  2. Complete filter coverage: every search filter available in
     config.py (keywords, locations, allowed countries, experience
     level, date posted, job type, remote preference, salary, sort,
     company/title blacklists, follow-companies) is editable here.
  3. Resume management: browse for a local resume file (uploaded via
     Selenium if the Easy Apply form has a file input) AND/OR choose
     which of your existing LinkedIn-uploaded resumes to use.
  4. Full question/answer coverage: the My Answers tab loads BOTH your
     personal overrides (my_answers.yaml) AND the ~670 lines of existing
     reference answers already in additionalQuestions.yaml, so you can
     see and edit everything the bot already knows how to answer, not
     just a blank slate.
  5. Real-time feedback: a live log pane + running counters instead of
     having to read a text file after the fact.
  6. Safe by default: Dry Run is ON by default in the GUI, with a very
     visible toggle and warning before you turn it off.
  7. Graceful Stop: a Stop button sets a flag that the bot checks between
     jobs, instead of force-killing the browser process.
  8. One-click manual login: the exact same interactive login flow used
     from the command line (login_helper.py), wired to a button.
  9. Visual proof: a screenshot gallery tab shows exactly what the bot
     saw/filled for every job it processed, so you can audit results
     without hunting through folders.

Run with:
    python gui_app.py
"""
import os
import queue
import sys
import threading
from typing import Optional

# Ensure all relative paths used throughout this app (cookies/, data/,
# screenshots/, additionalQuestions.yaml, user_config.json, etc.) resolve
# correctly regardless of the directory the app was launched FROM (e.g.
# double-clicking a shortcut, or running `python AI_Career_Agent/gui_app.py`
# from a parent folder). Without this, the app would silently load empty
# data when launched from anywhere other than this exact folder.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import app_config_store
import question_answerer as qa_module

APP_TITLE = "AI Career Agent"
SCREENSHOTS_DIR = os.path.join(os.getcwd(), "screenshots")


# ---------------------------------------------------------------------------
# Background worker that runs the bot on a separate thread so the GUI
# never freezes, and forwards callbacks into a thread-safe queue that a
# QTimer drains on the GUI thread (PyQt widgets must only be touched from
# the main/GUI thread).
# ---------------------------------------------------------------------------
class BotWorker:
    def __init__(self, event_queue: "queue.Queue"):
        self.event_queue = event_queue
        self.thread: Optional[threading.Thread] = None
        self.stop_flag = threading.Event()
        self.running = False

    def start(self):
        if self.running:
            return
        self.stop_flag.clear()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_flag.set()

    def _run(self):
        try:
            # Imported lazily so the GUI can start even before selenium
            # etc. are confirmed installed (clearer error reporting).
            import linkedin

            def on_log(msg):
                self.event_queue.put(("log", msg))

            def on_screenshot(path):
                self.event_queue.put(("screenshot", path))

            def on_stats(stats):
                self.event_queue.put(("stats", stats))

            self.event_queue.put(("log", "🚀 Starting bot..."))
            bot = linkedin.Linkedin(
                on_log=on_log,
                on_screenshot=on_screenshot,
                on_stats=on_stats,
                stop_flag=self.stop_flag,
            )
            bot.linkJobApply()
            self.event_queue.put(("log", "✅ Run finished."))
        except Exception as e:
            self.event_queue.put(("log", f"❌ Bot crashed: {e}"))
        finally:
            self.running = False
            self.event_queue.put(("done", None))


class LoginWorker:
    """Runs login_helper.py's interactive flow on a background thread."""

    def __init__(self, event_queue: "queue.Queue"):
        self.event_queue = event_queue
        self.thread: Optional[threading.Thread] = None

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            import login_helper
            self.event_queue.put(("log", "🔐 Opening Chrome for manual login..."))
            login_helper.main()
            self.event_queue.put(("log", "✅ Login flow finished."))
        except Exception as e:
            self.event_queue.put(("log", f"❌ Login flow error: {e}"))
        finally:
            self.event_queue.put(("login_done", None))


# ---------------------------------------------------------------------------
# Dashboard / Run tab
# ---------------------------------------------------------------------------
class DashboardTab(QWidget):
    def __init__(self, event_queue: "queue.Queue"):
        super().__init__()
        self.event_queue = event_queue
        self.bot_worker = BotWorker(event_queue)
        self.login_worker = LoginWorker(event_queue)

        layout = QVBoxLayout()

        # --- Controls row ---
        controls = QHBoxLayout()
        self.login_btn = QPushButton("🔐 Log in to LinkedIn")
        self.login_btn.clicked.connect(self.handle_login)
        controls.addWidget(self.login_btn)

        self.start_btn = QPushButton("▶️ Start Run")
        self.start_btn.setStyleSheet("font-weight: bold; background-color: #2e7d32; color: white; padding: 6px;")
        self.start_btn.clicked.connect(self.handle_start)
        controls.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("font-weight: bold; background-color: #c62828; color: white; padding: 6px;")
        self.stop_btn.clicked.connect(self.handle_stop)
        controls.addWidget(self.stop_btn)

        layout.addLayout(controls)

        # --- Dry run banner ---
        self.dry_run_banner = QLabel()
        self.dry_run_banner.setStyleSheet("padding: 6px; font-weight: bold;")
        layout.addWidget(self.dry_run_banner)
        self.refresh_dry_run_banner()

        # --- Live stats row ---
        stats_box = QGroupBox("Live Stats")
        stats_layout = QGridLayout()
        self.stat_labels = {}
        stat_fields = [
            ("jobs_processed", "Jobs Processed"),
            ("applied", "Applied"),
            ("blacklisted", "Blacklisted"),
            ("already_applied", "Already Applied"),
            ("cannot_apply", "Could Not Apply"),
        ]
        for i, (key, label) in enumerate(stat_fields):
            stats_layout.addWidget(QLabel(label + ":"), 0, i * 2)
            value_label = QLabel("0")
            value_label.setStyleSheet("font-weight: bold;")
            self.stat_labels[key] = value_label
            stats_layout.addWidget(value_label, 0, i * 2 + 1)
        stats_box.setLayout(stats_layout)
        layout.addWidget(stats_box)

        # --- Live log ---
        log_box = QGroupBox("Live Log")
        log_layout = QVBoxLayout()
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.log_view)
        log_box.setLayout(log_layout)
        layout.addWidget(log_box, stretch=1)

        self.setLayout(layout)

        # Poll the event queue for updates from background threads.
        self.timer = QTimer()
        self.timer.timeout.connect(self.drain_events)
        self.timer.start(200)

    def refresh_dry_run_banner(self):
        settings = app_config_store.load_user_settings()
        dry_run = settings.get("dryRun", True)
        if dry_run:
            self.dry_run_banner.setText("🧪 DRY RUN MODE: ON — no real applications will be submitted.")
            self.dry_run_banner.setStyleSheet("padding: 6px; font-weight: bold; background-color: #1b5e20; color: white;")
        else:
            self.dry_run_banner.setText("⚠️ DRY RUN MODE: OFF — applications WILL be submitted for real!")
            self.dry_run_banner.setStyleSheet("padding: 6px; font-weight: bold; background-color: #b71c1c; color: white;")

    def handle_login(self):
        self.login_btn.setEnabled(False)
        self.append_log("Launching Chrome for manual login. Please log in in the window that appears...")
        self.login_worker.start()

    def handle_start(self):
        self.refresh_dry_run_banner()
        settings = app_config_store.load_user_settings()
        if not settings.get("dryRun", True):
            reply = QMessageBox.question(
                self,
                "Confirm Live Run",
                "Dry Run is OFF. This run will submit REAL job applications.\n\nAre you sure you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.log_view.clear()
        for key in self.stat_labels:
            self.stat_labels[key].setText("0")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.bot_worker = BotWorker(self.event_queue)  # fresh worker each run
        self.bot_worker.start()

    def handle_stop(self):
        self.append_log("🛑 Stop requested. The bot will stop at the next safe checkpoint...")
        self.bot_worker.stop()
        self.stop_btn.setEnabled(False)

    def append_log(self, text: str):
        self.log_view.appendPlainText(text)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    def drain_events(self):
        try:
            while True:
                kind, payload = self.event_queue.get_nowait()
                if kind == "log":
                    self.append_log(str(payload))
                elif kind == "stats":
                    for key, label in self.stat_labels.items():
                        if key in payload:
                            label.setText(str(payload[key]))
                elif kind == "screenshot":
                    pass
                elif kind == "done":
                    self.start_btn.setEnabled(True)
                    self.stop_btn.setEnabled(False)
                elif kind == "login_done":
                    self.login_btn.setEnabled(True)
        except queue.Empty:
            pass


# ---------------------------------------------------------------------------
# Settings tab -- every filter available in config.py, plus resume mgmt.
# ---------------------------------------------------------------------------
class SettingsTab(QWidget):
    EXPERIENCE_OPTIONS = ["Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"]
    DATE_POSTED_OPTIONS = ["Any Time", "Past Month", "Past Week", "Past 24 hours"]
    JOB_TYPE_OPTIONS = ["Full-time", "Part-time", "Contract", "Temporary", "Volunteer", "Intership", "Other"]
    REMOTE_OPTIONS = ["On-site", "Remote", "Hybrid"]
    # Display labels make it explicit these are LinkedIn's fixed TIERS
    # (1-9), not literal USD amounts -- LinkedIn resolves each tier to the
    # LOCAL CURRENCY of the search location (verified empirically: an
    # Ireland search on tier 3 matched a job advertised at EUR, not USD).
    # The underlying value stored/sent to config.py (and mapped to
    # f_SB2=N in utils.py) is unchanged, only the label shown to the user
    # is clarified via Qt item data.
    SALARY_OPTIONS = [
        ("Tier 1 (reference: $40,000+ USD)", "$40,000+"),
        ("Tier 2 (reference: $60,000+ USD)", "$60,000+"),
        ("Tier 3 (reference: $80,000+ USD)", "$80,000+"),
        ("Tier 4 (reference: $100,000+ USD)", "$100,000+"),
        ("Tier 5 (reference: $120,000+ USD)", "$120,000+"),
        ("Tier 6 (reference: $140,000+ USD)", "$140,000+"),
        ("Tier 7 (reference: $160,000+ USD)", "$160,000+"),
        ("Tier 8 (reference: $180,000+ USD)", "$180,000+"),
        ("Tier 9 (reference: $200,000+ USD)", "$200,000+"),
    ]
    SORT_OPTIONS = ["Recent", "Relevent"]

    def __init__(self):
        super().__init__()
        outer_layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout()

        # --- Account & browser ---
        account_box = QGroupBox("🔑 Account & Browser")
        form = QFormLayout()
        self.email_edit = QLineEdit()
        form.addRow("LinkedIn Email:", self.email_edit)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("LinkedIn Password (optional if using manual login):", self.password_edit)
        self.headless_check = QCheckBox("Run browser in headless mode (no visible window)")
        form.addRow(self.headless_check)
        self.chrome_profile_edit = QLineEdit()
        self.chrome_profile_edit.setPlaceholderText(r"C:\Users\...\User Data\Default (optional)")
        form.addRow("Chrome Profile Path:", self.chrome_profile_edit)
        account_box.setLayout(form)
        layout.addWidget(account_box)

        # --- Resume ---
        resume_box = QGroupBox("📄 Resume")
        resume_form = QFormLayout()
        resume_row = QHBoxLayout()
        self.resume_path_edit = QLineEdit()
        self.resume_path_edit.setPlaceholderText("Optional: path to a local resume file to upload")
        resume_row.addWidget(self.resume_path_edit)
        browse_btn = QPushButton("📁 Browse...")
        browse_btn.clicked.connect(self.browse_resume)
        resume_row.addWidget(browse_btn)
        resume_form.addRow("Local Resume File:", resume_row)

        self.preferred_cv_spin = QSpinBox()
        self.preferred_cv_spin.setRange(1, 20)
        self.preferred_cv_spin.setValue(1)
        resume_form.addRow("Preferred CV # (if multiple on LinkedIn profile, 1 = first):", self.preferred_cv_spin)

        resume_note = QLabel(
            "If a local resume file is set above, the bot will try to upload it on Easy Apply forms\n"
            "that show a file-upload step. Otherwise, it selects from resumes already uploaded to\n"
            "your LinkedIn profile, using the 'Preferred CV #' setting above."
        )
        resume_note.setWordWrap(True)
        resume_note.setStyleSheet("color: #888;")
        resume_form.addRow(resume_note)

        self.resume_text_edit = QPlainTextEdit()
        self.resume_text_edit.setPlaceholderText(
            "Optional: paste the PLAIN TEXT of your resume here.\n"
            "Used ONLY for AI ATS scoring / resume tailoring / AI question answering below\n"
            "(separate from the file uploaded to LinkedIn above)."
        )
        self.resume_text_edit.setFixedHeight(100)
        resume_form.addRow("Resume Text (for AI features):", self.resume_text_edit)

        resume_box.setLayout(resume_form)
        layout.addWidget(resume_box)

        # --- AI features ---
        ai_box = QGroupBox("🤖 AI Features (ATS Scoring, Resume Tailoring, Question Answering)")
        ai_form = QFormLayout()

        self.use_ai_check = QCheckBox("Enable AI features (requires Resume Text above)")
        ai_form.addRow(self.use_ai_check)

        self.ai_api_key_edit = QLineEdit()
        self.ai_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.ai_api_key_edit.setPlaceholderText("sk-... (leave as default to use local AI provider instead)")
        ai_form.addRow("AI API Key:", self.ai_api_key_edit)

        self.ai_model_edit = QLineEdit()
        self.ai_model_edit.setPlaceholderText("gpt-4o")
        ai_form.addRow("AI Model:", self.ai_model_edit)

        self.min_ats_score_spin = QSpinBox()
        self.min_ats_score_spin.setRange(1, 5)
        self.min_ats_score_spin.setValue(3)
        ai_form.addRow("Minimum ATS Score to Apply (1-5):", self.min_ats_score_spin)

        self.enable_tailoring_check = QCheckBox("Attempt to tailor resume wording for each job (not yet uploaded to LinkedIn automatically)")
        ai_form.addRow(self.enable_tailoring_check)

        ai_note = QLabel(
            "When enabled, the bot scores each job against your Resume Text before applying\n"
            "(LinkedIn AND Indeed) and skips jobs below the minimum score. AI is also used as a\n"
            "fallback to answer custom application questions not covered in the My Answers tab."
        )
        ai_note.setWordWrap(True)
        ai_note.setStyleSheet("color: #888; font-size: 11px;")
        ai_form.addRow(ai_note)

        ai_box.setLayout(ai_form)
        layout.addWidget(ai_box)

        # --- Job search filters ---
        filters_box = QGroupBox("🎯 Job Search Filters")
        filters_form = QFormLayout()

        self.keywords_edit = QLineEdit()
        self.keywords_edit.setPlaceholderText("Software Engineer, Python, Developer, AI")
        filters_form.addRow("Keywords (comma-separated):", self.keywords_edit)

        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("Europe, Remote, Ireland")
        filters_form.addRow("Search Locations (comma-separated):", self.location_edit)

        self.allowed_countries_edit = QLineEdit()
        self.allowed_countries_edit.setPlaceholderText("Ireland, United Kingdom, Remote")
        filters_form.addRow("Allowed Countries (actual filter):", self.allowed_countries_edit)

        self.experience_list = self._make_checklist(self.EXPERIENCE_OPTIONS)
        filters_form.addRow("Experience Level:", self.experience_list)

        self.date_posted_combo = QComboBox()
        self.date_posted_combo.addItems(self.DATE_POSTED_OPTIONS)
        filters_form.addRow("Date Posted:", self.date_posted_combo)

        self.job_type_list = self._make_checklist(self.JOB_TYPE_OPTIONS)
        filters_form.addRow("Job Type:", self.job_type_list)

        self.remote_list = self._make_checklist(self.REMOTE_OPTIONS)
        filters_form.addRow("Remote Preference:", self.remote_list)

        self.salary_combo = QComboBox()
        for label, value in self.SALARY_OPTIONS:
            self.salary_combo.addItem(label, value)
        filters_form.addRow("Minimum Salary Tier:", self.salary_combo)

        salary_note = QLabel(
            "⚠️ LinkedIn defines 9 fixed salary TIERS internally (not literal dollar amounts).\n"
            "The \"$X,000+ USD\" text above is only a reference label for the tier number --\n"
            "LinkedIn resolves it to the LOCAL CURRENCY of your search location at filter/display\n"
            "time (e.g. the same tier shows as a EUR amount for an Ireland/EU search, GBP for a\n"
            "UK search). Verified empirically: an Ireland search on Tier 3 matched a job\n"
            "advertised at €100K, not $100K. If you need an exact amount, check the salary\n"
            "shown on job postings returned for your target search location."
        )
        salary_note.setWordWrap(True)
        salary_note.setStyleSheet("color: #e0a030; font-size: 11px;")
        filters_form.addRow(salary_note)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(self.SORT_OPTIONS)
        filters_form.addRow("Sort By:", self.sort_combo)

        self.blacklist_companies_edit = QLineEdit()
        self.blacklist_companies_edit.setPlaceholderText("Apple, Google")
        filters_form.addRow("Blacklist Companies:", self.blacklist_companies_edit)

        self.blacklist_titles_edit = QLineEdit()
        self.blacklist_titles_edit.setPlaceholderText("Manager, .Net")
        filters_form.addRow("Blacklist Title Keywords:", self.blacklist_titles_edit)

        self.follow_companies_check = QCheckBox("Follow companies automatically after applying")
        filters_form.addRow(self.follow_companies_check)

        self.phone_edit = QLineEdit()
        filters_form.addRow("Phone Number:", self.phone_edit)

        filters_box.setLayout(filters_form)
        layout.addWidget(filters_box)

        # --- Safety ---
        safety_box = QGroupBox("🧪 Safety & Limits")
        safety_form = QFormLayout()
        self.dry_run_check = QCheckBox("Dry Run (safe mode - no real applications submitted)")
        self.dry_run_check.setChecked(True)
        safety_form.addRow(self.dry_run_check)

        self.max_apply_spin = QSpinBox()
        self.max_apply_spin.setRange(0, 1000)
        self.max_apply_spin.setValue(5)
        safety_form.addRow("Max Applications Per Run (0 = no limit):", self.max_apply_spin)

        self.max_jobs_spin = QSpinBox()
        self.max_jobs_spin.setRange(0, 1000)
        self.max_jobs_spin.setValue(0)
        safety_form.addRow("Max Jobs To Process (0 = no limit, good for testing):", self.max_jobs_spin)

        self.display_warnings_check = QCheckBox("Show verbose warnings during run")
        safety_form.addRow(self.display_warnings_check)
        safety_box.setLayout(safety_form)
        layout.addWidget(safety_box)

        layout.addStretch(1)
        content.setLayout(layout)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("💾 Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        btn_row.addWidget(self.save_btn)
        self.status_label = QLabel("")
        btn_row.addWidget(self.status_label)
        outer_layout.addLayout(btn_row)

        self.setLayout(outer_layout)
        self.load_settings()

    @staticmethod
    def _make_checklist(options):
        """A compact multi-select widget built from checkboxes inside a
        bordered container, used for list-valued filters like Job Type."""
        container = QWidget()
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        container._checkboxes = {}
        for opt in options:
            cb = QCheckBox(opt)
            container._checkboxes[opt] = cb
            h.addWidget(cb)
        container.setLayout(h)
        return container

    @staticmethod
    def _get_checked(container):
        return [opt for opt, cb in container._checkboxes.items() if cb.isChecked()]

    @staticmethod
    def _set_checked(container, values):
        values_lower = [v.lower() for v in values]
        for opt, cb in container._checkboxes.items():
            cb.setChecked(opt.lower() in values_lower)

    def browse_resume(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Resume File", "", "Documents (*.pdf *.docx *.doc);;All Files (*)"
        )
        if path:
            self.resume_path_edit.setText(path)

    def load_settings(self):
        s = app_config_store.load_user_settings()
        self.email_edit.setText(s.get("email", ""))
        self.password_edit.setText(s.get("password", ""))
        self.headless_check.setChecked(s.get("headless", False))
        self.chrome_profile_edit.setText(s.get("chromeProfilePath", ""))

        self.resume_path_edit.setText(s.get("resumePath", ""))
        self.preferred_cv_spin.setValue(s.get("preferredCv", 1))
        self.resume_text_edit.setPlainText(s.get("resumeText", ""))

        self.use_ai_check.setChecked(s.get("use_ai_features", False))
        ai_api_key = s.get("ai_api_key", "YOUR_API_KEY_HERE")
        self.ai_api_key_edit.setText("" if ai_api_key == "YOUR_API_KEY_HERE" else ai_api_key)
        self.ai_model_edit.setText(s.get("ai_model", "gpt-4o"))
        self.min_ats_score_spin.setValue(s.get("min_ats_score", 3))
        self.enable_tailoring_check.setChecked(s.get("enable_resume_tailoring", True))

        self.keywords_edit.setText(", ".join(s.get("keywords", ["Software Engineer", "Python", "Developer", "AI"])))
        self.location_edit.setText(", ".join(s.get("location", ["Europe", "Remote", "Ireland"])))
        self.allowed_countries_edit.setText(", ".join(s.get("allowedCountries", ["Ireland", "United Kingdom", "Remote"])))

        self._set_checked(self.experience_list, s.get("experienceLevels", ["Mid-Senior level", "Director"]))

        date_posted = s.get("datePosted", ["Past Week"])
        if date_posted and date_posted[0] in self.DATE_POSTED_OPTIONS:
            self.date_posted_combo.setCurrentText(date_posted[0])

        self._set_checked(self.job_type_list, s.get("jobType", ["Full-time", "Part-time", "Contract"]))
        self._set_checked(self.remote_list, s.get("remote", ["On-site", "Remote", "Hybrid"]))

        salary_list = s.get("salary", ["$80,000+"])
        if salary_list:
            idx = self.salary_combo.findData(salary_list[0])
            if idx >= 0:
                self.salary_combo.setCurrentIndex(idx)

        sort_list = s.get("sort", ["Recent"])
        if sort_list and sort_list[0] in self.SORT_OPTIONS:
            self.sort_combo.setCurrentText(sort_list[0])

        self.blacklist_companies_edit.setText(", ".join(s.get("blacklistCompanies", [])))
        self.blacklist_titles_edit.setText(", ".join(s.get("blackListTitles", [])))
        self.follow_companies_check.setChecked(s.get("followCompanies", False))
        self.phone_edit.setText(s.get("Phone", ""))

        self.dry_run_check.setChecked(s.get("dryRun", True))
        self.max_apply_spin.setValue(s.get("maxApplicationsPerRun", 5))
        self.max_jobs_spin.setValue(s.get("maxJobsToProcess", 0))
        self.display_warnings_check.setChecked(s.get("displayWarnings", False))

    def save_settings(self):
        settings = {
            "email": self.email_edit.text().strip(),
            "password": self.password_edit.text(),
            "headless": self.headless_check.isChecked(),
            "chromeProfilePath": self.chrome_profile_edit.text().strip(),
            "resumePath": self.resume_path_edit.text().strip(),
            "preferredCv": self.preferred_cv_spin.value(),
            "resumeText": self.resume_text_edit.toPlainText().strip(),
            "use_ai_features": self.use_ai_check.isChecked(),
            "ai_api_key": self.ai_api_key_edit.text().strip() or "YOUR_API_KEY_HERE",
            "ai_model": self.ai_model_edit.text().strip() or "gpt-4o",
            "min_ats_score": self.min_ats_score_spin.value(),
            "enable_resume_tailoring": self.enable_tailoring_check.isChecked(),
            "keywords": [k.strip() for k in self.keywords_edit.text().split(",") if k.strip()],
            "location": [l.strip() for l in self.location_edit.text().split(",") if l.strip()],
            "allowedCountries": [c.strip() for c in self.allowed_countries_edit.text().split(",") if c.strip()],
            "experienceLevels": self._get_checked(self.experience_list),
            "datePosted": [self.date_posted_combo.currentText()],
            "jobType": self._get_checked(self.job_type_list),
            "remote": self._get_checked(self.remote_list),
            "salary": [self.salary_combo.currentData()],
            "sort": [self.sort_combo.currentText()],
            "blacklistCompanies": [c.strip() for c in self.blacklist_companies_edit.text().split(",") if c.strip()],
            "blackListTitles": [t.strip() for t in self.blacklist_titles_edit.text().split(",") if t.strip()],
            "followCompanies": self.follow_companies_check.isChecked(),
            "Phone": self.phone_edit.text().strip(),
            "dryRun": self.dry_run_check.isChecked(),
            "maxApplicationsPerRun": self.max_apply_spin.value(),
            "maxJobsToProcess": self.max_jobs_spin.value(),
            "displayWarnings": self.display_warnings_check.isChecked(),
        }
        app_config_store.save_user_settings(settings)
        self.status_label.setText("✅ Saved!")
        QTimer.singleShot(2000, lambda: self.status_label.setText(""))


# ---------------------------------------------------------------------------
# My Answers tab -- shows BOTH the existing ~670 lines of reference
# answers from additionalQuestions.yaml AND your personal overrides, all
# editable in one place.
# ---------------------------------------------------------------------------
class MyAnswersTab(QWidget):
    SECTION_LABELS = {
        "inputField": "Text Answers (name, phone, salary expectations, skills, etc.)",
        "radio": "Yes/No & Multiple-Choice Answers",
        "dropdown": "Dropdown Answers",
    }

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        info = QLabel(
            "This shows every answer the bot currently knows (loaded from additionalQuestions.yaml),\n"
            "plus your own personal answers. Edit any row, add new rows, or remove ones you don't need.\n"
            "When you Save, only YOUR changes are written to my_answers.yaml (layered on top of the\n"
            "original reference file at runtime) -- additionalQuestions.yaml itself is never modified."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        reload_row = QHBoxLayout()
        self.reload_btn = QPushButton("🔄 Reload All (reference + my answers)")
        self.reload_btn.clicked.connect(self.load_answers)
        reload_row.addWidget(self.reload_btn)
        reload_row.addStretch(1)
        layout.addLayout(reload_row)

        self.tables = {}
        tabs = QTabWidget()
        for section, label in self.SECTION_LABELS.items():
            table = QTableWidget(0, 2)
            table.setHorizontalHeaderLabels(["Keyword (matches question text)", "Your Answer"])
            table.horizontalHeader().setStretchLastSection(True)
            self.tables[section] = table

            container = QWidget()
            v = QVBoxLayout()
            v.addWidget(table)
            row_btns = QHBoxLayout()
            add_btn = QPushButton("+ Add Row")
            add_btn.clicked.connect(lambda _, t=table: t.insertRow(t.rowCount()))
            remove_btn = QPushButton("- Remove Selected Row")
            remove_btn.clicked.connect(lambda _, t=table: t.removeRow(t.currentRow()) if t.currentRow() >= 0 else None)
            row_btns.addWidget(add_btn)
            row_btns.addWidget(remove_btn)
            v.addLayout(row_btns)
            container.setLayout(v)
            tabs.addTab(container, label)

        layout.addWidget(tabs, stretch=1)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("💾 Save My Answers")
        self.save_btn.clicked.connect(self.save_answers)
        btn_row.addWidget(self.save_btn)
        self.status_label = QLabel("")
        btn_row.addWidget(self.status_label)
        layout.addLayout(btn_row)

        self.setLayout(layout)
        self.load_answers()

    def _load_reference_data(self):
        """Load the full reference data straight from additionalQuestions.yaml
        (the same file question_answerer.py reads), independent of the
        my_answers.yaml overlay, so the user sees everything that already
        exists."""
        try:
            answerer = qa_module.QuestionAnswerer(yaml_path="additionalQuestions.yaml")
            # Bypass the my_answers.yaml merge for this base view by
            # re-reading just the reference file's raw sections.
            import yaml
            if os.path.exists("additionalQuestions.yaml"):
                with open("additionalQuestions.yaml", "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f) or {}
            else:
                raw = {}
            return {
                "inputField": {str(k): str(v) for k, v in (raw.get("inputField") or {}).items()},
                "radio": {str(k): str(v) for k, v in (raw.get("radio") or {}).items()},
                "dropdown": {str(k): str(v) for k, v in (raw.get("dropdown") or {}).items()},
            }
        except Exception:
            return {"inputField": {}, "radio": {}, "dropdown": {}}

    def load_answers(self):
        reference = self._load_reference_data()
        mine = app_config_store.load_my_answers()

        for section, table in self.tables.items():
            table.setRowCount(0)
            # Combine: start with reference data, then overlay/override
            # with the user's own saved answers (so edits persist across
            # reloads and are visually distinguishable isn't necessary --
            # the merged value is simply what's shown, matching runtime
            # behavior exactly).
            combined = dict(reference.get(section, {}))
            combined.update(mine.get(section, {}))
            for keyword, answer in combined.items():
                row = table.rowCount()
                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem(keyword))
                table.setItem(row, 1, QTableWidgetItem(answer))

    def save_answers(self):
        data = {}
        for section, table in self.tables.items():
            section_data = {}
            for row in range(table.rowCount()):
                key_item = table.item(row, 0)
                val_item = table.item(row, 1)
                key = key_item.text().strip() if key_item else ""
                val = val_item.text().strip() if val_item else ""
                if key:
                    section_data[key] = val
            data[section] = section_data
        app_config_store.save_my_answers(data)
        self.status_label.setText("✅ Saved! (Changes layered on top of additionalQuestions.yaml)")
        QTimer.singleShot(3000, lambda: self.status_label.setText(""))


# ---------------------------------------------------------------------------
# Screenshots tab
# ---------------------------------------------------------------------------
class ScreenshotsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()

        self.list_widget = QListWidget()
        self.list_widget.setFixedWidth(320)
        self.list_widget.itemClicked.connect(self.show_selected)
        layout.addWidget(self.list_widget)

        right = QVBoxLayout()
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_list)
        right.addWidget(self.refresh_btn)

        self.image_label = QLabel("Select a screenshot to preview it here.")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(500, 400)
        self.image_label.setStyleSheet("border: 1px solid #555;")
        right.addWidget(self.image_label, stretch=1)

        right_container = QWidget()
        right_container.setLayout(right)
        layout.addWidget(right_container, stretch=1)

        self.setLayout(layout)
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        if not os.path.exists(SCREENSHOTS_DIR):
            return
        files = sorted(os.listdir(SCREENSHOTS_DIR), reverse=True)
        for f in files:
            if f.lower().endswith(".png"):
                self.list_widget.addItem(QListWidgetItem(f))

    def show_selected(self, item: QListWidgetItem):
        path = os.path.join(SCREENSHOTS_DIR, item.text())
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                self.image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.image_label.setPixmap(scaled)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1050, 760)

        self.event_queue: "queue.Queue" = queue.Queue()

        tabs = QTabWidget()
        self.dashboard_tab = DashboardTab(self.event_queue)
        tabs.addTab(self.dashboard_tab, "🏠 Dashboard")
        tabs.addTab(SettingsTab(), "⚙️ Settings")
        tabs.addTab(MyAnswersTab(), "📝 My Answers")
        self.screenshots_tab = ScreenshotsTab()
        tabs.addTab(self.screenshots_tab, "📸 Screenshots")

        self.setCentralWidget(tabs)

        # Refresh screenshot gallery periodically while a run may be in
        # progress, so new screenshots show up without manual refresh.
        self.screenshot_timer = QTimer()
        self.screenshot_timer.timeout.connect(self.screenshots_tab.refresh_list)
        self.screenshot_timer.start(3000)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()