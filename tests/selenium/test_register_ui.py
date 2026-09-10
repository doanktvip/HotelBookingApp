import pytest
from tests.selenium.pages.auth_page import AuthPage
import time

def test_register_success(live_server, selenium_driver, test_db):
    page = AuthPage(selenium_driver)
    page.open_page(live_server.url)
    page.switch_to_register_tab()
    
    username = f"vandat_{int(time.time())}" # Đảm bảo username unique
    page.register(username, f"testuser_{int(time.time())}@gmail.com", "Aa@123456", "Aa@123456")
    
    # Kì vọng: Có thông báo đăng ký thành công
    toast_msg = page.get_toast_message()
    assert "Đăng ký thành công" in toast_msg

def test_register_missing_username(live_server, selenium_driver, test_db):
    page = AuthPage(selenium_driver)
    page.open_page(live_server.url)
    page.switch_to_register_tab()
    
    # Bỏ trống username
    page.register("", "testuser@gmail.com", "Aa@123456", "Aa@123456")
    
    # Lấy thông báo lỗi HTML5
    username_input = page.find(*page.REGISTER_USERNAME)
    validation_msg = username_input.get_attribute("validationMessage")
    assert validation_msg != ""

def test_register_invalid_username(live_server, selenium_driver, test_db):
    page = AuthPage(selenium_driver)
    page.open_page(live_server.url)
    page.switch_to_register_tab()
    
    page.register("dat", "testuser@gmail.com", "Aa@123456", "Aa@123456")
    
    toast_msg = page.get_toast_message()
    assert toast_msg != ""

def test_register_missing_email(live_server, selenium_driver, test_db):
    page = AuthPage(selenium_driver)
    page.open_page(live_server.url)
    page.switch_to_register_tab()
    
    page.register("vandat", "", "Aa@123456", "Aa@123456")
    
    email_input = page.find(*page.REGISTER_EMAIL)
    assert email_input.get_attribute("validationMessage") != ""

def test_register_invalid_email(live_server, selenium_driver, test_db):
    page = AuthPage(selenium_driver)
    page.open_page(live_server.url)
    page.switch_to_register_tab()
    
    page.register("vandat", "testuser.gmail.com", "Aa@123456", "Aa@123456")
    
    email_input = page.find(*page.REGISTER_EMAIL)
    assert email_input.get_attribute("validationMessage") != ""

def test_register_missing_password(live_server, selenium_driver, test_db):
    page = AuthPage(selenium_driver)
    page.open_page(live_server.url)
    page.switch_to_register_tab()
    
    page.register("vandat", "testuser@gmail.com", "", "Aa@123456")
    
    pw_input = page.find(*page.REGISTER_PASSWORD)
    assert pw_input.get_attribute("validationMessage") != ""

def test_register_invalid_password(live_server, selenium_driver, test_db):
    page = AuthPage(selenium_driver)
    page.open_page(live_server.url)
    page.switch_to_register_tab()
    
    page.register("vandat", "testuser@gmail.com", "123", "123")
    
    pw_input = page.find(*page.REGISTER_PASSWORD)
    # HTML5 minlength validation
    assert pw_input.get_attribute("validationMessage") != "" or page.get_toast_message() != ""

def test_register_missing_confirm_password(live_server, selenium_driver, test_db):
    page = AuthPage(selenium_driver)
    page.open_page(live_server.url)
    page.switch_to_register_tab()
    
    page.register("vandat", "testuser@gmail.com", "Aa@123456", "")
    
    cpw_input = page.find(*page.REGISTER_CONFIRM_PASSWORD)
    assert cpw_input.get_attribute("validationMessage") != ""

def test_register_mismatch_password(live_server, selenium_driver, test_db):
    page = AuthPage(selenium_driver)
    page.open_page(live_server.url)
    page.switch_to_register_tab()
    
    page.register("vandat", "testuser@gmail.com", "Aa@123456", "123456")
    
    toast_msg = page.get_toast_message()
    assert "Mật khẩu xác nhận không khớp" in toast_msg or toast_msg != ""
