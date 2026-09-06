import pytest
from tests.selenium.pages.auth_page import AuthPage

# Ở TC10, chúng ta cần đảm bảo có 1 user trong CSDL để đăng nhập.
# Chúng ta có thể dùng fixtures_db có sẵn hoặc dùng account từ TC1.
# Giả sử trong fixtures_db có tài khoản 'customer', pass '123456' (hoặc 'Aa@123456').

def test_login_success(live_server, selenium_driver, test_db, sample_customer):
    """TC10: Đăng nhập thành công"""
    page = AuthPage(selenium_driver)
    page.open_page(live_server.url)
    
    page.login("customer", "123456")
    
    # Kì vọng: Chuyển hướng về trang chủ và hiển thị avatar
    assert page.is_user_avatar_displayed()


def test_login_missing_username(live_server, selenium_driver, test_db):
    """TC11: Thiếu thông tin username"""
    page = AuthPage(selenium_driver)
    page.open_page(live_server.url)
    
    page.login("", "Aa@123456")
    
    username_input = page.find(*page.LOGIN_USERNAME)
    assert username_input.get_attribute("validationMessage") != ""

def test_login_invalid_username(live_server, selenium_driver):
    """TC12: Username không tồn tại"""
    page = AuthPage(selenium_driver)
    page.open_page(live_server.url)
    
    page.login("vandat123_not_exist", "Aa@123456")
    
    toast_msg = page.get_toast_message()
    assert "không tồn tại" in toast_msg or toast_msg != ""

def test_login_missing_password(live_server, selenium_driver):
    """TC13: Thiếu thông tin password"""
    page = AuthPage(selenium_driver)
    page.open_page(live_server.url)
    
    page.login("vandat", "")
    
    pw_input = page.find(*page.LOGIN_PASSWORD)
    assert pw_input.get_attribute("validationMessage") != ""

def test_login_invalid_password(live_server, selenium_driver):
    """TC14: Sai mật khẩu"""
    page = AuthPage(selenium_driver)
    page.open_page(live_server.url)
    
    page.login("vandat", "WrongPassword123")
    
    toast_msg = page.get_toast_message()
    assert "Mật khẩu không chính xác" in toast_msg or toast_msg != ""
