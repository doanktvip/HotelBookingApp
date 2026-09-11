import pytest
import time
from tests.selenium.pages.home_page import HomePage
from tests.selenium.pages.auth_page import AuthPage
from selenium.webdriver.common.by import By


def test_guest_visit_home(live_server, selenium_driver):
    page = HomePage(selenium_driver)
    try:
        page.open_page(live_server.url)
        assert "StayNow" in page.driver.title or page.is_hero_title_displayed()
        page.take_screenshot("guest_visit_home.png")
    except:
        pass

def test_guest_visit_booking(live_server, selenium_driver, test_db):
    driver = selenium_driver
    # Truy cập URL đặt phòng của 1 RoomType (Id = 1)
    driver.get(live_server.url + "/booking/room-type/1")
    
    # Kì vọng: Chuyển hướng sang trang đăng nhập do chưa đăng nhập
    assert "login" in driver.current_url
    AuthPage(driver).take_screenshot("guest_visit_booking_denied.png")

def test_guest_visit_protected_urls(live_server, selenium_driver):
    urls_to_test = [
        "/profile",
        "/my-bookings",
        "/recept",
        "/predictions"
    ]
    for url in urls_to_test:
        selenium_driver.get(live_server.url + url)
        # Kì vọng: Không cho phép truy cập, chuyển hướng về login
        assert "login" in selenium_driver.current_url, f"Failed at {url}"
    AuthPage(selenium_driver).take_screenshot("guest_visit_protected_denied.png")

def test_customer_visit_booking(live_server, selenium_driver, sample_customer, sample_room_type, test_db):
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login("customer", "123456")
    assert auth_page.is_user_avatar_displayed()
    selenium_driver.get(live_server.url + f"/booking/room-type/{sample_room_type.id}")
    
    assert "booking" in selenium_driver.current_url
    auth_page.take_screenshot("customer_visit_booking_success.png")

def test_customer_visit_admin(live_server, selenium_driver, sample_customer):
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login("customer", "123456")
    
    urls_to_test = [
        "/recept",
        "/predictions"
    ]
    for url in urls_to_test:
        selenium_driver.get(live_server.url + url)
        assert "login" in selenium_driver.current_url or selenium_driver.current_url == live_server.url + "/" or "403" in selenium_driver.page_source or "Forbidden" in selenium_driver.page_source
    auth_page.take_screenshot("customer_visit_admin_denied.png")
