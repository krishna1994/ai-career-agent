"""
indeed.py - Indeed Job Application Automation
Adapted from: beatwad/LinkedIn-AI-Job-Applier-Ultimate (MIT License)
Integrated with AI Career Agent's AIEngine, SkillAnalyzer, and DBManager.
"""

import os
import sys
import time
import random
import hashlib
import pickle
from typing import Optional

sys.stdout.reconfigure(encoding='utf-8')

import config
import utils
from ai_engine import AIEngine
from skill_analyzer import SkillAnalyzer
from db_manager import DBManager

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

try:
    from selenium_stealth import stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

# ── Validated Selectors (Adapted from beatwad/LinkedIn-AI-Job-Applier-Ultimate) ──
INDEED_APPLY_BUTTON_SELECTORS = [
    "span.indeed-apply-status-not-applied button",
    "button[aria-label*='Apply with Indeed']",
    "button[aria-label*='Indeed Apply']",
    "button#indeedApplyButton",
    ".ia-IndeedApplyButton",
    "button[data-testid='apply-button']",
    "a[data-testid='apply-button']",
]

INDEED_NEXT_BUTTON_SELECTORS = [
    "button[data-testid='continue-button']",
    "button[data-testid='ia-continueButton']",
    "button[data-testid='ia-submitButton']",
    "button[data-testid='submit-application-button']",
]

INDEED_SUBMIT_BUTTON_SELECTORS = [
    "button[data-testid='ia-submitButton']",
    "button.ia-submitButton",
    "button[data-testid='submit-application-button']",
]

INDEED_FORM_SECTION_SELECTORS = [
    "div.ia-Questions-item",
    "div[data-testid='ia-Questions-item']",
    "div.ia-Qual-Questions-item",
]


