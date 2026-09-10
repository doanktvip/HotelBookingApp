import time
from selenium.webdriver.common.by import By
from .base_page import BasePage


class HotelDetailPage(BasePage):
    CHECK_IN_INPUT = (By.ID, "check_in")
    CHECK_OUT_INPUT = (By.ID, "check_out")
    CHECK_BUTTON = (By.XPATH, "//button[@id='search-btn'] | //button[@type='submit' and (contains(text(), 'Tìm kiếm') or contains(text(), 'Kiểm tra'))] | //button[@type='submit']")

    def get_room_badge(self, room_type_id):
        return (By.ID, f"room-avail-badge-{room_type_id}")

    def get_book_button(self, room_type_id):
        return (By.ID, f"room-book-btn-{room_type_id}")

    def open_page(self, base_url, hotel_id):
        self.open(f"{base_url}/hotels/{hotel_id}")

    def set_dates_and_check(self, check_in_str, check_out_str):
        self.js_typing(*self.CHECK_IN_INPUT, check_in_str)
        self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", self.find(*self.CHECK_IN_INPUT))
        self.js_typing(*self.CHECK_OUT_INPUT, check_out_str)
        self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", self.find(*self.CHECK_OUT_INPUT))
        self.js_click(*self.CHECK_BUTTON)
        time.sleep(1)

    def get_check_in_date(self):
        element = self.find(*self.CHECK_IN_INPUT)
        return element.get_attribute('value')

    def get_check_out_date(self):
        element = self.find(*self.CHECK_OUT_INPUT)
        return element.get_attribute('value')

    def is_room_type_displayed(self, room_type_name):
        return self.is_displayed(By.XPATH, f"//h5[contains(text(), '{room_type_name}')]")

    def get_room_status_badge_text(self, room_type_id):
        text = self.get_text(*self.get_room_badge(room_type_id))
        return text if text else None

    def is_book_button_disabled(self, room_type_id):
        try:
            element = self.find(*self.get_book_button(room_type_id))
            disabled_attr = element.get_attribute("disabled")
            return "disabled" in (element.get_attribute("class") or "") or disabled_attr in ("true", "disabled", "")
        except Exception:
            return False

    def is_book_button_enabled(self, room_type_id):
        try:
            element = self.find(*self.get_book_button(room_type_id))
            return element.is_enabled() and ("disabled" not in (element.get_attribute("class") or ""))
        except Exception:
            return False

    def get_book_button_text(self, room_type_id):
        return self.get_text(*self.get_book_button(room_type_id))

    def click_book_button(self, room_type_id):
        self.click(*self.get_book_button(room_type_id))

    def scroll_to_room_card(self, room_type_name):
        try:
            xpath = f"//div[contains(@class, 'custom-room-card')][.//h5[contains(text(), '{room_type_name}')]]"
            card = self.find(By.XPATH, xpath)
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", card)
            time.sleep(0.5)
        except Exception:
            pass

