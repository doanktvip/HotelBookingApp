import pytest
import time
from tests.selenium.pages.auth_page import AuthPage
from tests.selenium.pages.home_page import HomePage
from selenium.webdriver.common.by import By

def test_logout_success(live_server, selenium_driver, test_db, sample_customer):
    # 1. Login trước
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login("customer", "123456")
    
    home_page = HomePage(selenium_driver)
    
    # 2. Bấm avatar -> Logout
    # Bấm Đăng xuất bằng URL luôn cho chắc chắn do Bootstrap animation có thể che khuất
    selenium_driver.get(live_server.url + '/logout')

    # Kì vọng: Về trang chủ, không còn avatar
    assert not home_page.is_user_avatar_displayed(timeout=2)
    assert selenium_driver.current_url == live_server.url + "/" or "login" in selenium_driver.current_url
    home_page.take_screenshot("logout_success.png")

def test_access_protected_after_logout(live_server, selenium_driver, test_db, sample_customer):
    # 1. Login
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login("customer", "123456")
    
    # 2. Logout
    selenium_driver.get(live_server.url + '/logout')
    
    # 3. Cố truy cập lại trang bảo mật
    urls_to_test = ["/profile", "/my-bookings", "/recept"]
    for url in urls_to_test:
        selenium_driver.get(live_server.url + url)
        # Kì vọng: Bị chặn, về login
        assert "login" in selenium_driver.current_url
    auth_page.take_screenshot("logout_access_protected_denied.png")
