from selenium.webdriver.common.by import By
from .base_page import BasePage

class LoginPage(BasePage):
    """
    Page Object for the OpenSky Network Login page.
    """
    # Locators
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.ID, "kc-login")
    # Keycloak may render feedback text differently; be permissive here
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".kc-feedback-text, .pf-c-alert__title, .alert.alert-danger")

    def login(self, username, password):
        """
        Fills the login form and submits it.
        """
        self.input_text(self.USERNAME_INPUT, username)
        self.input_text(self.PASSWORD_INPUT, password)
        self.click(self.LOGIN_BUTTON)
        # After submitting, the page will either show an error or redirect.
        # The caller can instantiate another page object as needed.
        return None

    def get_error_message(self):
        """
        Returns the text of the login error message, if visible.
        """
        if self.is_element_visible(self.ERROR_MESSAGE, timeout=5):
            try:
                return self.get_text(self.ERROR_MESSAGE)
            except Exception:
                return None
        return None
