from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tests.selenium.pages.base_page import BasePage
import time

class ManageBookingsPage(BasePage):
    URL = "/recept?tab=list"
    
    SEARCH_INPUT = (By.NAME, "search")
    STATUS_SELECT = (By.NAME, "status")
    DATE_SELECT = (By.NAME, "check_in_date")
    SUBMIT_BTN = (By.XPATH, "//button[text()='Lọc']")
    BOOKING_ROWS = (By.CSS_SELECTOR, "tbody tr.border-bottom")
    EMPTY_ROW = (By.CSS_SELECTOR, "tbody tr td.text-center")
    TAB_LIST = (By.CSS_SELECTOR, "button[data-bs-target='#bookings-content']")
    
    CHECKOUT_MODAL = (By.ID, "checkoutModal")
    CHECKOUT_ROOM_PRICE = (By.ID, "checkout_room_price")
    CHECKOUT_LATE_FEE = (By.ID, "checkout_late_fee")
    CHECKOUT_LATE_FEE_ROW = (By.ID, "late_fee_row")
    CHECKOUT_TOTAL = (By.ID, "checkout_total")
    CHECKOUT_PAID = (By.ID, "checkout_paid")
    CHECKOUT_BALANCE = (By.ID, "checkout_balance")
    CONFIRM_CHECKOUT_BTN = (By.ID, "confirmCheckoutBtn")
    CLOSE_MODAL_BTN = (By.CSS_SELECTOR, "#checkoutModal .btn-close")

    def search(self, text="", status="ALL", date=""):
        self.find(*self.SEARCH_INPUT).clear()
        if text:
            self.find(*self.SEARCH_INPUT).send_keys(text)
            
        status_dropdown = self.find(*self.STATUS_SELECT)
        for option in status_dropdown.find_elements(By.TAG_NAME, "option"):
            if option.get_attribute("value") == status:
                option.click()
                break
                
        date_dropdown = self.find(*self.DATE_SELECT)
        for option in date_dropdown.find_elements(By.TAG_NAME, "option"):
            if option.get_attribute("value") == date:
                option.click()
                break
                
        btn = self.find(*self.SUBMIT_BTN)
        btn.click()
        try:
            WebDriverWait(self.driver, 5).until(EC.staleness_of(btn))
        except:
            pass

    def get_booking_rows(self):
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(self.BOOKING_ROWS)
            )
            return self.driver.find_elements(*self.BOOKING_ROWS)
        except:
            return []
            
    def is_empty_message_displayed(self):
        try:
            return self.driver.find_element(*self.EMPTY_ROW).is_displayed()
        except:
            return False

    def click_checkin(self, booking_id):
        xpath = f"//td[contains(text(), 'BK-{booking_id}')]/..//button[@value='checkin']"
        btn = self.find(By.XPATH, xpath)
        btn.click()
        try:
            WebDriverWait(self.driver, 5).until(EC.staleness_of(btn))
        except:
            pass

    def click_checkout(self, booking_id):
        xpath = f"//td[contains(text(), 'BK-{booking_id}')]/..//button[contains(., 'Check-out')]"
        btn = self.find(By.XPATH, xpath)
        btn.click()
        
    def wait_for_checkout_modal(self):
        self.find(*self.CHECKOUT_MODAL)
        time.sleep(0.5) 
        
    def confirm_checkout(self):
        time.sleep(0.5)
        btn = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(self.CONFIRM_CHECKOUT_BTN))
        btn.click()
        time.sleep(0.5)
        
    def close_checkout_modal(self):
        time.sleep(0.5)
        btn = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(self.CLOSE_MODAL_BTN))
        btn.click()
        time.sleep(0.5)
        WebDriverWait(self.driver, 5).until(
            EC.invisibility_of_element_located(self.CHECKOUT_MODAL)
        )
