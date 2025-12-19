from __future__ import annotations

from typing import Iterable

from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def first_clickable(elements: Iterable) -> object | None:
    for el in elements:
        try:
            if el and el.is_displayed() and el.is_enabled():
                return el
        except Exception:
            continue
    return None


def safe_click(driver: WebDriver, element, *, timeout_s: float = 10.0) -> None:
    """Click reliably: scroll, wait clickable, fallback to JS click."""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", element)
    except Exception:
        pass

    try:
        WebDriverWait(driver, timeout_s).until(EC.element_to_be_clickable(element))
    except Exception:
        # Still attempt to click below.
        pass

    try:
        element.click()
        return
    except (ElementClickInterceptedException, ElementNotInteractableException):
        pass
    except Exception:
        # Fall through to JS click
        pass

    driver.execute_script("arguments[0].click();", element)

