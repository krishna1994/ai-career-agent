"""
login_helper.py - One-time interactive LinkedIn login helper.

Opens a visible Chrome window on the LinkedIn login page and waits
(polling) for up to 5 minutes for the user to manually log in -- including
via "Sign in with Google" or any other SSO flow that may open a popup
window. Once a successful login is detected, it saves the session cookies
to the same location linkedin.py / indeed.py expect, so subsequent bot runs
reuse the authenticated session without needing credentials in config.py.

IMPORTANT: Unlike earlier versions, this script does NOT repeatedly
navigate the page during polling. Forcibly reloading the page while the
user is in the middle of an OAuth/Google login redirect would interrupt
that flow (which is what caused the "continuously refreshing" issue).
Instead we just inspect cookies/window handles in the background.

Usage:
    python login_helper.py
"""
import hashlib
import os
import pickle
import ssl
import sys
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ['WDM_SSL_VERIFY'] = '0'
ssl._create_default_https_context = ssl._create_unverified_context

import config
import utils

sys.stdout.reconfigure(encoding='utf-8')

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

POLL_INTERVAL_SEC = 2
MAX_WAIT_SEC = 300  # 5 minutes to log in manually

# LinkedIn sets this cookie once a session is authenticated, regardless of
# whether login happened via email/password or an SSO provider like Google.
AUTH_COOKIE_NAME = "li_at"


def has_auth_cookie(driver) -> bool:
    """Check for the LinkedIn auth cookie WITHOUT navigating the page.

    Selenium's get_cookies() only returns cookies for the domain of the
    currently focused window, so we only need to look at whichever window
    is currently active -- we are not forcing navigation here.
    """
    try:
        cookies = driver.get_cookies()
    except Exception:
        return False
    return any(c.get("name") == AUTH_COOKIE_NAME for c in cookies)


def switch_to_main_window_if_popup_closed(driver, main_handle: str) -> None:
    """If an OAuth popup (e.g. Google sign-in) opened and then closed,
    make sure Selenium's focus returns to the main LinkedIn window so
    subsequent cookie checks look at the right domain."""
    handles = driver.window_handles
    if main_handle in handles and driver.current_window_handle != main_handle:
        try:
            driver.switch_to.window(main_handle)
        except Exception:
            pass
    elif main_handle not in handles and handles:
        # Main window handle became stale (rare) - fall back to whatever
        # window is left open.
        try:
            driver.switch_to.window(handles[0])
        except Exception:
            pass


def main():
    utils.prYellow("🤖 AI Career Agent - Manual Login Helper")
    utils.prYellow("🌐 Opening Chrome. Please log in to LinkedIn in the window that appears.")
    utils.prYellow("   (Email/password, 'Sign in with Google', or any other method all work.)")

    try:
        chrome_install = ChromeDriverManager().install()
        folder = os.path.dirname(chrome_install)
        chromedriver_path = os.path.join(folder, "chromedriver.exe")
        service = ChromeService(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=utils.chromeBrowserOptions())
    except Exception:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=utils.chromeBrowserOptions())

    driver.get("https://www.linkedin.com/login")
    main_handle = driver.current_window_handle

    utils.prYellow(f"⏳ Waiting up to {MAX_WAIT_SEC // 60} minutes for you to log in...")
    utils.prYellow("   This window will NOT refresh or navigate on its own anymore --")
    utils.prYellow("   take your time with Google sign-in or any popups that appear.")

    start = time.time()
    logged_in = False
    while time.time() - start < MAX_WAIT_SEC:
        # If a Google OAuth popup opened and later closed itself, make sure
        # we're looking at the main LinkedIn window again before checking
        # cookies. We never call driver.get()/refresh here.
        switch_to_main_window_if_popup_closed(driver, main_handle)

        if has_auth_cookie(driver):
            logged_in = True
            break

        time.sleep(POLL_INTERVAL_SEC)

    if not logged_in:
        utils.prRed("❌ Timed out waiting for login. No cookies saved. Please try again.")
        driver.quit()
        return

    utils.prGreen("✅ Login detected! Saving session cookies...")

    # Make sure we are on the main window before reading the final cookie
    # jar, and do ONE navigation to the feed just to confirm + settle the
    # session before saving (this happens only once, after login, not
    # repeatedly during the wait).
    switch_to_main_window_if_popup_closed(driver, main_handle)
    try:
        driver.get("https://www.linkedin.com/feed")
        time.sleep(2)
    except Exception:
        pass

    cookies_path = f"{os.path.join(os.getcwd(), 'cookies')}/{hashlib.md5(config.email.encode('utf-8')).hexdigest()}.pkl"
    cookies_dir = os.path.dirname(cookies_path)
    if cookies_dir and not os.path.exists(cookies_dir):
        os.makedirs(cookies_dir, exist_ok=True)

    with open(cookies_path, "wb") as f:
        pickle.dump(driver.get_cookies(), f)

    utils.prGreen(f"✅ Cookies saved to: {cookies_path}")
    utils.prGreen("🎉 You're all set! Future bot runs will reuse this session automatically.")

    time.sleep(2)
    driver.quit()


if __name__ == "__main__":
    main()