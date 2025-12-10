import requests
import pytest
import time
from selenium.webdriver.common.by import By
from config.config import Config


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
            r = requests.head(href, allow_redirects=True, timeout=10)
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
        """FEED-05: Verify feed page downloads and removal documentation"""
        driver = setup
        driver.get(f"{self.BASE}feed")
        body = driver.find_element(By.TAG_NAME, 'body').text.lower()
        assert 'remove' in body or 'uninstall' in body or 'apt-get' in body
