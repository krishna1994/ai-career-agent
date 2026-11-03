import hashlib
import math
import os
import pickle
import random
import ssl
import sys
import time
from typing import Optional

# Fix for corporate SSL proxy (self-signed certificate) - must be set BEFORE webdriver_manager imports
os.environ['WDM_SSL_VERIFY'] = '0'
ssl._create_default_https_context = ssl._create_unverified_context

import config
import constants
import utils
from question_answerer import QuestionAnswerer
from ai_engine import AIEngine
from skill_analyzer import SkillAnalyzer
from db_manager import DBManager

sys.stdout.reconfigure(encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

try:
    from selenium_stealth import stealth
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

class Linkedin:
    def __init__(self, on_log=None, on_screenshot=None, on_stats=None, stop_flag=None) -> None:
        """
        Optional GUI integration hooks (all default to no-ops so the bot
        behaves identically when run from the command line):

        - on_log(message: str): called every time a line would be printed
          to the console, so a GUI can mirror it into a live log view.
        - on_screenshot(path: str): called every time a screenshot is
          saved, so a GUI can display it immediately (e.g. in a gallery).
        - on_stats(stats: dict): called periodically with running counters
          (jobs processed/applied/skipped/etc.) so a GUI can show live
          progress without parsing log text.
        - stop_flag: an object with an `.is_set()` method (e.g.
          `threading.Event`). Checked at multiple points in the main loop;
          if set, the run stops gracefully at the next safe checkpoint
          instead of mid-click. Allows a GUI "Stop" button to work
          without killing the browser process abruptly.
        """
        self.on_log = on_log or (lambda msg: None)
        self.on_screenshot = on_screenshot or (lambda path: None)
        self.on_stats = on_stats or (lambda stats: None)
        self.stop_flag = stop_flag
        utils.prYellow("🤖 Thanks for using AI Career Agent.")
        utils.prYellow("🌐 Bot will run in Chrome browser and log in Linkedin for you.")
        
        # Fix for WinError 193: Explicitly construct chromedriver path
        try:
            chrome_install = ChromeDriverManager().install()
            folder = os.path.dirname(chrome_install)
            chromedriver_path = os.path.join(folder, "chromedriver.exe")
            service = ChromeService(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=utils.chromeBrowserOptions())
        except Exception as e:
            # Fallback to original method if explicit path fails
            if config.displayWarnings:
                utils.prYellow(f"⚠️ Warning: Could not use explicit chromedriver path, using default: {str(e)[0:50]}")
            self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=utils.chromeBrowserOptions())

        # Avoid multi-minute hangs if a page gets stuck loading (e.g. a
        # LinkedIn bot-check / security checkpoint page that never fires
        # its 'load' event). 45s is generous for a normal page but short
        # enough to fail fast instead of blocking for the full urllib3
        # default timeout.
        try:
            self.driver.set_page_load_timeout(45)
        except Exception:
            pass

        # Apply stealth mode if available
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
        
        self.question_answerer = QuestionAnswerer()

        # AI features (ATS scoring, resume tailoring, AI question
        # answering) -- same engine already used by indeed.py. Loading
        # these here is cheap/safe even when config.use_ai_features is
        # False, since AIEngine itself checks self.enabled before making
        # any API calls.
        self.ai_engine = AIEngine()
        self.skill_analyzer = SkillAnalyzer()
        self.db = DBManager()
        self.resume_text = getattr(config, 'resumeText', '') or ''
        # Tracks the JD text + tailored resume for whichever job is
        # currently being processed, set in getJobProperties()/the main
        # loop right before the Easy Apply flow runs.
        self._current_jd_text = ""
        self._current_tailored_resume = None

        self.cookies_path = f"{os.path.join(os.getcwd(),'cookies')}/{self.getHash(config.email)}.pkl"
        self.driver.get('https://www.linkedin.com')
        self.loadCookies()

        if not self.isLoggedIn():
            self.driver.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
            utils.prYellow("🔄 Trying to log in Linkedin...")
            try:    
                self.driver.find_element("id","username").send_keys(config.email)
                time.sleep(2)
                self.driver.find_element("id","password").send_keys(config.password)
                time.sleep(2)
                self.driver.find_element("xpath",'//button[@type="submit"]').click()
                time.sleep(30)
            except Exception:
                utils.prRed("❌ Couldn't log in Linkedin by using Chrome. Please check your Linkedin credentials on config files line 7 and 8.")

            self.saveCookies()

    def getHash(self, string: str) -> str:
        return hashlib.md5(string.encode('utf-8')).hexdigest()

    def loadCookies(self) -> None:
        if os.path.exists(self.cookies_path):
            with open(self.cookies_path, "rb") as f:
                cookies = pickle.load(f)
            self.driver.delete_all_cookies()
            added = 0
            failed = 0
            for cookie in cookies:
                # Selenium's add_cookie() is picky about extra/incompatible
                # keys (e.g. 'sameSite' values it doesn't recognize, or a
                # float 'expiry'). A single bad cookie must not abort
                # restoration of the rest, so we add them one at a time
                # with per-cookie error handling, sanitizing common issues.
                try:
                    clean_cookie = dict(cookie)
                    # Selenium expects 'expiry' as an int, not a float.
                    if isinstance(clean_cookie.get('expiry'), float):
                        clean_cookie['expiry'] = int(clean_cookie['expiry'])
                    # Remove keys Selenium's add_cookie() doesn't accept.
                    clean_cookie.pop('sameSite', None)
                    clean_cookie.pop('storeId', None)
                    clean_cookie.pop('id', None)
                    self.driver.add_cookie(clean_cookie)
                    added += 1
                except Exception as e:
                    failed += 1
                    if config.displayWarnings:
                        utils.prYellow(f"⚠️ Warning: Could not restore cookie '{cookie.get('name')}': {str(e)[0:80]}")
            if config.displayWarnings:
                utils.prYellow(f"ℹ️ Restored {added} cookies, {failed} failed.")

    def saveCookies(self) -> None:
        try:
            # Get the directory path for cookies
            cookies_dir = os.path.dirname(self.cookies_path)
            
            # Create cookies directory if it doesn't exist
            if cookies_dir and not os.path.exists(cookies_dir):
                os.makedirs(cookies_dir, exist_ok=True)
            
            # Save cookies to file
            with open(self.cookies_path, "wb") as f:
                pickle.dump(self.driver.get_cookies(), f)
        except Exception as e:
            if config.displayWarnings:
                utils.prYellow(f"⚠️ Warning: Could not save cookies: {str(e)[0:100]}")
            # Don't raise the exception - cookie saving is not critical for bot operation
    
    def isLoggedIn(self) -> bool:
        # Dynamic ember IDs (e.g. 'ember14') are unreliable across sessions
        # and LinkedIn UI versions, so primarily check for the 'li_at' auth
        # cookie LinkedIn sets once a session is authenticated (works for
        # email/password login AND SSO logins like 'Sign in with Google').
        try:
            cookies = self.driver.get_cookies()
            if any(c.get('name') == 'li_at' for c in cookies):
                return True
        except Exception:
            pass

        # Fallback: check for UI elements that only exist when logged in.
        self.driver.get('https://www.linkedin.com/feed')
        try:
            self.driver.find_element(By.CSS_SELECTOR, "input.search-global-typeahead__input")
            return True
        except Exception:
            pass
        try:
            self.driver.find_element(By.XPATH, '//*[@id="ember14"]')
            return True
        except Exception:
            pass
        return False 
    
    def generateUrls(self) -> None:
        if not os.path.exists('data'):
            os.makedirs('data')
        try: 
            with open('data/urlData.txt', 'w',encoding="utf-8" ) as file:
                linkedinJobLinks = utils.LinkedinUrlGenerate().generateUrlLinks()
                for url in linkedinJobLinks:
                    file.write(url+ "\n")
            utils.prGreen("✅ Apply urls are created successfully, now the bot will visit those urls.")
        except Exception:
            utils.prRed("❌ Couldn't generate urls, make sure you have editted config file line 25-39")

    def linkJobApply(self) -> None:
        self.generateUrls()
        countApplied = 0
        countJobs = 0
        countBlacklisted = 0
        countAlreadyApplied = 0
        countCannotApply = 0
        startTime = time.time()
        reachedCap = False

        urlData = utils.getUrlDataFile()

        for url in urlData:        
            try:
                self.driver.get(url)
            except Exception as e:
                # A page-load timeout (e.g. LinkedIn bot-check/CAPTCHA page
                # that never finishes loading) must not crash the whole
                # run. Skip this search URL and move on to the next one.
                if config.displayWarnings:
                    utils.prYellow(f"⚠️ Warning: Page load failed for {url[0:80]}: {str(e)[0:80]}")
                try:
                    self.driver.execute_script("window.stop();")
                except Exception:
                    pass
                continue
            time.sleep(random.uniform(1, constants.botSpeed))

            # Handle case where no jobs are found (//small element doesn't exist)
            try:
                totalJobs = self.driver.find_element(By.XPATH,'//small').text 
            except Exception as e:
                urlWords = utils.urlToKeywords(url)
                lineToWrite = "\n Category: " + urlWords[0] + ", Location: " + urlWords[1] + ", No jobs found for this search criteria. Skipping..."
                self.displayWriteResults(lineToWrite)
                if config.displayWarnings:
                    utils.prYellow(f"⚠️ Warning: No jobs found for {urlWords[0]} in {urlWords[1]}. The //small element was not found.")
                continue  # Skip to next URL

            totalPages = utils.jobsToPages(totalJobs)

            urlWords =  utils.urlToKeywords(url)
            lineToWrite = "\n Category: " + urlWords[0] + ", Location: " +urlWords[1] + ", Applying " +str(totalJobs)+ " jobs."
            self.displayWriteResults(lineToWrite)

            for page in range(totalPages):
                currentPageJobs = constants.jobsPerPage * page
                url = url +"&start="+ str(currentPageJobs)
                try:
                    self.driver.get(url)
                except Exception as e:
                    if config.displayWarnings:
                        utils.prYellow(f"⚠️ Warning: Page load failed for {url[0:80]}: {str(e)[0:80]}")
                    try:
                        self.driver.execute_script("window.stop();")
                    except Exception:
                        pass
                    continue
                time.sleep(random.uniform(1, constants.botSpeed))

                offersPerPage = self.driver.find_elements(By.XPATH, '//li[@data-occludable-job-id]')
                offerIds = []
                
                # Extract all offer IDs immediately to avoid stale element references
                for offer in offersPerPage:
                    try:
                        offerId = offer.get_attribute("data-occludable-job-id")
                        if offerId:
                            offerIds.append(int(offerId.split(":")[-1]))
                    except Exception as e:
                        if config.displayWarnings:
                            utils.prYellow(f"⚠️ Warning: Could not get offer ID: {str(e)[0:50]}")
                        continue
                
                time.sleep(random.uniform(1, constants.botSpeed))
                
                # Check for "Applied" status by re-finding elements to avoid stale references
                try:
                    offersPerPage = self.driver.find_elements(By.XPATH, '//li[@data-occludable-job-id]')
                    appliedOfferIds = []
                    for offer in offersPerPage:
                        try:
                            if self.element_exists(offer, By.XPATH, ".//*[contains(text(), 'Applied')]"):
                                offerId = offer.get_attribute("data-occludable-job-id")
                                if offerId:
                                    appliedOfferIds.append(int(offerId.split(":")[-1]))
                        except Exception:
                            continue
                    # Remove already applied jobs from the list
                    offerIds = [jobId for jobId in offerIds if jobId not in appliedOfferIds]
                except Exception as e:
                    if config.displayWarnings:
                        utils.prYellow(f"⚠️ Warning: Could not check applied status: {str(e)[0:50]}")

                for jobID in offerIds:
                    if self.shouldStop():
                        reachedCap = True
                        break

                    offerPage = 'https://www.linkedin.com/jobs/view/' + str(jobID)
                    self.driver.get(offerPage)
                    time.sleep(random.uniform(1, constants.botSpeed))

                    countJobs += 1
                    self.on_stats({
                        "jobs_processed": countJobs,
                        "applied": countApplied,
                        "blacklisted": countBlacklisted,
                        "already_applied": countAlreadyApplied,
                        "cannot_apply": countCannotApply,
                    })

                    # Safety cap for this test run: stop after processing a
                    # fixed number of job postings (dry-run testing only).
                    max_jobs_to_process = getattr(config, 'maxJobsToProcess', 0)
                    if max_jobs_to_process and countJobs > max_jobs_to_process:
                        reachedCap = True
                        break

                    jobProperties = self.getJobProperties(countJobs)

                    # --- AI-powered ATS scoring gate (optional) ---
                    # Mirrors indeed.py's behavior: if AI features are
                    # enabled (config.use_ai_features) AND a plain-text
                    # resume is configured (config.resumeText), extract
                    # the job description and score the fit before
                    # bothering to click Easy Apply. Jobs below
                    # config.min_ats_score are skipped and logged to the
                    # SQLite database (data/applications.db) for review.
                    # If AI features are off or no resumeText is set,
                    # this step is a no-op and behavior is unchanged.
                    jdText = ""
                    atsScore = None
                    atsReason = None
                    if self.ai_engine.enabled and self.resume_text:
                        jdText = self.getJobDescription()
                        if jdText:
                            scoreData = self.ai_engine.get_ats_score(self.resume_text, jdText)
                            atsScore = scoreData.get('score', 1)
                            atsReason = scoreData.get('reason', '')
                            utils.prYellow(f"🤖 AI ATS Score: {atsScore}/5 - {atsReason}")
                            minAtsScore = getattr(config, 'min_ats_score', 3)
                            if atsScore < minAtsScore:
                                lineToWrite = jobProperties + " | " + f"* ⏭️ Skipped (AI ATS score {atsScore}/5 below threshold {minAtsScore}): " + str(offerPage)
                                self.displayWriteResults(lineToWrite)
                                try:
                                    self.db.log_application(
                                        str(jobID), jobProperties, "", "", offerPage,
                                        atsScore, atsReason, status="Skipped",
                                    )
                                except Exception:
                                    pass
                                continue

                            # Optional skill-gap check, same as indeed.py:
                            # jobs with too many missing skills (relative
                            # to config.max_skill_gaps) are also skipped.
                            try:
                                jdSkills = self.skill_analyzer.extract_skills_from_jd(jdText)
                                if jdSkills:
                                    gapResult = self.skill_analyzer.analyze_gaps(jdSkills, self.resume_text)
                                    gaps = gapResult.get('gaps', [])
                                    maxGaps = getattr(config, 'max_skill_gaps', 5)
                                    if len(gaps) > maxGaps:
                                        lineToWrite = jobProperties + " | " + f"* ⏭️ Skipped (too many skill gaps: {gaps}): " + str(offerPage)
                                        self.displayWriteResults(lineToWrite)
                                        try:
                                            self.db.log_application(
                                                str(jobID), jobProperties, "", "", offerPage,
                                                atsScore, f"Too many gaps: {gaps}", status="Skipped",
                                            )
                                        except Exception:
                                            pass
                                        continue
                            except Exception:
                                pass
                    self._current_jd_text = jdText

                    # Fallback used by question_answerer.answer_all() for
                    # any text question with no static keyword match in
                    # additionalQuestions.yaml/my_answers.yaml -- only
                    # engages if AI features + resumeText are configured.
                    def aiAnswerFn(questionText: str, _jd=jdText):
                        if self.ai_engine.enabled and self.resume_text:
                            try:
                                return self.ai_engine.answer_question(self.resume_text, _jd, questionText)
                            except Exception:
                                return None
                        return None

                    # Country/location gate: skip jobs whose displayed
                    # location doesn't match any of config.allowedCountries.
                    # This is enforced AFTER fetching the page because
                    # LinkedIn's search-level location parameter only
                    # reliably narrows results for recognized continents or
                    # LinkedIn-autocompleted place names -- generic values
                    # like "Remote" pass through to LinkedIn's search as a
                    # literal (and largely ignored) keyword, which is why
                    # jobs from unrelated countries were showing up.
                    allowed_countries = getattr(config, 'allowedCountries', [])
                    if allowed_countries and not self.isLocationAllowed(allowed_countries):
                        lineToWrite = jobProperties + " | " + "* 🌍 Skipped (location not in allowedCountries): " + str(offerPage)
                        self.displayWriteResults(lineToWrite)
                        continue

                    if "blacklisted" in jobProperties: 
                        countBlacklisted += 1
                        lineToWrite = jobProperties + " | " + "* 🤬 Blacklisted Job, skipped!: " +str(offerPage)
                        self.displayWriteResults(lineToWrite)
                    
                    else :                    
                        easyApplybutton = self.easyApplyButton()

                        if easyApplybutton is not None:
                            easyApplybutton.click()
                            time.sleep(random.uniform(1, constants.botSpeed))

                            # Capture the Easy Apply modal immediately after
                            # opening it, regardless of what happens in the
                            # subsequent steps. This guarantees we have
                            # visual evidence of the application attempt
                            # even if later selectors fail.
                            self.takeScreenshot(f"job_{countJobs}_{jobID}_easy_apply_modal")

                            # Fix for issue #72: LinkedIn added an extra "Continue to next step" button after Easy Apply
                            try:
                                continue_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']")
                                if continue_button.is_displayed():
                                    continue_button.click()
                                    time.sleep(random.uniform(1, constants.botSpeed))
                            except Exception:
                                # If button doesn't exist, continue normally
                                pass
                            
                            try:
                                self.chooseResume()
                                # Fill phone number and answer any custom
                                # application questions before submitting.
                                self.fillPhoneNumber()
                                answered = self.question_answerer.answer_all(self.driver, ai_answer_fn=aiAnswerFn)
                                if config.displayWarnings and any(answered.values()):
                                    utils.prGreen(f"✅ Answered questions: {answered}")

                                if config.dryRun:
                                    # In dry-run mode, do not submit the application,
                                    # just log that we would have applied.
                                    self.takeScreenshot(f"job_{countJobs}_{jobID}_before_submit")
                                    lineToWrite = jobProperties + " | " + "* 🧪 DRY RUN - Would apply to this job: "  + str(offerPage)
                                    self.displayWriteResults(lineToWrite)
                                    if atsScore is not None:
                                        try:
                                            self.db.log_application(
                                                str(jobID), jobProperties, "", "", offerPage,
                                                atsScore, atsReason, status="Dry Run",
                                            )
                                        except Exception:
                                            pass
                                else:
                                    self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']").click()
                                    time.sleep(random.uniform(1, constants.botSpeed))

                                    lineToWrite = jobProperties + " | " + "* 🥳 Just Applied to this job: "  + str(offerPage)
                                    self.displayWriteResults(lineToWrite)
                                    countApplied += 1
                                    if atsScore is not None:
                                        try:
                                            self.db.log_application(
                                                str(jobID), jobProperties, "", "", offerPage,
                                                atsScore, atsReason, status="Applied",
                                            )
                                        except Exception:
                                            pass
                                    if config.maxApplicationsPerRun and countApplied >= config.maxApplicationsPerRun:
                                        reachedCap = True

                            except Exception:
                                try:
                                    # Fill phone number and answer questions
                                    # before continuing to the next step.
                                    self.fillPhoneNumber()
                                    self.question_answerer.answer_all(self.driver, ai_answer_fn=aiAnswerFn)
                                    self.driver.find_element(By.CSS_SELECTOR,"button[aria-label='Continue to next step']").click()
                                    time.sleep(random.uniform(1, constants.botSpeed))
                                    self.chooseResume()
                                    comPercentage = self.driver.find_element(By.XPATH,'html/body/div[3]/div/div/div[2]/div/div/span').text
                                    percenNumber = int(comPercentage[0:comPercentage.index("%")])
                                    
                                    # For multi-step forms, respect dry-run as well.
                                    if config.dryRun:
                                        self.takeScreenshot(f"job_{countJobs}_{jobID}_multistep_before_submit")
                                        result = "* 🧪 DRY RUN - Would go through multi-step application: " + str(offerPage)
                                    else:
                                        result = self.applyProcess(percenNumber, offerPage, ai_answer_fn=aiAnswerFn)

                                    lineToWrite = jobProperties + " | " + result
                                    self.displayWriteResults(lineToWrite)
                                    if "Just Applied" in result and not config.dryRun:
                                        countApplied += 1
                                        if atsScore is not None:
                                            try:
                                                self.db.log_application(
                                                    str(jobID), jobProperties, "", "", offerPage,
                                                    atsScore, atsReason, status="Applied",
                                                )
                                            except Exception:
                                                pass
                                        if config.maxApplicationsPerRun and countApplied >= config.maxApplicationsPerRun:
                                            reachedCap = True
                                
                                except Exception: 
                                    countCannotApply += 1
                                    self.chooseResume()
                                    lineToWrite = jobProperties + " | " + "* 🥵 Cannot apply to this Job! " +str(offerPage)
                                    self.displayWriteResults(lineToWrite)
                        else:
                            countAlreadyApplied += 1
                            lineToWrite = jobProperties + " | " + "* 🥳 Already applied! Job: " +str(offerPage)
                            self.displayWriteResults(lineToWrite)

                    if reachedCap:
                        break
                if reachedCap:
                    break
            if reachedCap:
                break

            utils.prYellow("Category: " + urlWords[0] + "," +urlWords[1]+ " applied: " + str(countApplied) +
                  " jobs out of " + str(countJobs) + ".")
        
        if reachedCap:
            utils.prYellow("🛑 Reached max applications per run limit (" + str(config.maxApplicationsPerRun) + "). Stopping.")
        durationSec = time.time() - startTime
        utils.printSessionSummary(
            countJobs, countApplied, countBlacklisted, countAlreadyApplied, countCannotApply, durationSec
        )
        self.on_stats({
            "jobs_processed": countJobs,
            "applied": countApplied,
            "blacklisted": countBlacklisted,
            "already_applied": countAlreadyApplied,
            "cannot_apply": countCannotApply,
            "finished": True,
            "duration_sec": durationSec,
        })

    def chooseResume(self) -> None:
        """Handle the Easy Apply resume-selection/upload step.

        Two distinct cases exist on LinkedIn's Easy Apply forms:
        1. The applicant has one or more resumes already uploaded to their
           LinkedIn profile -- LinkedIn shows them as selectable cards and
           the bot picks one based on `config.preferredCv` (1-indexed).
        2. The form instead (or additionally) shows a raw file-upload
           input (some third-party/first-time flows do this). If
           `config.resumePath` points to a real local PDF/DOCX file, we
           upload it directly via Selenium's send_keys() on the hidden
           <input type="file">, which works without needing to click
           anything first.
        """
        # Case 2: a local resume file was configured and a file input
        # exists on the current step -- upload it. This is attempted
        # first (and independently of Case 1) since some forms show both
        # a "Upload resume" button and previously-uploaded resume cards.
        resume_path = getattr(config, 'resumePath', '') or ''
        if resume_path and os.path.exists(resume_path):
            try:
                file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                for file_input in file_inputs:
                    try:
                        file_input.send_keys(os.path.abspath(resume_path))
                        if config.displayWarnings:
                            utils.prGreen(f"✅ Uploaded resume file: {resume_path}")
                        time.sleep(1)
                        break
                    except Exception:
                        continue
            except Exception:
                pass

        # Case 1: select among resumes already uploaded to the LinkedIn
        # profile.
        try:
            self.driver.find_element(
                By.CLASS_NAME, "jobs-document-upload__title--is-required")
            resumes = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'ui-attachment--pdf')]")
            if (len(resumes) == 1 and resumes[0].get_attribute("aria-label") == "Select this resume"):
                resumes[0].click()
            elif (len(resumes) > 1 and resumes[config.preferredCv-1].get_attribute("aria-label") == "Select this resume"):
                resumes[config.preferredCv-1].click()
            elif (type(len(resumes)) != int):
                utils.prRed(
                    "❌ No resume has been selected please add at least one resume to your Linkedin account.")
        except Exception:
            pass

    def getJobProperties(self, count: int) -> str:
        textToWrite = ""
        jobTitle = ""
        jobLocation = ""

        # LinkedIn's job-page class names are build-hashed and change
        # frequently (e.g. 'b6bhc3'), so a semantic class like 'job-title'
        # no longer exists. The browser <title> tag reliably follows the
        # pattern "Job Title | Company | LinkedIn" regardless of markup
        # changes, so we parse it as our primary source, falling back to
        # the legacy class-based selector for older page layouts.
        try:
            page_title = self.driver.title or ""
            if "|" in page_title:
                jobTitle = page_title.split("|")[0].strip()
            else:
                jobTitle = page_title.strip()
            if not jobTitle:
                raise ValueError("Empty title")
            res = [blItem for blItem in config.blackListTitles if (blItem.lower() in jobTitle.lower())]
            if (len(res) > 0):
                jobTitle += "(blacklisted title: " + ' '.join(res) + ")"
        except Exception as e:
            if (config.displayWarnings):
                utils.prYellow("⚠️ Warning getting jobTitle from <title>, trying legacy selector: " + str(e)[0:50])
            try:
                jobTitle = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'job-title')]").get_attribute("innerHTML").strip()
            except Exception as e2:
                if (config.displayWarnings):
                    utils.prYellow("⚠️ Warning in getting jobTitle: " + str(e2)[0:50])
                jobTitle = ""

        # Company name is the second segment of the <title> tag
        # ("Job Title | Company | LinkedIn"); use it for blacklist
        # checking since the old 'job-details-jobs' class no longer
        # exists on the page.
        try:
            page_title = self.driver.title or ""
            parts = [p.strip() for p in page_title.split("|")]
            jobDetail = parts[1] if len(parts) > 1 else ""
            res = [blItem for blItem in config.blacklistCompanies if (blItem.lower() in jobDetail.lower())]
            if (len(res) > 0):
                jobDetail += "(blacklisted company: " + ' '.join(res) + ")"
        except Exception as e:
            if (config.displayWarnings):
                utils.prYellow("⚠️ Warning in getting jobDetail: " + str(e)[0:100])
            jobDetail = ""

        try:
            jobWorkStatusSpans = self.driver.find_elements(By.XPATH, "//span[contains(@class,'ui-label ui-label--accent-3 text-body-small')]//span[contains(@aria-hidden,'true')]")
            for span in jobWorkStatusSpans:
                jobLocation = jobLocation + " | " + span.text

        except Exception as e:
            if (config.displayWarnings):
                print(e)
                utils.prYellow("⚠️ Warning in getting jobLocation: " + str(e)[0:100])
            jobLocation = ""

        textToWrite = str(count) + " | " + jobTitle +" | " + jobDetail + jobLocation
        return textToWrite

    def getJobDescription(self) -> str:
        """Best-effort extraction of the job description text from the
        current LinkedIn job page, for use with AIEngine (ATS scoring,
        resume tailoring, question answering) and SkillAnalyzer (skill
        gap analysis). LinkedIn's class names are build-hashed and
        change frequently, so several selectors are tried in order of
        reliability; failures are non-fatal (an empty string disables
        the AI steps for that job, same as if AI features were off).
        """
        selectors = [
            (By.ID, "job-details"),
            (By.CSS_SELECTOR, "div.jobs-description__content"),
            (By.CSS_SELECTOR, "div.jobs-box__html-content"),
            (By.XPATH, "//div[contains(@class,'jobs-description')]"),
        ]
        for by, selector in selectors:
            try:
                el = self.driver.find_element(by, selector)
                text = el.text.strip()
                if text:
                    return text
            except Exception:
                continue
        return ""

    def isLocationAllowed(self, allowed_countries: list) -> bool:
        """Check whether the current job posting's displayed location
        matches one of the configured allowed countries/keywords.

        LinkedIn renders the job location as plain text inside the page's
        <main> content block (e.g. "Fixed Income Financing Quant VP,
        London Area, United Kingdom" or "...,  · 1 hour ago · 0
        applicants" right below the title/company). This text survives
        LinkedIn's CSS-class hashing (unlike class-name selectors), so we
        extract it and do a case-insensitive substring match against each
        configured allowed country/keyword.

        Returns True if no location text could be extracted at all (fails
        open, so a parsing hiccup doesn't block applications entirely --
        the allowedCountries filter is a best-effort safety net, not the
        only line of defense).
        """
        try:
            main_text = self.driver.find_element(By.XPATH, "//main").text
        except Exception:
            try:
                main_text = self.driver.find_element(By.TAG_NAME, "body").text
            except Exception:
                return True  # Could not read page text at all; fail open.

        if not main_text:
            return True

        # The location line typically appears within the first ~500
        # characters of the main content, right after the job title and
        # company name, so limit our search window to reduce the chance
        # of false-positive matches from unrelated text further down the
        # page (e.g. a company's "About" section mentioning other
        # countries where they have offices).
        search_window = main_text[:600].lower()

        for country in allowed_countries:
            if country.strip().lower() in search_window:
                return True
        return False

    def easyApplyButton(self) -> Optional[webdriver.remote.webelement.WebElement]:
        """Find the Easy Apply button on a job page.

        LinkedIn now ships build-hashed/obfuscated CSS class names (e.g.
        'b6bhc3') that change on every deploy, so matching on class names
        is unreliable. The 'aria-label' attribute on the button is far
        more stable since it's tied to accessibility semantics rather than
        styling, so we match on that instead.
        """
        try:
            time.sleep(random.uniform(1, constants.botSpeed))
            # Primary: stable aria-label used by LinkedIn's current markup.
            button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Easy Apply to this job']")
            return button
        except Exception:
            pass
        try:
            # Fallback: some pages use slightly different aria-label text
            # or rely on the visible button text instead.
            button = self.driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]")
            return button
        except Exception:
            pass
        try:
            # Legacy fallback for older/less-common page layouts that may
            # still use the original class-based markup.
            button = self.driver.find_element(By.XPATH, "//div[contains(@class,'jobs-apply-button--top-card')]//button[contains(@class, 'jobs-apply-button')]")
            return button
        except Exception:
            pass
        return None

    def fillPhoneNumber(self) -> None:
        """Fill phone number fields if they exist and are empty"""
        try:
            # Get phone number from config or additionalQuestions.yaml
            phone_number = ""
            
            # Try to get from config.Phone first
            if hasattr(config, 'Phone') and config.Phone and config.Phone.strip():
                phone_number = config.Phone.strip()
            else:
                # Try to read from additionalQuestions.yaml if available
                try:
                    import yaml
                    if os.path.exists('additionalQuestions.yaml'):
                        with open('additionalQuestions.yaml', 'r', encoding='utf-8') as f:
                            questions = yaml.safe_load(f)
                            if questions and 'inputField' in questions:
                                phone_number = questions['inputField'].get('Phone Number', '').strip()
                except Exception:
                    pass
            
            if not phone_number:
                return  # No phone number configured, skip filling
            
            # Try multiple selectors to find phone number input fields
            phone_selectors = [
                "input[type='tel']",
                "input[name*='phone']",
                "input[id*='phone']",
                "input[aria-label*='phone']",
                "input[placeholder*='phone']",
                "input[data-test-single-line-text-input]",
                "input[class*='phone']"
            ]
            
            phone_filled = False
            
            # Also try XPath selectors for case-insensitive matching
            xpath_selectors = [
                "//input[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'phone')]",
                "//input[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'phone')]",
                "//input[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'phone')]",
                "//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'phone')]"
            ]
            
            # Try CSS selectors first
            for selector in phone_selectors:
                try:
                    phone_inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for phone_input in phone_inputs:
                        try:
                            # Check if field is visible and empty
                            if phone_input.is_displayed():
                                current_value = phone_input.get_attribute("value") or ""
                                if current_value == "":
                                    phone_input.clear()
                                    phone_input.send_keys(phone_number)
                                    time.sleep(0.5)
                                    phone_filled = True
                                    if config.displayWarnings:
                                        utils.prYellow(f"✅ Filled phone number: {phone_number}")
                                    break
                        except Exception:
                            continue
                    if phone_filled:
                        break
                except Exception:
                    continue
            
            # Try XPath selectors if CSS didn't work
            if not phone_filled:
                for xpath in xpath_selectors:
                    try:
                        phone_inputs = self.driver.find_elements(By.XPATH, xpath)
                        for phone_input in phone_inputs:
                            try:
                                if phone_input.is_displayed():
                                    current_value = phone_input.get_attribute("value") or ""
                                    if current_value == "":
                                        phone_input.clear()
                                        phone_input.send_keys(phone_number)
                                        time.sleep(0.5)
                                        phone_filled = True
                                        if config.displayWarnings:
                                            utils.prYellow(f"✅ Filled phone number: {phone_number}")
                                        break
                            except Exception:
                                continue
                        if phone_filled:
                            break
                    except Exception:
                        continue
                
        except Exception as e:
            if config.displayWarnings:
                utils.prYellow(f"⚠️ Warning: Error in fillPhoneNumber: {str(e)[0:50]}")

    def applyProcess(self, percentage: int, offerPage: str, ai_answer_fn=None) -> str:
        applyPages = math.floor(100 / percentage) - 2 
        result = ""
        for pages in range(applyPages):
            # Fill phone number and answer questions before continuing to
            # the next step.
            self.fillPhoneNumber()
            self.question_answerer.answer_all(self.driver, ai_answer_fn=ai_answer_fn)
            self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']").click()
            time.sleep(random.uniform(1, constants.botSpeed))

        # Fill phone number and answer questions before review
        self.fillPhoneNumber()
        self.question_answerer.answer_all(self.driver, ai_answer_fn=ai_answer_fn)

        if config.dryRun:
            # In dry-run mode, navigate up to this point but do not submit.
            result = "* 🧪 DRY RUN - Would apply to this job: " + str(offerPage)
            return result

        self.driver.find_element( By.CSS_SELECTOR, "button[aria-label='Review your application']").click()
        time.sleep(random.uniform(1, constants.botSpeed))

        if config.followCompanies is False:
            try:
                self.driver.find_element(By.CSS_SELECTOR, "label[for='follow-company-checkbox']").click()
            except Exception:
                pass

        self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']").click()
        time.sleep(random.uniform(1, constants.botSpeed))

        result = "* 🥳 Just Applied to this job: " + str(offerPage)

        return result

    def displayWriteResults(self, lineToWrite: str) -> None:
        try:
            print(lineToWrite)
            utils.writeResults(lineToWrite)
            self.on_log(lineToWrite)
        except Exception as e:
            utils.prRed("❌ Error in DisplayWriteResults: " +str(e))

    def takeScreenshot(self, name: str) -> Optional[str]:
        """Save a screenshot of the current browser state for evidence/auditing.

        Screenshots are written to the 'screenshots' folder in the current
        working directory. Failures are non-fatal (logged as a warning only)
        since screenshotting is a convenience feature, not critical to the
        bot's core apply logic.
        """
        try:
            screenshots_dir = os.path.join(os.getcwd(), 'screenshots')
            os.makedirs(screenshots_dir, exist_ok=True)
            path = os.path.join(screenshots_dir, f"{name}.png")
            self.driver.save_screenshot(path)
            utils.prGreen(f"📸 Screenshot saved: {path}")
            self.on_screenshot(path)
            return path
        except Exception as e:
            if config.displayWarnings:
                utils.prYellow(f"⚠️ Warning: Could not save screenshot: {str(e)[0:80]}")
            return None

    def shouldStop(self) -> bool:
        """Check the GUI-provided stop flag, if any. Used at safe
        checkpoints in the main loop so a GUI 'Stop' button halts the run
        gracefully rather than killing the browser process mid-action."""
        try:
            return bool(self.stop_flag and self.stop_flag.is_set())
        except Exception:
            return False

    def element_exists(self, parent: webdriver.remote.webelement.WebElement, by: str, selector: str) -> bool:
        return len(parent.find_elements(by, selector)) > 0


def main() -> None:
    start = time.time()
    bot = Linkedin()
    bot.linkJobApply()
    end = time.time()
    utils.prYellow("---Took: " + str(round((time.time() - start)/60)) + " minute(s).")


if __name__ == "__main__":
    main()
