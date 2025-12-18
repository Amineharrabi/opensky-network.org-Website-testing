import time

import pytest

from tests.test_logger import get_logger, log_step

logger = get_logger(__name__)


TARGETS = [
    ("/", "Home"),
    ("/about", "About"),
    ("/data/api", "API"),
    ("/feed/raspberry", "Feed guide"),
]


def _browser_severe_logs(driver) -> list[dict]:
    try:
        logs = driver.get_log("browser") or []
    except Exception:
        return []
    severe = []
    for entry in logs:
        level = (entry.get("level") or "").upper()
        if level in ("SEVERE", "ERROR"):
            severe.append(entry)
    return severe


def _collected_js_errors(driver) -> list[dict]:
    try:
        return driver.execute_script("return window.__qaErrors || [];") or []
    except Exception:
        return []


@pytest.mark.js
@pytest.mark.audit
@pytest.mark.parametrize("path,desc", TARGETS)
def test_js_01_no_console_errors_on_key_pages(driver, settings, path, desc):
    url = settings.base_url.rstrip("/") + path
    log_step(logger, 1, f"Loading {desc}: {url}")
    driver.get(url)
    time.sleep(1.0)

    severe = _browser_severe_logs(driver)
    collected = _collected_js_errors(driver)

    if severe or collected:
        logger.info(f"[FINDING] JS errors on {url}")
        if severe:
            logger.info(f"[FINDING] console severe: {severe[:5]}")
        if collected:
            logger.info(f"[FINDING] window.__qaErrors: {collected[:5]}")

    if settings.audit_strict:
        assert not severe, f"Console errors on {url}: {severe[:3]}"
        assert not collected, f"JS runtime errors on {url}: {collected[:3]}"

