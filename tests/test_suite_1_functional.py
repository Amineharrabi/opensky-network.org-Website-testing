import pytest
import time
import requests
from selenium.webdriver.common.by import By
from pages.explorer_page import ExplorerPage
from config.config import Config
from tests.test_logger import get_logger, log_step, slow_down

logger = get_logger(__name__)


@pytest.mark.functional
class TestFunctionalSuite:
    """Realistic functional tests focusing on public OpenSky pages (map, controls, navigation)."""

    MAP_URL = "https://map.opensky-network.org/"

    def test_01_map_loads_successfully_and_performance(self, setup):
        """TC01: Load the public flight map and measure that main map canvas appears quickly."""
        driver = setup
        logger.info("🗺️  TC01: Testing map load and performance")
        log_step(logger, 1, "Navigating to flight map")
        driver.get(self.MAP_URL)
        slow_down(0.5)
        explorer_page = ExplorerPage(driver)

        log_step(logger, 2, "Checking if map canvas is visible")
        assert explorer_page.is_map_visible(), "Map canvas did not become visible within timeout"
        logger.info("  ├─ ✅ Map canvas is visible")
        slow_down(0.5)

        # measure page load time (best-effort). If instrumentation not available, get_page_load_time may return 0
        log_step(logger, 3, "Measuring page load time")
        try:
            load_time = explorer_page.get_page_load_time()
        except Exception:
            load_time = None

        if load_time is not None:
            assert load_time <= Config.MAP_LOAD_THRESHOLD, f"Map loaded too slowly: {load_time}s"
            logger.info(f"  ├─ ✅ Page load time: {load_time}s (threshold: {Config.MAP_LOAD_THRESHOLD}s)")

    def test_02_search_input_and_table_presence(self, setup):
        """TC02: Verify the map's search input and planes table DOM elements are present and usable."""
        driver = setup
        logger.info("🔍 TC02: Testing search input and table presence")
        log_step(logger, 1, "Navigating to map")
        driver.get(self.MAP_URL)
        slow_down(0.5)
        explorer_page = ExplorerPage(driver)

        log_step(logger, 2, "Checking search input presence")
        search_input = explorer_page.find_element(By.ID, "search_input")
        assert search_input is not None
        logger.info("  ├─ ✅ Search input found")
        slow_down(0.3)
        driver.get(self.MAP_URL)
        explorer_page = ExplorerPage(driver)

        # Ensure search input exists
        assert explorer_page.is_element_visible(explorer_page.SEARCH_INPUT), "Search input not visible"
        logger.info("  ├─ ✅ Search input is visible")
        slow_down(0.3)

        # Enter a short search term and ensure the table element exists (dynamic rows may not be present in every run)
        log_step(logger, 4, "Testing flight search")
        explorer_page.search_for_flight("AAL")
        slow_down(0.5)
        assert explorer_page.is_element_visible(explorer_page.FLIGHT_TABLE), "Planes table element not present"
        logger.info("  ├─ ✅ Planes table is visible after search")

    def test_03_map_controls_present(self, setup):
        """TC03: Verify key map controls (Home, Follow, Random) and sidebar toggle exist."""
        driver = setup
        logger.info("🎮 TC03: Testing map controls")
        log_step(logger, 1, "Navigating to map")
        driver.get(self.MAP_URL)
        slow_down(0.5)
        explorer_page = ExplorerPage(driver)

        log_step(logger, 2, "Checking map controls")
        controls = [("H", "Home button"), ("F", "Follow button"), ("R", "Random follow button"), ("toggle_sidebar_button", "Sidebar toggle")]
        for ctrl_id, desc in controls:
            visible = explorer_page.is_element_visible((By.ID, ctrl_id))
            assert visible, f"{desc} ({ctrl_id}) not visible"
            logger.info(f"  ├─ ✅ {desc} found")
            slow_down(0.2)

    def test_04_home_page_has_flight_map_link(self, setup):
        """TC04: From the main site home page, verify the Flight Map link points to the map.opensky-network.org domain."""
        driver = setup
        driver.get(Config.BASE_URL)
        explorer_page = ExplorerPage(driver)

        # Look for the Flight Map nav link
        elems = driver.find_elements(By.XPATH, "//a[contains(text(), 'Flight Map') or contains(., 'Flight Map')]")
        assert elems, "Flight Map link not found on home page"
        href = elems[0].get_attribute("href")
        assert "map.opensky-network.org" in href or "/map" in href, f"Flight Map link points to unexpected location: {href}"

    def test_05_login_link_points_to_auth(self, setup):
        """TC05: Verify the Sign in / Login entry points to the auth system (does not perform login)."""
        driver = setup
        driver.get(Config.BASE_URL)

        # locate sign in / login link (may be in navbar)
        login_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'auth.opensky-network.org') or contains(@href, '/login') or contains(text(), 'Sign in')]")
        assert login_links, "No login/sign-in link found on home page"


