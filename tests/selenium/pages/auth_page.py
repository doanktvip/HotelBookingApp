from selenium.webdriver.common.by import By
from tests.selenium.pages.base_page import BasePage
import time


class AuthPage(BasePage):
    URL = "/login" 
    
    # Tabs
    LOGIN_TAB = (By.ID, "login-tab")
    REGISTER_TAB = (By.ID, "register-tab")
    
    # Đăng nhập
    LOGIN_FORM = (By.CSS_SELECTOR, "form[action='/login']")
    LOGIN_USERNAME = (By.CSS_SELECTOR, "form[action='/login'] input[name='username']")
    LOGIN_PASSWORD = (By.CSS_SELECTOR, "form[action='/login'] input[name='password']")
    LOGIN_SUBMIT = (By.CSS_SELECTOR, "form[action='/login'] button[type='submit']")
    
    # Form Đăng Ký
    REGISTER_FORM = (By.CSS_SELECTOR, "form[action='/register']")
    REGISTER_USERNAME = (By.CSS_SELECTOR, "form[action='/register'] input[name='username']")
    REGISTER_EMAIL = (By.CSS_SELECTOR, "form[action='/register'] input[name='email']")
    REGISTER_PASSWORD = (By.CSS_SELECTOR, "form[action='/register'] input[name='password']")
    REGISTER_CONFIRM_PASSWORD = (By.CSS_SELECTOR, "form[action='/register'] input[name='confirm_password']")
    REGISTER_SUBMIT = (By.CSS_SELECTOR, "form[action='/register'] button[type='submit']")
    
    TOAST_MESSAGE = (By.CSS_SELECTOR, ".alert-text")

    def open_page(self, base_url):
        self.open(base_url + self.URL)
        
    def switch_to_register_tab(self):
        self.click(*self.REGISTER_TAB)
        
    def switch_to_login_tab(self):
        self.click(*self.LOGIN_TAB)

    # Các hàm thao tác Đăng nhập
    def login(self, username, password):
        if username:
            self.typing(*self.LOGIN_USERNAME, username)
        if password:
            self.typing(*self.LOGIN_PASSWORD, password)
        self.click(*self.LOGIN_SUBMIT)
        time.sleep(1.5)

    def register(self, username, email, password, confirm_password):
        if username:
            self.typing(*self.REGISTER_USERNAME, username)
        if email:
            self.typing(*self.REGISTER_EMAIL, email)
        if password:
            self.typing(*self.REGISTER_PASSWORD, password)
        if confirm_password:
            self.typing(*self.REGISTER_CONFIRM_PASSWORD, confirm_password)
        self.click(*self.REGISTER_SUBMIT)
        
    def get_toast_message(self):
        return self.get_text(*self.TOAST_MESSAGE)
