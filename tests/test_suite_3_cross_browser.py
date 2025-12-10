import os
import time
from pathlib import Path

import pytest
from selenium.webdriver.common.by import By

from config.config import Config


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


@pytest.mark.cross_browser
@pytest.mark.parametrize('cb_id,expected_browser,os_name,path,desc', CB_MATRIX)
def test_cb_matrix(cb_id, expected_browser, os_name, path, desc, request, driver):
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

    driver.get(url)
    time.sleep(1)

    # Take screenshot for visual comparison / manual review
    ss_dir = _ensure_screenshot_dir()
    fname = ss_dir / f"{cb_id}_{running_browser}.png"
    try:
        driver.save_screenshot(str(fname))
    except Exception:
        pass

    # Basic DOM sanity: main content or header exists
    try:
        el = driver.find_element(By.TAG_NAME, 'header')
    except Exception:
        el = None
    assert el is not None, f"Header not found on {url}"

    # Check a primary interactive control is clickable: first nav link
    clickable = False
    try:
        nav_link = driver.find_element(By.CSS_SELECTOR, 'a[href]')
        href = nav_link.get_attribute('href')
        nav_link.click()
        time.sleep(0.8)
        # after click, either URL changed or still available
        clickable = True
    except Exception:
        clickable = False

    assert clickable, f"Primary link not clickable on {running_browser} for {cb_id}"

    # Try to collect JS console errors where supported
    js_errors = []
    try:
        # Not all drivers support browser log retrieval; do best-effort
        logs = driver.get_log('browser')
        for entry in logs:
            if entry.get('level') in ('SEVERE', 'ERROR'):
                js_errors.append(entry)
    except Exception:
        # ignore if logs not available
        js_errors = []

    assert len(js_errors) == 0, f"JS console errors on {cb_id} ({running_browser}): {js_errors}"
import pytest
from pages.explorer_page import ExplorerPage

@pytest.mark.crossbrowser
class TestCrossBrowserSuite:
    """
    Cross-browser tests for the OpenSky Network website.
    """

    def test_14_map_rendering_across_browsers(self, setup):
        """TC14: Verify the map container is visible across different browsers."""
        driver = setup
        explorer_page = ExplorerPage(driver)
        assert explorer_page.is_map_visible(), f"Map did not render correctly in {driver.name}."

    def test_15_search_consistency_across_browsers(self, setup):
        """TC15: Verify that searching for a flight yields a visible result table across browsers."""
        driver = setup
        explorer_page = ExplorerPage(driver)
        explorer_page.search_for_flight("DLH")  # Lufthansa
        assert explorer_page.is_element_visible(explorer_page.FLIGHT_TABLE), f"Flight table did not appear after search in {driver.name}."

    def test_16_javascript_execution_for_title(self, setup):
        """TC16: Check that basic JavaScript execution works by retrieving the page title."""
        driver = setup
        js_title = driver.execute_script("return document.title;")
        assert "OpenSky Network" in js_title, f"JavaScript did not execute correctly to get title in {driver.name}."

    def test_17_ui_element_consistency(self, setup):
        """TC17: Check for the presence and basic style of key UI elements."""
        driver = setup
        explorer_page = ExplorerPage(driver)
        search_input = explorer_page.find_element(explorer_page.SEARCH_INPUT)
        assert search_input.is_displayed(), f"Search input not displayed in {driver.name}."
        # A simple style check
        assert "#f8f9fa" in search_input.value_of_css_property("background-color"), f"Search input style mismatch in {driver.name}."

    def test_18_login_link_navigation(self, setup):
        """TC18: Verify the login link navigates correctly across browsers."""
        driver = setup
        explorer_page = ExplorerPage(driver)
        login_page = explorer_page.go_to_login_page()
        assert "Login" in login_page.driver.title, f"Navigation to login page failed in {driver.name}."
