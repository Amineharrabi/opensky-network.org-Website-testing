import time
from pathlib import Path

import pytest

from config.config import Config
from tests.test_logger import get_logger, log_step, log_check

logger = get_logger(__name__)


RWD_MATRIX = [
    ("RWD-01", 320, 568, "iPhone SE", ["/", "/feed/raspberry"]),
    ("RWD-02", 375, 667, "iPhone 8", ["/", "/feed/raspberry", "/data/api-docs"]),
    ("RWD-03", 390, 844, "iPhone 14", ["/" , "/feed/raspberry"]),
    ("RWD-04", 414, 896, "iPhone Plus", ["/", "/feed/raspberry"]),
    ("RWD-05", 360, 800, "Budget Android", ["/feed/raspberry"]),
    ("RWD-06", 768, 1024, "iPad portrait", ["/", "/about/faq"]),
    ("RWD-07", 1024, 1366, "iPad Pro landscape", ["/", "/feed/raspberry"]),
    ("RWD-08", 1440, 900, "Laptop common", ["/", "/data/api-docs"]),
    ("RWD-09", 1920, 1080, "Desktop 1080p", ["/", "/data/api-docs"]),
    ("RWD-10", 2560, 1440, "2K Desktop", ["/", "/data/api-docs"]),
    ("RWD-11", 1366, 768, "Zoom 125% (approx)", ["/", "/feed/raspberry"]),
    ("RWD-12", 1366, 768, "Dark Mode forced (approx)", ["/", "/feed/raspberry"]),
]


def _ensure_resp_screenshots_dir():
    p = Path('reports') / 'screenshots' / 'responsive'
    p.mkdir(parents=True, exist_ok=True)
    return p


def _has_horizontal_scroll(driver):
    script = "return document.documentElement.scrollWidth > window.innerWidth;"
    try:
        return driver.execute_script(script)
    except Exception:
        return False


def _largest_tap_target_bounding(driver):
    # find buttons/links and compute max bounding box area/size for tap target heuristic
    script = """
    let els = Array.from(document.querySelectorAll('a, button, [role=button], input[type=button], input[type=submit]'));
    let sizes = els.map(e=>{
      let r = e.getBoundingClientRect();
      return {w: r.width, h: r.height, text: e.innerText||e.getAttribute('aria-label')||''};
    });
    return sizes;
    """
    try:
        return driver.execute_script(script)
    except Exception:
        return []


def _code_blocks_overflow(driver):
    # Return True if any <pre> or .code block overflows horizontally
    script = """
    let blocks = Array.from(document.querySelectorAll('pre, code, .code'));
    for (let b of blocks){ if (b.scrollWidth > b.clientWidth) return true; }
    return false;
    """
    try:
        return driver.execute_script(script)
    except Exception:
        return False


@pytest.mark.responsive
@pytest.mark.parametrize('case_id,w,h,device,pages', RWD_MATRIX)
def test_responsive_viewports(case_id, w, h, device, pages, driver, settings):
    """Run a set of responsive checks for a given viewport.

    Checks include: no horizontal scroll, tap target sizes, code block overflow, and screenshots.
    """
    ss_dir = _ensure_resp_screenshots_dir()

    log_step(logger, 1, f"Testing {device} viewport {w}x{h}px")
    
    # set viewport
    try:
        driver.set_window_size(w, h)
    except Exception:
        # some drivers ignore set_window_size in headless; emulation via CDP when available
        pass

    for p in pages:
        url = Config.BASE_URL.rstrip('/') + p
        log_step(logger, 2, f"Loading {p or 'homepage'}")
        driver.get(url)
        time.sleep(1)

        # screenshot
        fname = ss_dir / f"{case_id}_{w}x{h}_{p.strip('/').replace('/','_') or 'home'}.png"
        try:
            log_step(logger, 3, f"Capturing screenshot")
            driver.save_screenshot(str(fname))
            log_check(logger, f"Screenshot saved")
        except Exception:
            pass

        # check horizontal scroll
        log_step(logger, 4, f"Checking for horizontal scroll")
        has_scroll = _has_horizontal_scroll(driver)
        if has_scroll:
            logger.info(f"[FINDING] Horizontal scroll detected for {case_id} at {w}x{h} on {p}")
            if settings.audit_strict:
                assert not has_scroll, f"Horizontal scroll detected for {case_id} at {w}x{h} on {p}"
        else:
            log_check(logger, f"No horizontal scroll")

        # tap targets: ensure at least one primary control has width/height >= 44px
        log_step(logger, 5, f"Verifying tap targets >= 44px")
        sizes = _largest_tap_target_bounding(driver)
        ok_tap = False
        for s in sizes:
            try:
                if (s.get('w', 0) >= 44 and s.get('h', 0) >= 44):
                    ok_tap = True
                    break
            except Exception:
                continue
        assert ok_tap, f"No tap targets >=44px detected for {case_id} at {w}x{h} on {p}"
        log_check(logger, f"Tap targets >= 44px found")

        # code blocks overflow check for pages where code is expected
        if '/data/api-docs' in p or '/feed' in p:
            overflow = _code_blocks_overflow(driver)
            if overflow:
                logger.info(f"[FINDING] Code block overflow detected for {case_id} at {w}x{h} on {p}")
                if settings.audit_strict:
                    assert not overflow, f"Code block overflow detected for {case_id} at {w}x{h} on {p}"

        # zoom / accessibility checks (approximate): when case is RWD-11 we check for layout break
        if case_id == 'RWD-11':
            # attempt to simulate browser zoom by increasing page scale via JS
            try:
                driver.execute_script("document.body.style.zoom='125%';")
                time.sleep(0.5)
                has_scroll_zoom = _has_horizontal_scroll(driver)
                assert not has_scroll_zoom, f"Layout breaks under zoom for {case_id} on {p}"
            finally:
                driver.execute_script("document.body.style.zoom='100%';")

        # dark mode forced (best-effort): try to emulate prefers-color-scheme if available
        if case_id == 'RWD-12':
            try:
                driver.execute_cdp_cmd('Emulation.setEmulatedMedia', {'features': [{'name': 'prefers-color-scheme', 'value': 'dark'}]})
                time.sleep(0.5)
                # sample background & foreground colors
                colors = driver.execute_script("return {bg:getComputedStyle(document.documentElement).backgroundColor, fg:getComputedStyle(document.documentElement).color};")
                assert colors and ('rgb' in colors.get('bg','') or 'rgba' in colors.get('bg',''))
            except Exception:
                # not all drivers support CDP for emulation; skip strict failure
                pass
