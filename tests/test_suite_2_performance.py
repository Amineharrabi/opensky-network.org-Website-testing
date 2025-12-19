import time
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from config.config import Config
from tests.test_logger import get_logger, log_step, log_check, slow_down
from utils.web_audit import head_or_get

logger = get_logger(__name__)


def _create_chrome(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=opts)
    return driver


def _emulate_network(driver, latency_ms=70, download_mbps=12, upload_mbps=3):
    # CDP expects bytes/sec
    download_bps = int(download_mbps * 1024 * 1024 / 8)
    upload_bps = int(upload_mbps * 1024 * 1024 / 8)
    try:
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
            "offline": False,
            "latency": latency_ms,
            "downloadThroughput": download_bps,
            "uploadThroughput": upload_bps,
        })
    except Exception:
        return


def _collect_performance_metrics(driver):
    script = """
    (function(){
      function sum(arr, key){return arr.reduce((s,i)=>s+(i[key]||0),0)}
      let lcpEntries = performance.getEntriesByType('largest-contentful-paint') || [];
      let lcp = lcpEntries.length? lcpEntries[lcpEntries.length-1].renderTime || lcpEntries[lcpEntries.length-1].startTime : 0;
      let layoutShifts = performance.getEntriesByType('layout-shift') || [];
      let cls = layoutShifts.reduce((s,e)=> s + (e.value||0), 0);
      let longTasks = performance.getEntriesByType('longtask') || [];
      let tbt = longTasks.reduce((s,e)=> s + Math.max(0,(e.duration-50)), 0);
      let resources = performance.getEntriesByType('resource') || [];
      let transfer = resources.reduce((s,r)=> s + (r.transferSize||0), 0);
      return {lcp: lcp, cls: cls, tbt: tbt, transferSize: transfer, nav: performance.timing.toJSON(), resourcesCount: resources.length};
    })();
    """
    try:
        metrics = driver.execute_script(script)
        return metrics or {}
    except Exception:
        return {}


@pytest.mark.performance
def test_perf_01_homepage_cold_load_tti(settings):
    """PERF-01 Homepage Cold Load (First Visit)

    Emulate 4G 70ms RTT, clear cache, load once and measure LCP, TBT, CLS, total transfer size.
    Success criteria captured from user CSV.
    """
    driver = _create_chrome(headless=True)
    try:
        _emulate_network(driver, latency_ms=70, download_mbps=12)
        # clear cache / service workers
        try:
            driver.execute_cdp_cmd('Network.clearBrowserCache', {})
            driver.execute_cdp_cmd('Network.clearBrowserCookies', {})
        except Exception:
            pass

        start = time.time()
        logger.info("  ├─ Loading homepage with 4G throttling...")
        driver.get(Config.BASE_URL)
        # wait a bit for observers to record
        time.sleep(2)
        metrics = _collect_performance_metrics(driver) or {}
        load_time = time.time() - start

        # heuristics / approximations
        lcp_raw = metrics.get("lcp")
        lcp = (lcp_raw / 1000.0) if isinstance(lcp_raw, (int, float)) and lcp_raw > 0 else load_time
        tbt_raw = metrics.get("tbt") or 0
        tbt = (tbt_raw / 1000.0) if isinstance(tbt_raw, (int, float)) else 0.0
        cls = float(metrics.get("cls") or 0.0)
        transfer = metrics.get("transferSize") or 0
        total_kb = (transfer / 1024.0) if isinstance(transfer, (int, float)) else 0.0

        logger.info(f"  ├─ Measured: Load {load_time:.2f}s, LCP {lcp:.2f}s, TBT {tbt:.2f}s, CLS {cls:.3f}, {total_kb:.0f}KB")
        slow_down(0.5)

        # Make performance assertions strict in all runs to surface regressions.
        # Tightened thresholds intentionally to reveal issues during QA.
        assert lcp <= 1.5, f"LCP too high: {lcp}s"
        logger.info(f"  ├─ ✅ LCP OK: {lcp:.2f}s ≤ 1.5s")
        # use load_time as proxy TTI
        assert load_time <= 2.0, f"Load time (proxy TTI) too high: {load_time}s"
        logger.info(f"  ├─ ✅ Load time OK: {load_time:.2f}s ≤ 2.0s")
        assert tbt <= 0.05, f"TBT too high: {tbt}s"
        logger.info(f"  ├─ ✅ TBT OK: {tbt:.2f}s ≤ 0.05s")
        assert cls <= 0.05, f"CLS too high: {cls}"
        logger.info(f"  ├─ ✅ CLS OK: {cls:.3f} ≤ 0.05")
        assert total_kb <= 1000.0, f"Total transfer > 1.0MB: {total_kb}KB"
        logger.info(f"  ├─ ✅ Transfer OK: {total_kb:.0f}KB ≤ 1000KB")
    finally:
        driver.quit()


