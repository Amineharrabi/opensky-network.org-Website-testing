import requests
import pytest
import time
from selenium.webdriver.common.by import By
from config.config import Config


@pytest.mark.functional
class TestAboutPages:
    BASE = Config.BASE_URL

    def test_ABOUT_01_faq_searchable(self, setup):
        """ABOUT-01: Verify FAQ page content and searchability"""
        driver = setup
        driver.get(f"{self.BASE}about/faq")
        assert 'FAQ' in driver.title or 'Frequently' in driver.page_source
        # Look for common query presence
        body = driver.find_element(By.TAG_NAME, 'body').text
        assert 'ADS-B' in body or 'ADS-B' in driver.page_source

    def test_ABOUT_02_terms_and_privacy(self, setup):
        """ABOUT-02: Test terms-of-use and privacy-policy links"""
        driver = setup
        for path in ['/about/terms-of-use', '/about/privacy-policy']:
            driver.get(f"{self.BASE}{path}")
            time.sleep(1)
            assert driver.title
            # quick scan for expected keywords
            body = driver.find_element(By.TAG_NAME, 'body').text
            assert 'data' in body.lower() or 'privacy' in body.lower()

    def test_ABOUT_03_publications_links(self, setup):
        """ABOUT-03: Validate publications page links"""
        driver = setup
        driver.get(f"{self.BASE}about/publications")
        links = driver.find_elements(By.XPATH, "//a[contains(@href, 'pdf') or contains(@href, 'arxiv') or contains(text(), 'Download')]")
        if links:
            href = links[0].get_attribute('href')
            r = requests.head(href, allow_redirects=True, timeout=10)
            assert r.status_code < 400

    def test_ABOUT_04_cross_navigation(self, setup):
        """ABOUT-04: Cross-page navigation from about sections"""
        driver = setup
        driver.get(f"{self.BASE}about/faq")
        # breadcrumb or home link
        home = driver.find_elements(By.XPATH, "//a[contains(@href, '/') and (contains(text(), 'Home') or contains(@class, 'navbar-brand'))]")
        if home:
            home[0].click()
            time.sleep(1)
            assert driver.current_url.rstrip('/') in (self.BASE.rstrip('/'), self.BASE)
