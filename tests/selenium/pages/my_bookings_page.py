import time
from selenium.webdriver.common.by import By
from tests.selenium.pages.base_page import BasePage


class MyBookingsPage(BasePage):
    URL = "/my-bookings"

    def __init__(self, driver):
        super().__init__(driver)
        self.url = self.URL

    def open_page(self, base_url):
        self.driver.get(base_url + self.url)
        time.sleep(1)

    def get_booking_card(self, booking_id):
        xpath = f"//div[contains(@class, 'card')][.//span[contains(text(), '#{booking_id}')]]"
        try:
            return self.find(By.XPATH, xpath)
        except Exception:
            cards = self.driver.find_elements(By.CSS_SELECTOR, ".card")
            for card in cards:
                if f"#{booking_id}" in card.text:
                    return card
            return None

    def get_booking_card_by_code(self, booking_code):
        clean_code = str(booking_code).replace("BK-", "").replace("BK", "")
        xpath = f"//div[contains(@class, 'card')][.//span[contains(text(), '#{clean_code}') or contains(text(), 'BK-{clean_code}') or contains(text(), 'BK{clean_code}')]]"
        try:
            card = self.find(By.XPATH, xpath)
            self.scroll_to_card(card)
            return card
        except Exception:
            return None

    def scroll_to_card(self, booking_card):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", booking_card)
            time.sleep(0.5)
        except Exception:
            pass

    def get_status_badge(self, booking_card):
        try:
            return booking_card.find_element(By.XPATH, ".//span[contains(@class, 'badge')]")
        except Exception:
            return booking_card.find_element(By.CSS_SELECTOR, ".badge")

    def get_status_badge_text(self, booking_card):
        try:
            badge = self.get_status_badge(booking_card)
            return badge.text.strip()
        except Exception:
            return ""

    def get_card_status_badge_text(self, card):
        return self.get_status_badge_text(card)

    def get_cancel_button(self, booking_card):
        buttons = booking_card.find_elements(By.XPATH, ".//button[contains(., 'Hủy đặt phòng') or contains(., 'Hủy phòng')] | .//a[contains(., 'Hủy đặt phòng') or contains(., 'Hủy phòng')]")
        return buttons[0] if buttons else None

    def has_cancel_button(self, card):
        return self.is_cancel_button_visible(card)

    def is_cancel_button_visible(self, booking_card):
        btn = self.get_cancel_button(booking_card)
        return btn is not None and btn.is_displayed()

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

    def get_pay_button(self, booking_card):
        buttons = booking_card.find_elements(By.XPATH, ".//button[contains(., 'Thanh toán')] | .//a[contains(., 'Thanh toán')]")
        return buttons[0] if buttons else None

    def has_pay_button(self, card):
        return self.is_pay_button_visible(card)

    def is_pay_button_visible(self, booking_card):
        btn = self.get_pay_button(booking_card)
        return btn is not None and btn.is_displayed()

    def get_modal(self, booking_id):
        modal_id = f"cancelBookingModal{booking_id}"
        return self.driver.find_element(By.ID, modal_id)

    def click_confirm_cancel(self, booking_id):
        modal = self.get_modal(booking_id)
        confirm_btn = modal.find_element(By.XPATH, ".//button[contains(text(), 'Xác nhận hủy')]")
        self.driver.execute_script("arguments[0].click();", confirm_btn)
        time.sleep(1)

    def click_close_modal(self, booking_id):
        modal = self.get_modal(booking_id)
        close_btn = modal.find_element(By.XPATH, ".//button[contains(text(), 'Giữ đặt phòng')]")
        self.driver.execute_script("arguments[0].click();", close_btn)
        time.sleep(0.5)

    def get_toast_message(self):
        try:
            toast = self.driver.find_element(By.CSS_SELECTOR, ".alert-text")
            return toast.get_attribute("textContent").strip()
        except Exception:
            return ""
