from selenium.webdriver.common.by import By
from tests.selenium.pages.base_page import BasePage
import time

class MyBookingsPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.url = "/my-bookings"
        
    def open_page(self, base_url):
        self.driver.get(base_url + self.url)
        time.sleep(1)

    def get_booking_card(self, booking_id):
        cards = self.driver.find_elements(By.CSS_SELECTOR, ".card")
        for card in cards:
            if f"#{booking_id}" in card.text:
                return card
        return None
        
    def get_cancel_button(self, booking_card):
        buttons = booking_card.find_elements(By.XPATH, ".//button[contains(., 'Hủy đặt phòng')]")
        if buttons:
            return buttons[0]
        return None
        
    def is_cancel_button_disabled(self, booking_card):
        btn = self.get_cancel_button(booking_card)
        if not btn:
            return True
        return not btn.is_enabled()
        
    def click_cancel_button(self, booking_card):
        btn = self.get_cancel_button(booking_card)
        if btn:
            self.driver.execute_script("arguments[0].click();", btn)
            time.sleep(1)
            
    def get_modal(self, booking_id):
        modal_id = f"cancelBookingModal{booking_id}"
        return self.driver.find_element(By.ID, modal_id)
        
    def click_confirm_cancel(self, booking_id):
        modal = self.get_modal(booking_id)
        confirm_btn = modal.find_element(By.XPATH, ".//button[contains(text(), 'Xác nhận hủy')]")
        self.driver.execute_script("arguments[0].click();", confirm_btn)
        time.sleep(2)
        
    def click_close_modal(self, booking_id):
        modal = self.get_modal(booking_id)
        close_btn = modal.find_element(By.XPATH, ".//button[contains(text(), 'Giữ đặt phòng')]")
        self.driver.execute_script("arguments[0].click();", close_btn)
        time.sleep(1)
        
    def is_cancel_button_visible(self, booking_card):
        btn = self.get_cancel_button(booking_card)
        return btn is not None and btn.is_displayed()

    def get_toast_message(self):
        try:
            toast = self.driver.find_element(By.CSS_SELECTOR, ".alert-text")
            return toast.get_attribute("textContent").strip()
        except:
            return ""