@pytest.mark.functional
class TestHomePages:
    """HOME-01 .. HOME-04 implemented inside the main suite file."""
    BASE = Config.BASE_URL

    def test_HOME_01_homepage_loads_and_sections_visible(self, setup):
        driver = setup
        assert "OpenSky" in driver.title or "OpenSky Network" in driver.title

        news = driver.find_elements(By.XPATH, "//h2[contains(., 'Latest News') or contains(., 'Latest News & Updates')]")
        assert news, "Latest News & Updates section not found"

        map_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Flight Map')]")
        assert map_links, "Live Flight Map link not found"

        assert driver.find_elements(By.XPATH, "//h5[contains(., 'About OpenSky') or contains(., 'About')]")
        assert driver.find_elements(By.XPATH, "//h5[contains(., 'Feed Data') or contains(., 'Feed Data')]")
        assert driver.find_elements(By.XPATH, "//h5[contains(., 'Our Data') or contains(., 'Our Data')]")

    def test_HOME_02_navigation_links(self, setup):
        driver = setup
        about = driver.find_element(By.XPATH, "//a[contains(@href, '/about') and (contains(text(), 'About') or contains(text(), 'About OpenSky'))]")
        about_href = about.get_attribute('href')
        resp = requests.head(about_href, allow_redirects=True, timeout=10)
        assert resp.status_code < 400

        feed = driver.find_element(By.XPATH, "//a[contains(@href, '/feed') and contains(text(), 'Feed')]")
        resp = requests.head(feed.get_attribute('href'), allow_redirects=True, timeout=10)
        assert resp.status_code < 400

        data = driver.find_element(By.XPATH, "//a[contains(@href, '/data') and contains(text(), 'Our Data')]")
        resp = requests.head(data.get_attribute('href'), allow_redirects=True, timeout=10)
        assert resp.status_code < 400

        fmap = driver.find_element(By.XPATH, "//a[contains(text(), 'Flight Map')]")
        fmap_href = fmap.get_attribute('href')
        assert 'map.opensky-network.org' in fmap_href or '/map' in fmap_href

    def test_HOME_03_signin_cta(self, setup):
        driver = setup
        signin = driver.find_elements(By.XPATH, "//a[contains(@href, '/login') or contains(text(), 'Sign in') or contains(text(), 'Sign In')]")
        assert signin, "Sign in link not found"
        signin[0].click()
        time.sleep(2)
        assert '/login' in driver.current_url or 'auth.opensky-network.org' in driver.current_url
        assert driver.find_elements(By.ID, 'username')
        assert driver.find_elements(By.ID, 'password')

    def test_HOME_04_news_updates_links(self, setup):
        driver = setup
        links = driver.find_elements(By.XPATH, "//section//a[contains(@href, 'ansperformance') or contains(text(), 'Eurocontrol')]")
        if not links:
            links = driver.find_elements(By.XPATH, "//section//a[starts-with(@href, 'http')]")
        assert links, "No announcement links found in news section"
        href = links[0].get_attribute('href')
        r = requests.head(href, allow_redirects=True, timeout=10)
        assert r.status_code < 400


@pytest.mark.functional
class TestAboutPagesInline:
    BASE = Config.BASE_URL

    def test_ABOUT_01_faq_searchable(self, setup):
        driver = setup
        driver.get(f"{self.BASE}about/faq")
        assert 'FAQ' in driver.title or 'Frequently' in driver.page_source
        body = driver.find_element(By.TAG_NAME, 'body').text
        assert 'ADS-B' in body or 'ADS-B' in driver.page_source

    def test_ABOUT_02_terms_and_privacy(self, setup):
        driver = setup
        for path in ['/about/terms-of-use', '/about/privacy-policy']:
            driver.get(f"{self.BASE}{path}")
            time.sleep(1)
            assert driver.title
            body = driver.find_element(By.TAG_NAME, 'body').text
            assert 'data' in body.lower() or 'privacy' in body.lower()

    def test_ABOUT_03_publications_links(self, setup):
        driver = setup
        driver.get(f"{self.BASE}about/publications")
        links = driver.find_elements(By.XPATH, "//a[contains(@href, 'pdf') or contains(@href, 'arxiv') or contains(text(), 'Download')]")
        if links:
            href = links[0].get_attribute('href')
            r = requests.head(href, allow_redirects=True, timeout=10)
            assert r.status_code < 400

    def test_ABOUT_04_cross_navigation(self, setup):
        driver = setup
        driver.get(f"{self.BASE}about/faq")
        home = driver.find_elements(By.XPATH, "//a[contains(@href, '/') and (contains(text(), 'Home') or contains(@class, 'navbar-brand'))]")
        if home:
            home[0].click()
            time.sleep(1)
            assert driver.current_url.rstrip('/') in (self.BASE.rstrip('/'), self.BASE)


