import json
import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService

from config.config import Config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")

_test_start_times: dict[str, float] = {}


@dataclass(frozen=True)
class RuntimeSettings:
    base_url: str
    map_url: str
    browser: str
    headless: bool
    artifacts_dir: Path
    allow_driver_download: bool
    audit_strict: bool
    link_check_max: int
    link_check_timeout_s: float
    link_check_delay_s: float
    check_external_links: bool
    jira_create_on_fail: bool
    jira_project: str | None
    jira_issue_type: str
    jira_label: str | None


def pytest_addoption(parser):
    parser.addoption("--browser", action="store", default="chrome", help="chrome, firefox, edge")
    parser.addoption(
        "--headless",
        action="store_true",
        default=None,
        help="Run tests in headless mode (overrides Config.HEADLESS)",
    )
    parser.addoption("--no-headless", dest="headless", action="store_false", help="Disable headless mode")

    parser.addoption("--base-url", action="store", default=Config.BASE_URL, help="Base URL to test")
    parser.addoption(
        "--map-url",
        action="store",
        default="https://map.opensky-network.org/",
        help="OpenSky public map URL",
    )
    parser.addoption(
        "--artifacts-dir",
        action="store",
        default=str(Path("reports") / "artifacts"),
        help="Directory for failure artifacts (screenshots, HTML, logs)",
    )
    parser.addoption(
        "--allow-driver-download",
        action="store_true",
        default=False,
        help="Allow webdriver-manager downloads when local drivers are missing/mismatched",
    )
    parser.addoption(
        "--audit-strict",
        action="store_true",
        default=False,
        help="Fail security/audit tests strictly (otherwise they log findings)",
    )
    parser.addoption(
        "--link-check-max",
        action="store",
        type=int,
        default=40,
        help="Max URLs to check per page in link integrity tests",
    )
    parser.addoption(
        "--link-check-timeout",
        action="store",
        type=float,
        default=10.0,
        help="Timeout (seconds) for link integrity requests",
    )
    parser.addoption(
        "--link-check-delay",
        action="store",
        type=float,
        default=0.0,
        help="Delay (seconds) between link integrity requests",
    )
    parser.addoption(
        "--check-external-links",
        action="store_true",
        default=False,
        help="Also check external links (may be noisy/slow)",
    )

    parser.addoption(
        "--jira-create-on-fail",
        action="store_true",
        default=False,
        help="Create a Jira issue automatically when a test fails (requires env vars)",
    )
    parser.addoption("--jira-project", action="store", default=None, help="Jira project key (e.g. QA)")
    parser.addoption("--jira-issue-type", action="store", default="Bug", help="Jira issue type")
    parser.addoption("--jira-label", action="store", default=None, help="Optional Jira label")


@pytest.fixture(scope="session")
def settings(request) -> RuntimeSettings:
    browser = request.config.getoption("--browser") or "chrome"
    headless_opt = request.config.getoption("--headless")
    headless = headless_opt if headless_opt is not None else Config.HEADLESS

    return RuntimeSettings(
        base_url=str(request.config.getoption("--base-url")),
        map_url=str(request.config.getoption("--map-url")),
        browser=browser,
        headless=bool(headless),
        artifacts_dir=Path(request.config.getoption("--artifacts-dir")),
        allow_driver_download=bool(request.config.getoption("--allow-driver-download")),
        audit_strict=bool(request.config.getoption("--audit-strict")),
        link_check_max=int(request.config.getoption("--link-check-max") or 40),
        link_check_timeout_s=float(request.config.getoption("--link-check-timeout") or 10.0),
        link_check_delay_s=float(request.config.getoption("--link-check-delay") or 0.0),
        check_external_links=bool(request.config.getoption("--check-external-links")),
        jira_create_on_fail=bool(request.config.getoption("--jira-create-on-fail")),
        jira_project=request.config.getoption("--jira-project"),
        jira_issue_type=str(request.config.getoption("--jira-issue-type") or "Bug"),
        jira_label=request.config.getoption("--jira-label"),
    )


