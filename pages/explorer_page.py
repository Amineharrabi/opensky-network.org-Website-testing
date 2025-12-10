from selenium.webdriver.common.by import By
from .base_page import BasePage
import time

class ExplorerPage(BasePage):
    """
    Page Object for the OpenSky Network Explorer page (the main map view).
    """
    # Locators
    MAP_CONTAINER = (By.ID, "map_canvas")
    SEARCH_INPUT = (By.ID, "search_input")
    FLIGHT_TABLE = (By.ID, "planesTable")
    LOGIN_LINK = (By.XPATH, "//a[contains(@href, '/login') or contains(text(), 'Sign in')]")
    FLIGHT_DETAILS_PANEL = (By.ID, "selected_infoblock")

    def is_map_visible(self):
        """Check if the map container is visible and loaded."""
        return self.is_element_visible(self.MAP_CONTAINER, timeout=20)

    def search_for_flight(self, identifier):
        """
        Searches for a flight using its ICAO24, callsign, or other identifier.
        """
        # Enter search text and wait briefly for client-side filtering to apply.
        self.input_text(self.SEARCH_INPUT, identifier)
        time.sleep(2)

    def select_flight_from_table_by_callsign(self, callsign):
        """
        Finds and clicks a flight in the table by its callsign.
        Returns True if found and clicked, False otherwise.
        """
        try:
            flight_row_xpath = f"//table[@id='planesTable']//td[contains(text(), '{callsign}')]/.."
            flight_row = self.find_element((By.XPATH, flight_row_xpath))
            self.scroll_to_element((By.XPATH, flight_row_xpath))
            flight_row.click()
            return True
        except Exception:
            return False

    def is_flight_details_panel_visible(self):
        """Checks if the flight details panel is displayed."""
        return self.is_element_visible(self.FLIGHT_DETAILS_PANEL, timeout=10)

    def get_flight_details_text(self):
        """Returns the text content of the flight details panel."""
        if self.is_flight_details_panel_visible():
            return self.get_text(self.FLIGHT_DETAILS_PANEL)
        return None

    def go_to_login_page(self):
        """Navigates to the login page."""
        self.click(self.LOGIN_LINK)
        # Return a new LoginPage object
        from .login_page import LoginPage
        return LoginPage(self.driver)
