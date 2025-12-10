import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from config.config import Config
import time
import os

@pytest.fixture(scope="function")
def driver(request):
    browser = request.config.getoption("--browser", default="chrome")
    headless = request.config.getoption("--headless", default=None)
    
    # Override Config.HEADLESS if --headless option is explicitly set
    use_headless = headless if headless is not None else Config.HEADLESS
    
    if browser == "chrome":
        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        if use_headless:
            options.add_argument("--headless=new")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        
        # Try to use local chromedriver.exe from /tests directory first
        chromedriver_path = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
        if os.path.exists(chromedriver_path):
            try:
                service = ChromeService(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                # If local chromedriver fails (version mismatch, etc.), fall back to webdriver-manager
                print(f"[DEBUG] Local chromedriver failed ({e}), falling back to webdriver-manager")
                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
        else:
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
    elif browser == "firefox":
        options = webdriver.FirefoxOptions()
        if Config.HEADLESS:
            options.add_argument("--headless")
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()),
                                   options=options)
    elif browser == "edge":
        options = webdriver.EdgeOptions()
        if Config.HEADLESS:
            options.add_argument("--headless")
        driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()),
                               options=options)
    
    driver.implicitly_wait(Config.IMPLICIT_WAIT)
    driver.set_page_load_timeout(Config.PAGE_LOAD_TIMEOUT)
    
    yield driver
    
    # Teardown
    driver.quit()

@pytest.fixture(scope="function")
def setup(driver):
    driver.get(Config.BASE_URL)
    return driver

def pytest_addoption(parser):
    parser.addoption("--browser", action="store", default="chrome", 
                    help="Browser to run tests: chrome, firefox, edge")
    parser.addoption("--headless", action="store_true", default=None,
                    help="Run tests in headless mode (overrides Config.HEADLESS)")
    parser.addoption("--no-headless", dest="headless", action="store_false",
                    help="Run tests with visible browser window (disables headless mode)")