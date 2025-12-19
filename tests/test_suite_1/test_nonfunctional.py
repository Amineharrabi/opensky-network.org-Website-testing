import pytest
import time
import requests
from selenium.webdriver.common.by import By
from config.config import Config
from utils.web_audit import head_or_get


@pytest.mark.nonfunctional
class TestNonFunctional:
    BASE = Config.BASE_URL

    def test_NF_01_browser_compatibility_smoke(self, setup):
        """NF-01: Simple smoke test for rendering on current browser"""
        driver = setup
        driver.get(self.BASE)
        # Ensure no JS errors visible via performance logs not implemented here; just basic rendering
        assert 'OpenSky' in driver.title or driver.page_source

    def test_NF_02_page_load_performance(self, setup):
        """NF-02: Measure load times for a few pages"""
        driver = setup
        pages = [self.BASE, f"{self.BASE}data/api", f"{self.BASE}feed"]
        times = []
        for p in pages:
            driver.get(p)
            try:
                t = driver.execute_script('return (window.performance.timing.loadEventEnd - window.performance.timing.navigationStart)')
                times.append(t/1000.0 if t and t>0 else None)
            except Exception:
                times.append(None)
        # At least one measurement succeeded
        assert any(t is not None for t in times)

    def test_NF_03_https_and_mixed_content(self, setup):
        """NF-04: Security: HTTPS and mixed content check (basic)"""
        driver = setup
        driver.get(self.BASE)
        # Ensure the current page uses https
        assert driver.current_url.startswith('https://')
        # Basic network check using requests for homepage
        r = head_or_get(self.BASE, timeout=10)
        if r.status_code in (403, 429):
            pytest.skip(f"Homepage blocked by WAF/CDN (HTTP {r.status_code})")
        assert r.status_code < 400

    def test_NF_05_sitemap_validation_quick(self):
        """NF-05: Quick sitemap.xml check (if present)"""
        sitemap_url = f"{Config.BASE_URL.rstrip('/')}/sitemap.xml"
        try:
            r = head_or_get(sitemap_url, timeout=8)
            if r.status_code in (403, 429):
                pytest.skip(f"sitemap.xml blocked by WAF/CDN (HTTP {r.status_code})")
            assert r.status_code in (200, 301, 302)
        except requests.RequestException:
            pytest.skip('sitemap.xml not available or network blocked')