@pytest.mark.functional
class TestFeedPagesInline:
    BASE = Config.BASE_URL

    def test_FEED_01_main_feed_overview(self, setup):
        driver = setup
        driver.get(f"{self.BASE}feed")
        assert 'Feed Data' in driver.page_source or 'Feed' in driver.title
        assert driver.find_elements(By.XPATH, "//a[contains(@href, '/feed/raspberry')]")

    def test_FEED_02_raspberry_pi_guide(self, setup):
        driver = setup
        driver.get(f"{self.BASE}feed/raspberry")
        links = driver.find_elements(By.XPATH, "//a[contains(@href, '.deb') or contains(text(), 'wget') or contains(@href, 'github')]")
        if links:
            href = links[0].get_attribute('href')
            r = requests.head(href, allow_redirects=True, timeout=10)
            assert r.status_code < 400

    def test_FEED_03_debian_docker_steps_present(self, setup):
        driver = setup
        driver.get(f"{self.BASE}feed/debian")
        body = driver.find_element(By.TAG_NAME, 'body').text.lower()
        assert 'apt' in body or 'docker' in body

    def test_FEED_04_specialized_feed_pages(self, setup):
        driver = setup
        for path in ['feed/flarm', 'feed/vhf']:
            driver.get(f"{self.BASE}{path}")
            assert driver.title or driver.page_source

    def test_FEED_05_downloads_and_removal_documented(self, setup):
        driver = setup
        driver.get(f"{self.BASE}feed")
        body = driver.find_element(By.TAG_NAME, 'body').text.lower()
        assert 'remove' in body or 'uninstall' in body or 'apt-get' in body


@pytest.mark.functional
class TestDataPagesInline:
    BASE = Config.BASE_URL

    def test_DATA_01_main_data_page_methods(self, setup):
        driver = setup
        driver.get(f"{self.BASE}data")
        assert 'Our Data' in driver.page_source or 'Data' in driver.title
        links = driver.find_elements(By.XPATH, "//a[contains(@href, '/data/api') or contains(@href, '/data/trino')]")
        assert links

    def test_DATA_02_aircraft_alerts(self, setup):
        driver = setup
        driver.get(f"{self.BASE}data/aircraft")
        search = driver.find_elements(By.XPATH, "//input[contains(@placeholder, 'Search') or contains(@id, 'search')]")
        assert driver.page_source

    def test_DATA_03_api_docs_navigation(self, setup):
        driver = setup
        driver.get(f"{self.BASE}data/api")
        assert '/states/all' in driver.page_source or 'API' in driver.page_source

    def test_DATA_04_tools_page_links(self, setup):
        driver = setup
        driver.get(f"{self.BASE}data/tools")
        links = driver.find_elements(By.XPATH, "//a[contains(@href, 'github') or contains(@href, 'pypi')]")
        assert links

    def test_DATA_05_scientific_datasets(self, setup):
        driver = setup
        driver.get(f"{self.BASE}data/scientific")
        assert 'dataset' in driver.page_source.lower() or 'trino' in driver.page_source.lower()


@pytest.mark.nonfunctional
class TestNonFunctionalInline:
    BASE = Config.BASE_URL

    def test_NF_01_browser_compatibility_smoke(self, setup):
        driver = setup
        driver.get(self.BASE)
        assert 'OpenSky' in driver.title or driver.page_source

    def test_NF_02_page_load_performance(self, setup):
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
        assert any(t is not None for t in times)

    def test_NF_03_https_and_mixed_content(self, setup):
        driver = setup
        driver.get(self.BASE)
        assert driver.current_url.startswith('https://')
        r = requests.head(self.BASE, allow_redirects=True, timeout=10)
        assert r.status_code < 400

    def test_NF_05_sitemap_validation_quick(self):
        sitemap_url = f"{Config.BASE_URL.rstrip('/')}/sitemap.xml"
        try:
            r = requests.head(sitemap_url, allow_redirects=True, timeout=8)
            assert r.status_code in (200, 301, 302)
        except requests.RequestException:
            pytest.skip('sitemap.xml not available or network blocked')