@pytest.mark.performance
def test_perf_02_homepage_warm_load_cache_enabled(settings):
    """PERF-02 Homepage Warm Load (Repeat View)

    Load the homepage once to populate cache, then reload and measure.
    """
    driver = _create_chrome(headless=True)
    try:
        _emulate_network(driver, latency_ms=70, download_mbps=12)
        driver.get(Config.BASE_URL)
        time.sleep(1)
        # second load (cache enabled)
        start = time.time()
        driver.get(Config.BASE_URL)
        time.sleep(1)
        load_time = time.time() - start
        metrics = _collect_performance_metrics(driver) or {}
        lcp_raw = metrics.get("lcp")
        lcp = (lcp_raw / 1000.0) if isinstance(lcp_raw, (int, float)) and lcp_raw > 0 else load_time

        if settings.audit_strict:
            assert lcp <= 1.0, f"Warm LCP too high: {lcp}s"
            assert load_time <= 1.2, f"Warm load TTI proxy too high: {load_time}s"
        else:
            if lcp > 1.0:
                logger.info(f"[FINDING] warm LCP too high: {lcp:.2f}s (threshold 1.0s)")
            if load_time > 1.2:
                logger.info(f"[FINDING] warm load time too high: {load_time:.2f}s (threshold 1.2s)")
    finally:
        driver.quit()


@pytest.mark.performance
def test_perf_06_api_docs_on_slow_3g(settings):
    """PERF-06 API Docs Page on slow 3G

    Simulate slow 3G and assert LCP ≤ 2.5s on the target docs page.
    """
    driver = _create_chrome(headless=True)
    try:
        # slow 3G ~ 400 kbps, 400 ms RTT
        _emulate_network(driver, latency_ms=400, download_mbps=0.4, upload_mbps=0.2)
        target = Config.BASE_URL.rstrip('/') + '/data/api-docs'
        driver.get(target)
        time.sleep(2)
        metrics = _collect_performance_metrics(driver) or {}
        lcp_raw = metrics.get("lcp")
        lcp = (lcp_raw / 1000.0) if isinstance(lcp_raw, (int, float)) and lcp_raw > 0 else None
        if lcp is None:
            pytest.skip('LCP not available from this environment')
        if settings.audit_strict:
            assert lcp <= 2.5, f"API docs LCP too high on slow 3G: {lcp}s"
        elif lcp > 2.5:
            logger.info(f"[FINDING] API docs LCP too high on slow 3G: {lcp:.2f}s (threshold 2.5s)")
    finally:
        driver.quit()


@pytest.mark.performance
def test_perf_11_404_page_speed(settings):
    """PERF-11 Broken Link / 404 Page Speed

    Single-request check: response time < 500 ms and payload < 50 KB.
    For load scenarios run the k6 script provided in tests/perf_scripts.
    """
    url = Config.BASE_URL.rstrip('/') + '/this-page-does-not-exist-2025'
    start = time.time()
    r = head_or_get(url, timeout=10)
    elapsed = (time.time() - start) * 1000.0
    if r.status_code in (403, 429):
        pytest.skip(f"404 probe blocked by WAF/CDN (HTTP {r.status_code})")
    assert r.status_code == 404 or r.status_code == 200
    if settings.audit_strict:
        assert elapsed <= 500, f"404 page response too slow: {elapsed} ms"
        assert len(r.content) <= 50 * 1024, f"404 payload too large: {len(r.content)} bytes"
    else:
        if elapsed > 500:
            logger.info(f"[FINDING] 404 response slow: {elapsed:.0f} ms ({url})")
        if len(r.content) > 50 * 1024:
            logger.info(f"[FINDING] 404 payload large: {len(r.content)} bytes ({url})")


def _k6_available():
    return shutil.which('k6') is not None


