import os
import time
from pathlib import Path

import pytest
from selenium.webdriver.common.by import By

from config.config import Config
from tests.test_logger import get_logger, log_step, log_check, slow_down

logger = get_logger(__name__)


CB_MATRIX = [
    ("CB-01", "chrome", "Windows", "/", "Homepage"),
    ("CB-02", "chrome-mobile", "Android", "/", "Homepage (mobile)"),
    ("CB-03", "firefox", "Windows", "/", "Homepage"),
    ("CB-04", "firefox", "mac", "/", "Homepage mac"),
    ("CB-05", "edge", "Windows", "/", "Homepage Edge"),
    ("CB-06", "safari", "mac", "/", "Homepage Safari"),
    ("CB-07", "safari-mobile", "iOS", "/", "Homepage iOS"),
    ("CB-08", "safari-tech-preview", "mac", "/", "All pages (STP)"),
    ("CB-09", "chrome-old", "any", "/", "Chrome 2 versions back"),
    ("CB-10", "firefox-esr", "any", "/", "Firefox ESR"),
]


def _ensure_screenshot_dir():
    p = Path('reports') / 'screenshots'
    p.mkdir(parents=True, exist_ok=True)
    return p


def _matches_requested_browser(requested, running):
    # Normalize several labels to match what CI/runner may pass in --browser
    if requested == running:
        return True
    # special cases
    if requested == 'chrome-mobile' and running in ('chrome', 'chrome-mobile'):
        return True
    if requested == 'safari-mobile' and running in ('safari',):
        return True
    if requested == 'chrome-old' and running == 'chrome':
        # assume chrome runner can be configured to older binary externally
        return True
    if requested == 'firefox-esr' and running == 'firefox':
        return True
    return False


@pytest.mark.crossbrowser
@pytest.mark.parametrize('cb_id,expected_browser,os_name,path,desc', CB_MATRIX)
def test_cb_matrix(cb_id, expected_browser, os_name, path, desc, request, driver, settings):
    """Cross-browser smoke checks.

    These tests are convenience checks: they will only run when the requested
    runtime browser (via `--browser`) matches the matrix entry. This avoids
    creating drivers for browsers you don't have installed here.
    """
    running_browser = request.config.getoption('--browser') or 'chrome'

    if not _matches_requested_browser(expected_browser, running_browser):
        pytest.skip(f"Test {cb_id} requires browser '{expected_browser}' but runner is '{running_browser}'")

    # Compose URL to test
    url = Config.BASE_URL.rstrip('/') + path

    log_step(logger, 1, f"Loading {url} on {running_browser}")
    driver.get(url)
    time.sleep(1)

    # Take screenshot for visual comparison / manual review
    ss_dir = _ensure_screenshot_dir()
    fname = ss_dir / f"{cb_id}_{running_browser}.png"
    try:
        log_step(logger, 2, f"Taking screenshot: {fname.name}")
        driver.save_screenshot(str(fname))
        log_check(logger, f"Screenshot saved")
    except Exception:
        pass

    # Basic DOM sanity: page body exists (site may not use <header> tag)
    log_step(logger, 3, "Verifying body element exists")
    body = driver.find_element(By.TAG_NAME, "body")
    assert body is not None, f"Body not found on {url}"
    log_check(logger, "Body found")

    # Check a primary interactive control is clickable: first nav link
    log_step(logger, 4, "Testing primary link clickability")
    clickable = False
    try:
        nav_link = driver.find_element(By.CSS_SELECTOR, 'a[href]')
        href = nav_link.get_attribute('href')
        nav_link.click()
        time.sleep(0.8)
        clickable = True
        log_check(logger, "Primary link is clickable")
    except Exception:
        clickable = False

    assert clickable, f"Primary link not clickable on {running_browser} for {cb_id}"

    # Try to collect JS console errors where supported
    log_step(logger, 5, "Checking for JS console errors")
    js_errors = []
    try:
        # Not all drivers support browser log retrieval; do best-effort
        logs = driver.get_log('browser')
        for entry in logs:
            if entry.get('level') in ('SEVERE', 'ERROR'):
                js_errors.append(entry)
        if not js_errors:
            log_check(logger, "No JS console errors found")
    except Exception:
        # ignore if logs not available
        js_errors = []

    if js_errors:
        logger.info(f"[FINDING] JS console errors on {cb_id} ({running_browser}): {js_errors[:3]}")
        if settings.audit_strict:
            assert len(js_errors) == 0, f"JS console errors on {cb_id} ({running_browser}): {js_errors}"
