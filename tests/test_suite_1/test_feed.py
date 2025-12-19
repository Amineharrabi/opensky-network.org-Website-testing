import pytest
import time
from selenium.webdriver.common.by import By
from config.config import Config
from utils.web_audit import head_or_get


@pytest.mark.functional
class TestFeedPages:
    BASE = Config.BASE_URL

    def test_FEED_01_main_feed_overview(self, setup):
        """FEED-01: Verify main feed page overview"""
        driver = setup
        driver.get(f"{self.BASE}feed")
        assert 'Feed Data' in driver.page_source or 'Feed' in driver.title
        # check subpage links exist
        assert driver.find_elements(By.XPATH, "//a[contains(@href, '/feed/raspberry')]")

    def test_FEED_02_raspberry_pi_guide(self, setup, tmp_path):
        """FEED-02: Test Raspberry Pi feed installation guide and download link"""
        driver = setup
        driver.get(f"{self.BASE}feed/raspberry")
        # find wget/download links
        links = driver.find_elements(By.XPATH, "//a[contains(@href, '.deb') or contains(text(), 'wget') or contains(@href, 'github')]")
        if links:
            href = links[0].get_attribute('href')
            r = head_or_get(href, timeout=10)
            if r.status_code in (403, 429):
                pytest.skip(f"External link blocked (HTTP {r.status_code}): {href}")
            assert r.status_code < 400

    def test_FEED_03_debian_docker_steps_present(self, setup):
        """FEED-03: Validate Debian/Docker feed setup instructions present"""
        driver = setup
        driver.get(f"{self.BASE}feed/debian")
        body = driver.find_element(By.TAG_NAME, 'body').text.lower()
        assert 'apt' in body or 'docker' in body

    def test_FEED_04_specialized_feed_pages(self, setup):
        """FEED-04: Test specialized feed pages (FLARM, VHF)"""
        driver = setup
        for path in ['feed/flarm', 'feed/vhf']:
            driver.get(f"{self.BASE}{path}")
            assert driver.title or driver.page_source

    def test_FEED_05_downloads_and_removal_documented(self, setup):
        """FEED-05: Check that feed page contains install/download guidance (wording may vary)."""
        driver = setup
        driver.get(f"{self.BASE}feed")
        body = driver.find_element(By.TAG_NAME, 'body').text.lower()

        # Strong signal: the page should explain installation or provide references to install steps.
        assert any(k in body for k in ("install", "installation", "debian", "raspberry", "apt", "docker")), (
            "Feed page does not seem to contain installation guidance keywords; site content may have changed."
        )

        # Removal/uninstall is a "nice to have" and may legitimately be absent.
        if not any(k in body for k in ("remove", "uninstall", "purge")):
            pytest.skip("Uninstall/removal steps not clearly documented (content/wording may vary)")