@pytest.mark.skipif(not _k6_available(), reason="k6 not installed; see tests/perf_scripts for k6 scenarios")
def test_perf_k6_run_smoke():
    """Run a small k6 smoke scenario (if k6 is installed).

    This is a convenience wrapper that will run a short k6 JS file from tests/perf_scripts.
    Use the full k6 scripts for real load testing on a properly provisioned runner.
    """
    script = Path(__file__).parent / 'perf_scripts' / 'perf_03_concurrent_homepage.js'
    assert script.exists(), f"Missing k6 script: {script}"
    proc = subprocess.run(['k6', 'run', str(script)], capture_output=True, text=True, timeout=600)
    print(proc.stdout)
    assert proc.returncode == 0
import pytest
import time
from pages.explorer_page import ExplorerPage
from config.config import Config
from selenium.webdriver.common.action_chains import ActionChains

@pytest.mark.performance
class TestPerformanceSuite:
    """
    Performance and stress tests for the OpenSky Network website.
    """

    def test_08_map_load_time(self, setup, settings):
        """TC08: Verify the map loads within an acceptable time threshold."""
        driver = setup
        driver.get(settings.map_url)
        explorer_page = ExplorerPage(driver)
        start_time = time.time()
        map_loaded = explorer_page.is_map_visible()
        load_time = time.time() - start_time
        assert map_loaded, "Map did not become visible within the timeout."
        assert load_time < Config.MAP_LOAD_THRESHOLD, f"Map load time ({load_time:.2f}s) exceeded threshold."

    def test_09_search_response_time(self, setup, settings):
        """TC09: Measure the time for the flight table to update after a search."""
        driver = setup
        driver.get(settings.map_url)
        explorer_page = ExplorerPage(driver)
        start_time = time.time()
        explorer_page.search_for_flight("AAL")  # American Airlines
        response_time = time.time() - start_time
        assert response_time < 5.0, f"Search response time ({response_time:.2f}s) was too slow."

    def test_10_flight_details_panel_response_time(self, setup, settings):
        """TC10: Measure the time it takes for the flight details panel to appear."""
        driver = setup
        driver.get(settings.map_url)
        explorer_page = ExplorerPage(driver)
        callsign = "SWR100"
        explorer_page.search_for_flight(callsign)
        if not explorer_page.select_flight_from_table_by_callsign(callsign):
            pytest.skip(f"Flight {callsign} not found. Skipping test.")
        
        start_time = time.time()
        details_visible = explorer_page.is_flight_details_panel_visible()
        response_time = time.time() - start_time
        assert details_visible, "Flight details panel did not appear."
        assert response_time < Config.API_RESPONSE_THRESHOLD, f"Details panel took too long to appear ({response_time:.2f}s)."

    @pytest.mark.stress
    def test_11_map_interaction_stress(self, setup, settings):
        """TC11: Stress test the map with rapid zoom and pan actions."""
        driver = setup
        driver.get(settings.map_url)
        explorer_page = ExplorerPage(driver)
        assert explorer_page.is_map_visible(), "Map is not visible for stress test."
        map_element = explorer_page.find_element(explorer_page.MAP_CONTAINER)
        actions = ActionChains(driver)
        start_time = time.time()
        for _ in range(5):
            actions.move_to_element(map_element).double_click().pause(0.2).perform()
            actions.drag_and_drop_by_offset(map_element, 100, 50).pause(0.2).perform()
        total_time = time.time() - start_time
        assert total_time < 25, f"Map interaction stress test took too long ({total_time:.2f}s)."

    @pytest.mark.load
    def test_12_concurrent_sessions_load_test(self, setup):
        """TC12: Basic load test by simulating multiple tabs."""
        driver = setup
        original_window = driver.current_window_handle
        for _ in range(3):
            driver.execute_script("window.open(arguments[0]);", Config.BASE_URL)
            time.sleep(1)
        assert len(driver.window_handles) == 4, "Failed to open new tabs."
        # Close tabs
        for window in driver.window_handles:
            if window != original_window:
                driver.switch_to.window(window)
                driver.close()
        driver.switch_to.window(original_window)

    @pytest.mark.stress
    def test_13_page_refresh_stress_test(self, setup):
        """TC13: Stress test by repeatedly refreshing the page."""
        driver = setup
        start_time = time.time()
        for _ in range(5):
            driver.refresh()
            time.sleep(0.5)
        total_time = time.time() - start_time
        assert total_time < 30, f"Page refresh stress test took too long ({total_time:.2f}s)."
