import random
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import time


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def open(self, url):
        self.driver.get(url)

    def find(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def finds(self, by, value):
        self.wait.until(EC.presence_of_all_elements_located((by, value)))
        return self.driver.find_elements(by, value)

    def click(self, by, value):
        element = self.wait.until(EC.element_to_be_clickable((by, value)))
        element.click()

    def js_click(self, by, value):
        element = self.wait.until(EC.presence_of_element_located((by, value)))
        self.driver.execute_script("arguments[0].click();", element)

    def js_clicks(self, by, value):
        elements = self.wait.until(EC.presence_of_all_elements_located((by, value)))
        if elements:
            index = random.randint(0, len(elements) - 1)
            self.driver.execute_script("arguments[0].click();", elements[index])

    def typing(self, by, value, text):
        element = self.wait.until(EC.visibility_of_element_located((by, value)))
        element.clear()
        element.send_keys(text)

    def js_typing(self, by, value, text):
        element = self.find(by, value)
        self.driver.execute_script("arguments[0].value = arguments[1];", element, text)

    def is_displayed(self, by, value, timeout=5):
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.visibility_of_element_located((by, value)))
            return element.is_displayed()
        except (TimeoutException, NoSuchElementException):
            return False

    def get_text(self, by, value):
        for _ in range(3):
            try:
                element = self.wait.until(EC.presence_of_element_located((by, value)))
                text = element.get_attribute("textContent")
                return text.strip() if text else ""
            except StaleElementReferenceException:
                continue
        return ""

    def get_current_url(self):
        return self.driver.current_url

    def is_user_avatar_displayed(self, timeout=5):
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-bs-toggle='dropdown']")))
            return True
        except:
            return False

    def take_screenshot(self, name):
        os.makedirs("screenshots", exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filepath = f"screenshots/{name}_{timestamp}.png"
        self.driver.save_screenshot(filepath)
        return filepath

