from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from tests.selenium.pages.base_page import BasePage
import time


class ManageBookingsPage(BasePage):
    URL = "/recept?tab=list"

    SEARCH_INPUT = (By.CSS_SELECTOR, "#search-input, input[name='search']")
    STATUS_SELECT = (By.CSS_SELECTOR, "#status-filter, select[name='status']")
    DATE_SELECT = (By.NAME, "check_in_date")
    SUBMIT_BTN = (By.CSS_SELECTOR, "#search-btn, button[type='submit']")
    BOOKING_ROWS = (By.CSS_SELECTOR, "tbody tr.booking-row, tbody tr.border-bottom")
    EMPTY_ROW = (By.CSS_SELECTOR, "tbody tr td.empty-bookings-cell, tbody tr td.text-center")
    TAB_LIST = (By.CSS_SELECTOR, "button[data-bs-target='#bookings-content']")
    NAV_MANAGE_BOOKINGS = (By.XPATH, "//a[contains(., 'Quản lý đơn đặt phòng')] | //button[contains(., 'Quản lý đơn đặt phòng')]")

    # Modal Checkout
    CHECKOUT_MODAL = (By.ID, "checkoutModal")
    CHECKOUT_ROOM_PRICE = (By.ID, "checkout_room_price")
    CHECKOUT_LATE_FEE = (By.ID, "checkout_late_fee")
    CHECKOUT_LATE_FEE_ROW = (By.ID, "late_fee_row")
    CHECKOUT_TOTAL = (By.ID, "checkout_total")
    CHECKOUT_PAID = (By.ID, "checkout_paid")
    CHECKOUT_BALANCE = (By.ID, "checkout_balance")
    CHECKOUT_ALERT = (By.ID, "checkout_alert")
    CONFIRM_CHECKOUT_BTN = (By.ID, "confirmCheckoutBtn")
    CLOSE_MODAL_BTN = (By.CSS_SELECTOR, "#cancelCheckoutBtn, #checkoutModal .btn-close")

    def open_page(self, base_url, tab="list", endpoint="/reception/bookings"):
        self.open(f"{base_url}{endpoint}?tab={tab}")
        self.switch_to_list_tab()

    def click_manage_booking_nav(self):
        self.click(*self.NAV_MANAGE_BOOKINGS)
        time.sleep(1)
        self.switch_to_list_tab()

    def switch_to_list_tab(self):
        try:
            tab_pane = self.find(By.ID, "bookings-content")
            if "active" not in (tab_pane.get_attribute("class") or ""):
                self.click(*self.TAB_LIST)
                time.sleep(0.5)
        except Exception:
            pass

    def search(self, text="", status="ALL", date=""):
        time.sleep(0.5)  # Wait for page to be fully interactive
        input_el = self.find(*self.SEARCH_INPUT)
        self.driver.execute_script("arguments[0].value = '';", input_el)
        time.sleep(0.2)
        if text:
            self.driver.execute_script("arguments[0].value = arguments[1];", input_el, text)
            time.sleep(0.2)

        status_el = self.find(*self.STATUS_SELECT)
        sel_status = Select(status_el)
        try:
            sel_status.select_by_value(status)
            time.sleep(0.2)
        except Exception:
            pass

        if date:
            date_el = self.find(*self.DATE_SELECT)
            sel_date = Select(date_el)
            try:
                sel_date.select_by_value(date)
                time.sleep(0.2)
            except Exception:
                pass

        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        btn = self.find(*self.SUBMIT_BTN)
        old_url = self.driver.current_url
        self.driver.execute_script("arguments[0].click();", btn)
        
        try:
            WebDriverWait(self.driver, 5).until(EC.staleness_of(btn))
        except:
            pass
        
        time.sleep(1)

    def get_booking_rows(self):
        try:
            return self.finds(*self.BOOKING_ROWS)
        except Exception:
            return []

    def get_booking_codes(self):
        try:
            cells = self.finds(By.CSS_SELECTOR, ".booking-code-cell")
            return [c.get_attribute("textContent").strip() for c in cells]
        except Exception:
            return []

    def get_booking_row_by_code(self, code):
        xpath = f"//tr[contains(@class, 'booking-row') or contains(@class, 'border-bottom')][.//td[contains(@class, 'booking-code-cell') and contains(text(), '{code}')]]"
        return self.find(By.XPATH, xpath)

    def get_booking_row_by_id(self, booking_id):
        booking_code = f"BK{booking_id:03d}"
        xpath = f"//tr[contains(@class, 'booking-row') or contains(@class, 'border-bottom')][.//td[contains(@class, 'booking-code-cell') and (contains(text(), '{booking_code}') or contains(text(), 'BK-{booking_id}') or contains(text(), '{booking_id}'))]]"
        row = self.find(By.XPATH, xpath)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row)
        return row

    def get_row_data(self, row):
        def _safe_text(selector):
            try:
                return row.find_element(By.CSS_SELECTOR, selector).text.strip()
            except Exception:
                return ""

        return {
            "code": _safe_text(".booking-code-cell"),
            "customer_name": _safe_text(".customer-name-cell"),
            "phone": _safe_text(".customer-phone-cell"),
            "room_type": _safe_text(".room-type-cell"),
            "room_number": _safe_text(".room-number-cell"),
            "check_in": _safe_text(".checkin-date-cell"),
            "check_out": _safe_text(".checkout-date-cell"),
            "status": _safe_text(".status-cell")
        }

    def get_row_status_text(self, row):
        try:
            status_el = row.find_element(By.CSS_SELECTOR, ".status-cell")
            text = (status_el.text or "").strip()
            if not text:
                text = (status_el.get_attribute("textContent") or "").strip()
            return text
        except Exception:
            return ""

    def has_checkin_button(self, row):
        btns = row.find_elements(By.CSS_SELECTOR, "button[value='checkin'], .checkin-btn, button[id^='checkin-btn-']")
        if not btns:
            return False
        btn = btns[0]
        if not btn.is_displayed():
            return False
        if btn.get_attribute("disabled") is not None or not btn.is_enabled():
            return False
        return True

    def has_checkout_button(self, row):
        btns = row.find_elements(By.CSS_SELECTOR, "button[onclick*='openCheckoutModal'], .checkout-btn, button[id^='checkout-btn-']")
        if not btns:
            return False
        btn = btns[0]
        if not btn.is_displayed():
            return False
        if btn.get_attribute("disabled") is not None or not btn.is_enabled():
            return False
        return True

    def is_empty_message_displayed(self):
        return self.is_displayed(*self.EMPTY_ROW)

    def get_empty_message_text(self):
        return self.get_text(*self.EMPTY_ROW)

    def click_checkin(self, booking_id):
        xpath = f"//button[@id='checkin-btn-{booking_id}'] | //td[contains(text(), 'BK-{booking_id}') or contains(text(), 'BK{booking_id:03d}')]/..//button[@value='checkin']"
        btn = self.find(By.XPATH, xpath)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", btn)
        time.sleep(0.5)

    def click_checkout(self, booking_id):
        xpath = f"//button[@id='checkout-btn-{booking_id}'] | //td[contains(text(), 'BK-{booking_id}') or contains(text(), 'BK{booking_id:03d}')]/..//button[contains(., 'Check-out')]"
        btn = self.find(By.XPATH, xpath)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", btn)
        self.wait_for_checkout_modal()

    def wait_for_checkout_modal(self):
        self.find(*self.CHECKOUT_MODAL)
        time.sleep(1)

    def confirm_checkout(self):
        btn = self.find(*self.CONFIRM_CHECKOUT_BTN)
        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(1)

    def close_checkout_modal(self):
        try:
            btn = self.find(By.CSS_SELECTOR, "#cancelCheckoutBtn, #checkoutModal .btn-close")
            self.driver.execute_script("arguments[0].click();", btn)
        except Exception:
            pass
        time.sleep(1)

    def get_checkout_modal_details(self):
        self.wait_for_checkout_modal()
        confirm_btn = self.find(*self.CONFIRM_CHECKOUT_BTN)
        is_disabled = (confirm_btn.get_attribute("disabled") is not None) or (not confirm_btn.is_enabled())
        return {
            "room_price": self.get_text(*self.CHECKOUT_ROOM_PRICE),
            "late_fee": self.get_text(*self.CHECKOUT_LATE_FEE),
            "total": self.get_text(*self.CHECKOUT_TOTAL),
            "paid": self.get_text(*self.CHECKOUT_PAID),
            "balance": self.get_text(*self.CHECKOUT_BALANCE),
            "is_confirm_disabled": is_disabled,
            "alert_displayed": self.is_displayed(*self.CHECKOUT_ALERT)
        }