def _sanitize_nodeid(nodeid: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", nodeid)
    return safe[:180].strip("_") or "test"


def _install_js_error_collector(driver) -> None:
    script = r"""
    (function() {
      window.__qaErrors = [];
      function push(kind, payload) {
        try {
          window.__qaErrors.push({ kind: kind, ts: Date.now(), payload: payload });
        } catch (e) {}
      }
      window.addEventListener('error', function(e) {
        push('error', {
          message: e.message,
          filename: e.filename,
          lineno: e.lineno,
          colno: e.colno
        });
      });
      window.addEventListener('unhandledrejection', function(e) {
        var reason = e && e.reason ? (e.reason.message || String(e.reason)) : 'unknown';
        push('unhandledrejection', { reason: reason });
      });
    })();
    """
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": script})
    except Exception:
        # Non-Chrome drivers or restricted environments: best-effort only.
        return


@pytest.fixture(scope="session")
def driver(settings: RuntimeSettings):
    logger.info(f"[DRV] init browser={settings.browser} headless={settings.headless}")

    browser = settings.browser.lower()

    created_driver = None
    if browser == "chrome":
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-notifications")
        options.add_argument("--start-maximized")
        if settings.headless:
            options.add_argument("--headless=new")

        # Enable browser console logs (Chrome only)
        options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

        # Prefer the repo-pinned driver (tests/chromedriver.exe) to avoid network downloads.
        chromedriver_path = Path(__file__).with_name("chromedriver.exe")
        if chromedriver_path.exists():
            try:
                service = ChromeService(str(chromedriver_path))
                created_driver = webdriver.Chrome(service=service, options=options)
                logger.info(f"[DRV] using local chromedriver: {chromedriver_path}")
            except Exception as exc:
                logger.warning(f"[DRV] local chromedriver failed: {exc}")

        if created_driver is None:
            # Selenium 4+ can provision the driver via Selenium Manager automatically.
            # This is the most reliable option on developer machines where Chrome auto-updates.
            try:
                created_driver = webdriver.Chrome(options=options)
                logger.info("[DRV] using Selenium Manager provisioned driver")
            except Exception as exc:
                logger.warning(f"[DRV] Selenium Manager driver failed: {exc}")

        if created_driver is None:
            if not settings.allow_driver_download:
                raise pytest.UsageError(
                    "Chrome driver not available/compatible. "
                    "Update `tests/chromedriver.exe`, install a matching chromedriver in PATH, "
                    "or re-run with `--allow-driver-download` to use webdriver-manager."
                )
            from webdriver_manager.chrome import ChromeDriverManager

            service = ChromeService(ChromeDriverManager().install())
            created_driver = webdriver.Chrome(service=service, options=options)
            logger.info("[DRV] using webdriver-manager downloaded chromedriver")
    elif browser == "firefox":
        if not settings.allow_driver_download:
            raise pytest.UsageError(
                "Firefox requires geckodriver. Re-run with `--allow-driver-download` or provide a local geckodriver."
            )
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        from selenium.webdriver.firefox.service import Service as FirefoxService
        from webdriver_manager.firefox import GeckoDriverManager

        options = FirefoxOptions()
        if settings.headless:
            options.add_argument("-headless")
        service = FirefoxService(GeckoDriverManager().install())
        created_driver = webdriver.Firefox(service=service, options=options)
    elif browser == "edge":
        if not settings.allow_driver_download:
            raise pytest.UsageError(
                "Edge requires msedgedriver. Re-run with `--allow-driver-download` or provide a local Edge driver."
            )
        from selenium.webdriver.edge.options import Options as EdgeOptions
        from selenium.webdriver.edge.service import Service as EdgeService
        from webdriver_manager.microsoft import EdgeChromiumDriverManager

        options = EdgeOptions()
        if settings.headless:
            options.add_argument("--headless")
        service = EdgeService(EdgeChromiumDriverManager().install())
        created_driver = webdriver.Edge(service=service, options=options)
    else:
        raise pytest.UsageError(f"Unsupported --browser={settings.browser}")

    created_driver.implicitly_wait(Config.IMPLICIT_WAIT)
    created_driver.set_page_load_timeout(Config.PAGE_LOAD_TIMEOUT)
    if browser == "chrome":
        _install_js_error_collector(created_driver)

    yield created_driver

    try:
        created_driver.quit()
    finally:
        logger.info("[DRV] closed")


@pytest.fixture(scope="function")
def setup(driver, settings: RuntimeSettings):
    driver.get(settings.base_url)
    return driver


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="replace")


