from selenium.webdriver.common.by import By
from .base_page import BasePage
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

class HotelDetailPage(BasePage):
    """Page Object Model for the Hotel Detail Page"""
    
    # Locators
    CHECK_IN_INPUT = (By.ID, "check_in")
    CHECK_OUT_INPUT = (By.ID, "check_out")
    CHECK_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    
    # Locators cho Room Type Card
    def get_room_badge(self, room_type_id):
        return (By.ID, f"room-avail-badge-{room_type_id}")
        
    def get_book_button(self, room_type_id):
        return (By.ID, f"room-book-btn-{room_type_id}")

    def open_page(self, base_url, hotel_id):
        self.open(f"{base_url}/hotels/{hotel_id}")

    def set_dates_and_check(self, check_in_str, check_out_str):
        self.js_typing(*self.CHECK_IN_INPUT, check_in_str)
        self.js_typing(*self.CHECK_OUT_INPUT, check_out_str)
        self.click(*self.CHECK_BUTTON)
        # Đợi load lại
        time.sleep(0.5)

    def get_check_in_date(self):
        element = self.find(*self.CHECK_IN_INPUT)
        return element.get_attribute('value')
        
    def get_check_out_date(self):
        element = self.find(*self.CHECK_OUT_INPUT)
        return element.get_attribute('value')

    def get_room_status_badge_text(self, room_type_id):
        try:
            return self.get_text(*self.get_room_badge(room_type_id))
        except (TimeoutException, NoSuchElementException):
            return None
            
    def is_book_button_disabled(self, room_type_id):
        try:
            element = self.find(*self.get_book_button(room_type_id))
            # Nếu là button có class disabled hoặc có thuộc tính disabled
            return 'disabled' in element.get_attribute('class') or element.get_attribute('disabled') == 'true' or element.get_attribute('disabled') == 'disabled'
        except (TimeoutException, NoSuchElementException):
            return False
            
    def get_book_button_text(self, room_type_id):
        return self.get_text(*self.get_book_button(room_type_id))
        
    def click_book_button(self, room_type_id):
        self.click(*self.get_book_button(room_type_id))
