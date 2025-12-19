import os
from datetime import datetime

class Config:
    # Base URL for the new target website
    BASE_URL = "https://opensky-network.org/"
    
    # Browser settings
    BROWSER = os.getenv('BROWSER', 'chrome')  # chrome, firefox, edge
    HEADLESS = os.getenv('HEADLESS', 'False').lower() in ('true', '1', 'yes')
    IMPLICIT_WAIT = 10  # Reasonable timeout for element waits
    PAGE_LOAD_TIMEOUT = 30
    
    # Test data (placeholders for now)
    VALID_USERNAME = "your_username"
    VALID_PASSWORD = "your_password"
    INVALID_USERNAME = "invaliduser"
    
    # Performance thresholds (seconds)
    # Made stricter to catch regressions during local QA runs
    MAP_LOAD_THRESHOLD = 2.0  # stricter threshold (seconds)
    API_RESPONSE_THRESHOLD = 1.0
    
    # Responsive resolutions
    RESOLUTIONS = {
        'mobile': (375, 667),      # iPhone SE
        'tablet': (768, 1024),     # iPad
        'desktop': (1920, 1080),   # Full HD
        'wide': (2560, 1440)       # 2K
    }
    
    # Directories
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
    SCREENSHOTS_DIR = os.path.join(BASE_DIR, 'screenshots')
    
    # Create directories if they don't exist
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    
    # Report name with timestamp
    REPORT_NAME = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
