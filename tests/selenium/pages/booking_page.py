from selenium.webdriver.common.by import By
from .base_page import BasePage
from selenium.webdriver.support.ui import Select

class BookingPage(BasePage):
    """Page Object Model for the Booking Confirmation Page"""
    
    # Locators
    CUSTOMER_NAME_INPUT = (By.ID, "name")
    CUSTOMER_EMAIL_INPUT = (By.ID, "email")
    CUSTOMER_PHONE_INPUT = (By.ID, "phone")
    
    CHECK_IN_INPUT = (By.ID, "check_in")
    CHECK_OUT_INPUT = (By.ID, "check_out")
    QUANTITY_SELECT = (By.ID, "quantity")
    
    PAY_MOMO_RADIO = (By.ID, "pay_momo")
    PAY_VNPAY_RADIO = (By.ID, "pay_vnpay")
    
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "#bookingForm button[type='submit']")
    
    BASE_PRICE = (By.ID, "basePrice")
    SUMMARY_TOTAL = (By.ID, "summary-total")
    SUMMARY_QTY = (By.ID, "summary-qty")
    
    def open_page(self, base_url, room_type_id):
        self.open(f"{base_url}/booking/room-type/{room_type_id}")
        
    def get_customer_info(self):
        return {
            "name": self.find(*self.CUSTOMER_NAME_INPUT).get_attribute("value"),
            "email": self.find(*self.CUSTOMER_EMAIL_INPUT).get_attribute("value"),
            "phone": self.find(*self.CUSTOMER_PHONE_INPUT).get_attribute("value")
        }
        
    def is_customer_info_readonly(self):
        name_readonly = self.find(*self.CUSTOMER_NAME_INPUT).get_attribute("readonly")
        email_readonly = self.find(*self.CUSTOMER_EMAIL_INPUT).get_attribute("readonly")
        phone_readonly = self.find(*self.CUSTOMER_PHONE_INPUT).get_attribute("readonly")
        return bool(name_readonly) and bool(email_readonly) and bool(phone_readonly)
        
    def get_base_price(self):
        return self.get_text(*self.BASE_PRICE)
        
    def get_summary_total(self):
        return self.get_text(*self.SUMMARY_TOTAL)
        
    def get_quantity_options(self):
        select = self.find(*self.QUANTITY_SELECT)
        options = select.find_elements(By.TAG_NAME, "option")
        return [opt.get_attribute("value") for opt in options]
        
    def select_quantity(self, quantity):
        select = self.find(*self.QUANTITY_SELECT)
        sel = Select(select)
        sel.select_by_value(str(quantity))
        
    def select_payment_method(self, method="MOMO"):
        if method == "MOMO":
            self.js_click(By.CSS_SELECTOR, "label[for='pay_momo']")
        elif method == "VNPAY":
            self.js_click(By.CSS_SELECTOR, "label[for='pay_vnpay']")
            
    def submit_booking(self):
        self.js_click(*self.SUBMIT_BUTTON)