class Indeed:
    def __init__(self) -> None:
        utils.prYellow("🤖 AI Career Agent - Indeed Module")
        utils.prYellow("🌐 Bot will run in Chrome browser and log in to Indeed for you.")

        try:
            chrome_install = ChromeDriverManager().install()
            folder = os.path.dirname(chrome_install)
            chromedriver_path = os.path.join(folder, "chromedriver.exe")
            service = ChromeService(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=utils.chromeBrowserOptions())
        except Exception as e:
            if config.displayWarnings:
                utils.prYellow(f"⚠️ Warning: Could not use explicit chromedriver path: {str(e)[0:50]}")
            self.driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=utils.chromeBrowserOptions()
            )

        if STEALTH_AVAILABLE:
            try:
                stealth(self.driver,
                        languages=["en-US", "en"],
                        vendor="Google Inc.",
                        platform="Win32",
                        webgl_vendor="Intel Inc.",
                        renderer="Intel Iris OpenGL Engine",
                        fix_hairline=True)
            except Exception as e:
                utils.prYellow(f"⚠️ Warning: Could not apply stealth mode: {str(e)}")

        self.ai_engine = AIEngine()
        self.skill_analyzer = SkillAnalyzer()
        self.db = DBManager()
        self.resume_text = self._load_resume_text()

        self.cookies_path = f"{os.path.join(os.getcwd(), 'cookies')}/indeed_{self._get_hash(config.email)}.pkl"
        self.driver.get('https://www.indeed.com')
        self._load_cookies()

        if not self._is_logged_in():
            self._login()

    def _get_hash(self, string: str) -> str:
        return hashlib.md5(string.encode('utf-8')).hexdigest()

    def _load_resume_text(self) -> str:
        """Load resume text from a local file if available."""
        resume_path = getattr(config, 'resume_text_path', 'resume.txt')
        if os.path.exists(resume_path):
            with open(resume_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def _load_cookies(self) -> None:
        if os.path.exists(self.cookies_path):
            with open(self.cookies_path, "rb") as f:
                cookies = pickle.load(f)
            self.driver.delete_all_cookies()
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception:
                    pass

    def _save_cookies(self) -> None:
        try:
            cookies_dir = os.path.dirname(self.cookies_path)
            if cookies_dir and not os.path.exists(cookies_dir):
                os.makedirs(cookies_dir, exist_ok=True)
            with open(self.cookies_path, "wb") as f:
                pickle.dump(self.driver.get_cookies(), f)
        except Exception as e:
            if config.displayWarnings:
                utils.prYellow(f"⚠️ Warning: Could not save cookies: {str(e)[0:100]}")

    def _is_logged_in(self) -> bool:
        self.driver.get('https://www.indeed.com')
        try:
            self.driver.find_element(By.CSS_SELECTOR, '[data-testid="UserDropdown"]')
            return True
        except Exception:
            pass
        return False

    def _login(self) -> None:
        utils.prYellow("🔄 Trying to log in to Indeed...")
        self.driver.get("https://secure.indeed.com/auth?hl=en_US&co=US&continue=https%3A%2F%2Fwww.indeed.com%2F")
        try:
            email_field = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input#ifl-InputFormField-3"))
            )
            email_field.send_keys(config.email)
            time.sleep(1)
            continue_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button.css-1oq9dqq")
            continue_btn.click()
            time.sleep(2)
            password_field = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            password_field.send_keys(config.password)
            time.sleep(1)
            sign_in_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            sign_in_btn.click()
            time.sleep(5)
            self._save_cookies()
            utils.prGreen("✅ Logged in to Indeed successfully.")
        except Exception as e:
            utils.prRed(f"❌ Could not log in to Indeed: {str(e)[0:100]}")
            utils.prYellow("💡 Tip: Try logging in manually and using chromeProfilePath in config.py")

    def _build_search_url(self, keyword: str, location: str) -> str:
        """Build an Indeed search URL with filters."""
        base = "https://www.indeed.com/jobs"
        params = f"?q={keyword.replace(' ', '+')}&l={location.replace(' ', '+')}"
        params += "&fromage=7"  # Past week
        params += "&sc=0kf%3Aattr(DSQF7)%3B"  # Easy Apply filter
        return base + params

    def _get_job_description(self) -> str:
        """Extract the job description from the current page."""
        try:
            jd_element = self.driver.find_element(By.CSS_SELECTOR,
                "#jobDescriptionText, div[data-testid='jobsearch-JobComponent-description']")
            return jd_element.text
        except Exception:
            return ""

    def _find_apply_button(self) -> Optional[object]:
        """Find the Indeed Easy Apply button using validated selectors."""
        for selector in INDEED_APPLY_BUTTON_SELECTORS:
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                if btn.is_displayed():
                    return btn
            except Exception:
                continue
        return None

    def _fill_text_fields(self) -> None:
        """Fill text input fields using AI if available."""
        try:
            text_inputs = self.driver.find_elements(By.CSS_SELECTOR,
                "input[type='text']:not([readonly]), input[type='number']:not([readonly]), textarea:not([readonly])")
            for field in text_inputs:
                if not field.is_displayed():
                    continue
                current_val = field.get_attribute("value") or ""
                if current_val.strip():
                    continue
                # Try to find the label for this field
                field_id = field.get_attribute("id")
                question_text = ""
                if field_id:
                    try:
                        label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{field_id}']")
                        question_text = label.text.strip()
                    except Exception:
                        pass
                if question_text and self.ai_engine.enabled and self.resume_text:
                    answer = self.ai_engine.answer_question(self.resume_text, "", question_text)
                    if answer:
                        field.clear()
                        field.send_keys(answer[:500])
                        time.sleep(0.3)
        except Exception as e:
            if config.displayWarnings:
                utils.prYellow(f"⚠️ Warning in _fill_text_fields: {str(e)[0:50]}")

    def _fill_dropdowns(self) -> None:
        """Fill dropdown fields using AI if available."""
        try:
            selects = self.driver.find_elements(By.CSS_SELECTOR, "select")
            for sel in selects:
                if not sel.is_displayed():
                    continue
                select_obj = Select(sel)
                if select_obj.first_selected_option.get_attribute("value"):
                    continue
                options = [o.text for o in select_obj.options if o.get_attribute("value")]
                if not options:
                    continue
                # Default: select first non-empty option
                select_obj.select_by_index(1)
        except Exception as e:
            if config.displayWarnings:
                utils.prYellow(f"⚠️ Warning in _fill_dropdowns: {str(e)[0:50]}")

    def _click_next_or_submit(self) -> bool:
        """Click the next or submit button. Returns True if submit was clicked."""
        for selector in INDEED_SUBMIT_BUTTON_SELECTORS:
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                if btn.is_displayed():
                    btn.click()
                    return True
            except Exception:
                continue

        for selector in INDEED_NEXT_BUTTON_SELECTORS:
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                if btn.is_displayed():
                    btn.click()
                    return False
            except Exception:
                continue
        return False

    def _apply_to_job(self, job_id: str, job_title: str, company: str, location: str, url: str) -> str:
        """Attempt to apply to a single Indeed job. Returns status string."""
        jd_text = self._get_job_description()

        # AI Scoring
        ats_score = None
        ats_reason = None
        if self.ai_engine.enabled and self.resume_text and jd_text:
            score_data = self.ai_engine.get_ats_score(self.resume_text, jd_text)
            ats_score = score_data.get('score', 1)
            ats_reason = score_data.get('reason', '')
            utils.prYellow(f"🤖 AI Score: {ats_score}/5 - {ats_reason}")
            if ats_score < getattr(config, 'min_ats_score', 3):
                utils.prYellow(f"⏭️ Skipping (score too low): {job_title}")
                self.db.log_application(job_id, job_title, company, location, url,
                                        ats_score, ats_reason, status="Skipped")
                return "Skipped"

        # Skill Gap Analysis
        if jd_text:
            jd_skills = self.skill_analyzer.extract_skills_from_jd(jd_text)
            if jd_skills and self.resume_text:
                gap_result = self.skill_analyzer.analyze_gaps(jd_skills, self.resume_text)
                gaps = gap_result.get('gaps', [])
                if len(gaps) > getattr(config, 'max_skill_gaps', 5):
                    utils.prYellow(f"⏭️ Skipping (too many gaps: {gaps}): {job_title}")
                    self.db.log_application(job_id, job_title, company, location, url,
                                            ats_score, f"Too many gaps: {gaps}", status="Skipped")
                    return "Skipped"

        apply_btn = self._find_apply_button()
        if not apply_btn:
            utils.prYellow(f"⏭️ No Easy Apply button found for: {job_title}")
            self.db.log_application(job_id, job_title, company, location, url,
                                    ats_score, ats_reason, status="No Easy Apply")
            return "No Easy Apply"

        apply_btn.click()
        time.sleep(random.uniform(1, 2))

        # Multi-step form filling
        for step in range(10):
            self._fill_text_fields()
            self._fill_dropdowns()
            time.sleep(random.uniform(0.5, 1))

            if config.dryRun:
                utils.prYellow(f"🧪 DRY RUN - Would apply to: {url}")
                self.db.log_application(job_id, job_title, company, location, url,
                                        ats_score, ats_reason, status="Dry Run")
                return "Dry Run"

            submitted = self._click_next_or_submit()
            time.sleep(random.uniform(1, 2))
            if submitted:
                utils.prGreen(f"✅ Applied to: {job_title} at {company}")
                self.db.log_application(job_id, job_title, company, location, url,
                                        ats_score, ats_reason, status="Applied")
                return "Applied"

        self.db.log_application(job_id, job_title, company, location, url,
                                ats_score, ats_reason, status="Failed")
        return "Failed"

    def run(self) -> None:
        """Main loop: search and apply to Indeed jobs."""
        count_applied = 0
        count_total = 0

        indeed_keywords = getattr(config, 'indeed_keywords', config.keywords)
        indeed_locations = getattr(config, 'indeed_locations', config.location)

        for keyword in indeed_keywords:
            for location in indeed_locations:
                url = self._build_search_url(keyword, location)
                self.driver.get(url)
                time.sleep(random.uniform(2, 3))

                job_cards = self.driver.find_elements(By.CSS_SELECTOR,
                    "div.job_seen_beacon, div[data-testid='slider_item']")

                utils.prYellow(f"🔍 Found {len(job_cards)} jobs for '{keyword}' in '{location}'")

                for card in job_cards:
                    if getattr(config, 'maxApplicationsPerRun', 0) and count_applied >= config.maxApplicationsPerRun:
                        utils.prYellow(f"🛑 Reached max applications limit ({config.maxApplicationsPerRun}). Stopping.")
                        return

                    try:
                        job_id = card.get_attribute("data-jk") or str(count_total)
                        title_el = card.find_element(By.CSS_SELECTOR, "h2.jobTitle a, [data-testid='jobTitle']")
                        job_title = title_el.text.strip()
                        job_url = "https://www.indeed.com/viewjob?jk=" + job_id

                        try:
                            company_el = card.find_element(By.CSS_SELECTOR, "[data-testid='company-name'], .companyName")
                            company = company_el.text.strip()
                        except Exception:
                            company = "Unknown"

                        count_total += 1
                        utils.prYellow(f"\n{count_total} | {job_title} | {company}")

                        self.driver.get(job_url)
                        time.sleep(random.uniform(1, 2))

                        status = self._apply_to_job(job_id, job_title, company, location, job_url)
                        if status == "Applied":
                            count_applied += 1

                    except Exception as e:
                        if config.displayWarnings:
                            utils.prYellow(f"⚠️ Error processing job card: {str(e)[0:80]}")
                        continue

        utils.prGreen(f"\n✅ Indeed Session Complete: Applied to {count_applied}/{count_total} jobs.")


def main() -> None:
    bot = Indeed()
    bot.run()


if __name__ == "__main__":
    main()