def _collect_failure_artifacts(driver, settings: RuntimeSettings, nodeid: str) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    test_dir = settings.artifacts_dir / _sanitize_nodeid(nodeid)
    test_dir.mkdir(parents=True, exist_ok=True)

    # Screenshot
    try:
        screenshot_path = test_dir / "screenshot.png"
        driver.save_screenshot(str(screenshot_path))
        artifacts["screenshot"] = str(screenshot_path)
    except Exception:
        pass

    # HTML dump
    try:
        html_path = test_dir / "page.html"
        _write_text(html_path, driver.page_source or "")
        artifacts["html"] = str(html_path)
    except Exception:
        pass

    # Browser logs (Chrome only)
    try:
        logs = driver.get_log("browser")
        log_path = test_dir / "console.json"
        _write_text(log_path, json.dumps(logs, indent=2))
        artifacts["console"] = str(log_path)
    except Exception:
        pass

    # JS errors from injected collector (Chrome only, best-effort)
    try:
        errors = driver.execute_script("return window.__qaErrors || [];")
        err_path = test_dir / "js_errors.json"
        _write_text(err_path, json.dumps(errors, indent=2))
        artifacts["js_errors"] = str(err_path)
    except Exception:
        pass

    return artifacts


def pytest_runtest_setup(item):
    _test_start_times[item.nodeid] = time.time()
    logger.info(f"[TEST] {item.nodeid}")


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return

    start = _test_start_times.get(item.nodeid, time.time())
    duration = time.time() - start
    status = "PASS" if report.passed else ("SKIP" if report.skipped else "FAIL")
    logger.info(f"[{status}] {item.nodeid} ({duration:.2f}s)")

    if not report.failed:
        return

    settings = item.funcargs.get("settings")
    driver = item.funcargs.get("driver")
    if settings is None or driver is None:
        return

    artifacts = _collect_failure_artifacts(driver, settings, item.nodeid)
    if artifacts:
        logger.info(f"[ART] saved: {artifacts}")

    if not settings.jira_create_on_fail:
        return

    try:
        from utils.jira_client import JiraClient, JiraIssueCreateRequest

        jira = JiraClient.from_env()
        summary = f"[AUTOTEST] {item.nodeid}"
        description = (
            f"*Automated failure*\n\n"
            f"- Test: {item.nodeid}\n"
            f"- URL: {settings.base_url}\n"
            f"- Browser: {settings.browser}\n"
            f"- Headless: {settings.headless}\n"
        )
        req = JiraIssueCreateRequest(
            project_key=settings.jira_project,
            issue_type=settings.jira_issue_type,
            summary=summary,
            description=description,
            labels=[settings.jira_label] if settings.jira_label else [],
        )
        issue_key = jira.create_issue(req)
        for _, file_path in artifacts.items():
            jira.add_attachment(issue_key, Path(file_path))
        logger.info(f"[JIRA] created {issue_key}")
    except Exception as exc:
        logger.warning(f"[JIRA] failed to create issue: {exc}")


def pytest_runtest_teardown(item, nextitem):
    _test_start_times.pop(item.nodeid, None)
