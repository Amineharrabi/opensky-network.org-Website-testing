import time

import pytest
from selenium.webdriver.common.by import By

from tests.test_logger import get_logger, log_step, log_check

logger = get_logger(__name__)


XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "\"><img src=x onerror=alert(1)>",
    "'><svg/onload=alert(1)>",
    "<details open ontoggle=alert(1)>",
]


@pytest.mark.security
@pytest.mark.negative
@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_input_01_map_search_rejects_dom_xss(driver, settings, payload):
    url = settings.map_url
    log_step(logger, 1, f"Loading map: {url}")
    driver.get(url)
    time.sleep(2)

    log_step(logger, 2, "Typing payload into search input")
    search = driver.find_element(By.ID, "search_input")
    search.clear()
    search.send_keys(payload)
    time.sleep(1.0)

    log_step(logger, 3, "Ensuring no alert was triggered")
    alert_present = False
    try:
        driver.switch_to.alert
        alert_present = True
    except Exception:
        alert_present = False
    assert not alert_present, "Unexpected JS alert triggered (possible XSS)"
    log_check(logger, "No alert detected")

    log_step(logger, 4, "Heuristic DOM check: payload must not create an <img src=x> or injected <svg>")
    injected = driver.execute_script(
        "return {"
        "img: document.querySelectorAll('img[src=\"x\"]').length, "
        "svg: document.querySelectorAll('svg').length"
        "};"
    )
    if injected and injected.get("img"):
        pytest.fail("Detected injected <img src=x> element (possible DOM XSS)")

