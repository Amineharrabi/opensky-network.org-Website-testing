import time
import requests
import pytest
from selenium.webdriver.common.by import By
from config.config import Config


@pytest.mark.functional
class TestHomePage:
    BASE = Config.BASE_URL

    def test_HOME_01_homepage_loads_and_sections_visible(self, setup):
        """HOME-01: Verify homepage loads and displays key sections"""
        driver = setup
        # Ensure page title and key sections
        assert "OpenSky" in driver.title or "OpenSky Network" in driver.title

        # Latest News & Updates
        news = driver.find_elements(By.XPATH, "//h2[contains(., 'Latest News') or contains(., 'Latest News & Updates')]")
        assert news, "Latest News & Updates section not found"

        # Live Flight Map link
        map_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Flight Map')]")
        assert map_links, "Live Flight Map link not found"

        # About OpenSky, Feed Data, Our Data
        assert driver.find_elements(By.XPATH, "//h5[contains(., 'About OpenSky') or contains(., 'About')]")
        assert driver.find_elements(By.XPATH, "//h5[contains(., 'Feed Data') or contains(., 'Feed Data')]")
        assert driver.find_elements(By.XPATH, "//h5[contains(., 'Our Data') or contains(., 'Our Data')]")

    def test_HOME_02_navigation_links(self, setup):
        """HOME-02: Validate navigation links from homepage"""
        driver = setup
        # About
        about = driver.find_element(By.XPATH, "//a[contains(@href, '/about') and (contains(text(), 'About') or contains(text(), 'About OpenSky'))]")
        about_href = about.get_attribute('href')
        resp = requests.head(about_href, allow_redirects=True, timeout=10)
        assert resp.status_code < 400

        # Feed
        feed = driver.find_element(By.XPATH, "//a[contains(@href, '/feed') and contains(text(), 'Feed')]")
        resp = requests.head(feed.get_attribute('href'), allow_redirects=True, timeout=10)
        assert resp.status_code < 400

        # Our Data
        data = driver.find_element(By.XPATH, "//a[contains(@href, '/data') and contains(text(), 'Our Data')]")
        resp = requests.head(data.get_attribute('href'), allow_redirects=True, timeout=10)
        assert resp.status_code < 400

        # Flight Map
        fmap = driver.find_element(By.XPATH, "//a[contains(text(), 'Flight Map')]")
        fmap_href = fmap.get_attribute('href')
        assert 'map.opensky-network.org' in fmap_href or '/map' in fmap_href

    def test_HOME_03_signin_cta(self, setup):
        """HOME-03: Test sign-in call-to-action"""
        driver = setup
        # Look for sign in / login link/button
        signin = driver.find_elements(By.XPATH, "//a[contains(@href, '/login') or contains(text(), 'Sign in') or contains(text(), 'Sign In')]")
        assert signin, "Sign in link not found"
        signin[0].click()
        # Wait for navigation
        time.sleep(2)
        assert '/login' in driver.current_url or 'auth.opensky-network.org' in driver.current_url
        # Check username/password present
        assert driver.find_elements(By.ID, 'username')
        assert driver.find_elements(By.ID, 'password')

    def test_HOME_04_news_updates_links(self, setup):
        """HOME-04: Verify news and updates section and announcement links"""
        driver = setup
        # Find the Eurocontrol challenge link or any external announcement link
        links = driver.find_elements(By.XPATH, "//section//a[contains(@href, 'ansperformance') or contains(text(), 'Eurocontrol')]")
        if not links:
            # fallback: any external link in news section
            links = driver.find_elements(By.XPATH, "//section//a[starts-with(@href, 'http')]")
        assert links, "No announcement links found in news section"

        # Verify external link is reachable
        href = links[0].get_attribute('href')
        r = requests.head(href, allow_redirects=True, timeout=10)
        assert r.status_code < 400
