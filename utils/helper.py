
import time
import os
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from config.config import Config


class TestHelpers:
    """Utility functions for tests"""
    
    @staticmethod
    def take_screenshot(driver, name):
        """Take screenshot with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join(Config.SCREENSHOTS_DIR, filename)
        driver.save_screenshot(filepath)
        return filepath
    
    @staticmethod
    def wait_for_page_load(driver, timeout=10):
        """Wait for page to fully load"""
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            return True
        except TimeoutException:
            return False
    
    @staticmethod
    def measure_load_time(driver, url):
        """Measure page load time"""
        start_time = time.time()
        driver.get(url)
        TestHelpers.wait_for_page_load(driver)
        load_time = time.time() - start_time
        return load_time
    
    @staticmethod
    def check_console_errors(driver):
        """Check browser console for JavaScript errors"""
        logs = driver.get_log('browser')
        errors = [log for log in logs if log['level'] == 'SEVERE']
        return errors
    
    @staticmethod
    def scroll_to_bottom(driver):
        """Scroll to bottom of page"""
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)
    
    @staticmethod
    def scroll_to_top(driver):
        """Scroll to top of page"""
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
    
    @staticmethod
    def get_network_performance(driver):
        """Get network performance metrics"""
        performance = driver.execute_script("""
            var performance = window.performance || {};
            var timings = performance.timing || {};
            return {
                'loadTime': timings.loadEventEnd - timings.navigationStart,
                'domContentLoaded': timings.domContentLoadedEventEnd - timings.navigationStart,
                'responseTime': timings.responseEnd - timings.requestStart,
                'renderTime': timings.domComplete - timings.domLoading
            };
        """)
        return performance


# ============================================
# FILE: utils/report_generator.py
# ============================================
"""
Generate custom test reports with detailed metrics
"""
