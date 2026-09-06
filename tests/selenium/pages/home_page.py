from selenium.webdriver.common.by import By
from tests.selenium.pages.base_page import BasePage

class HomePage(BasePage):
    URL = "/"
    
    HERO_TITLE = (By.CSS_SELECTOR, ".hero-section h1")
    SEARCH_BUTTON = (By.CSS_SELECTOR, "form.search-form button[type='submit']")

    def open_page(self, base_url):
        self.open(base_url + self.URL)

    def is_hero_title_displayed(self):
        return self.is_displayed(*self.HERO_TITLE)
