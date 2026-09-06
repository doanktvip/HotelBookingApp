import pytest
import time
from unittest.mock import patch
from datetime import date, datetime, timedelta
from tests.selenium.pages.hotel_detail_page import HotelDetailPage
from tests.selenium.pages.booking_page import BookingPage
from tests.selenium.pages.auth_page import AuthPage
from app.models import Room, RoomStatus, RoomType, db
from selenium.webdriver.common.by import By
from decimal import Decimal

def wait_for_toast(selenium_driver):
    time.sleep(1)
    try:
        return selenium_driver.find_element(By.CSS_SELECTOR, ".alert-text").text
    except:
        return ""

def test_default_dates(live_server, selenium_driver, sample_hotel, specific_room_setup):
    page = HotelDetailPage(selenium_driver)
    
    # Warm up để tránh 500 error lần đầu tiên
    try:
        selenium_driver.get(live_server.url)
    except:
        pass
    
    page.open_page(live_server.url, sample_hotel.id)
    
    check_in = page.get_check_in_date()
    check_out = page.get_check_out_date()
    
    today = date.today().strftime('%Y-%m-%d')
    assert check_in == today, f"Expected check_in {today}, got {check_in}"
    expected_check_out = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    assert check_out == expected_check_out, f"Expected check_out {expected_check_out}, got {check_out}"

def test_auto_correct_past_check_in(live_server, selenium_driver, sample_hotel, specific_room_setup):
    page = HotelDetailPage(selenium_driver)
    page.open_page(live_server.url, sample_hotel.id)
    
    past_date = (date.today() - timedelta(days=5)).strftime('%Y-%m-%d')
    future_date = (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')
    
    # HTML5 min attribute prevent typing past date, so we manipulate DOM to bypass it if needed
    # But since date_sync.js auto corrects on change, we can test that
    selenium_driver.execute_script(f"document.getElementById('check_in').value = '{past_date}'; document.getElementById('check_in').dispatchEvent(new Event('change'));")
    
    time.sleep(0.5)
    check_in = page.get_check_in_date()
    today = date.today().strftime('%Y-%m-%d')
    assert check_in == today, f"Expected check_in to be corrected to {today}, got {check_in}"

def test_auto_correct_same_check_in_out(live_server, selenium_driver, sample_hotel, specific_room_setup):
    page = HotelDetailPage(selenium_driver)
    page.open_page(live_server.url, sample_hotel.id)
    
    today = date.today().strftime('%Y-%m-%d')
    selenium_driver.execute_script(f"document.getElementById('check_out').value = '{today}'; document.getElementById('check_out').dispatchEvent(new Event('change'));")
    
    time.sleep(0.5)
    check_out = page.get_check_out_date()
    expected_check_out = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    assert check_out == expected_check_out

def test_auto_correct_invalid_check_out(live_server, selenium_driver, sample_hotel, specific_room_setup):
    page = HotelDetailPage(selenium_driver)
    page.open_page(live_server.url, sample_hotel.id)
    
    tomorrow = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    selenium_driver.execute_script(f"document.getElementById('check_in').value = '{tomorrow}'; document.getElementById('check_in').dispatchEvent(new Event('change'));")
    
    time.sleep(0.5)
    check_out = page.get_check_out_date()
    expected_check_out = (date.today() + timedelta(days=2)).strftime('%Y-%m-%d')
    assert check_out == expected_check_out

def test_maintenance_room(live_server, selenium_driver, sample_hotel, specific_room_setup):
    rt_a, rt_b, rt_c = specific_room_setup
    page = HotelDetailPage(selenium_driver)
    page.open_page(live_server.url, sample_hotel.id)
    
    badge_text = page.get_room_status_badge_text(rt_c.id)
    assert "Hết phòng" in badge_text or "Đã hết" in badge_text
    assert page.is_book_button_disabled(rt_c.id)

def test_no_available_room(live_server, selenium_driver, sample_hotel, specific_room_setup):
    rt_a, rt_b, rt_c = specific_room_setup
    page = HotelDetailPage(selenium_driver)
    page.open_page(live_server.url, sample_hotel.id)
    
    badge_text = page.get_room_status_badge_text(rt_b.id)
    assert "Hết phòng" in badge_text or "Đã hết" in badge_text
    assert page.is_book_button_disabled(rt_b.id)

def test_show_correct_available_count(live_server, selenium_driver, sample_hotel, specific_room_setup):
    rt_a, rt_b, rt_c = specific_room_setup
    page = HotelDetailPage(selenium_driver)
    page.open_page(live_server.url, sample_hotel.id)
    
    badge_text = page.get_room_status_badge_text(rt_a.id)
    assert "Còn 3 trống" in badge_text
    assert not page.is_book_button_disabled(rt_a.id)

def test_readonly_user_info(live_server, selenium_driver, sample_customer, sample_room_type):
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login("customer", "123456")
    
    page = BookingPage(selenium_driver)
    page.open_page(live_server.url, sample_room_type.id)
    
    assert page.is_customer_info_readonly()
    info = page.get_customer_info()
    assert info["name"] == "customer"
    assert info["email"] == "customer@gmail.com"

def test_correct_room_info(live_server, selenium_driver, sample_customer, sample_room_type):
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login("customer", "123456")
    
    page = BookingPage(selenium_driver)
    page.open_page(live_server.url, sample_room_type.id)
    
    source = selenium_driver.page_source
    assert sample_room_type.name in source
    assert sample_room_type.hotel.name in source
    expected_price = "{:,.0f}".format(sample_room_type.base_price).replace(',', '.')
    assert expected_price in page.get_base_price()

def test_limit_quantity(live_server, selenium_driver, sample_customer, specific_room_setup):
    rt_a, rt_b, rt_c = specific_room_setup
    
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login("customer", "123456")
    
    page = BookingPage(selenium_driver)
    page.open_page(live_server.url, rt_a.id) # rt_a has 3 rooms
    
    options = page.get_quantity_options()
    assert len(options) == 3
    assert options == ["1", "2", "3"]

@patch('app.routes.booking.MoMoService.create_payment_request')
def test_accept_valid_booking(mock_create_payment, live_server, selenium_driver, sample_customer, specific_room_setup):
    mock_create_payment.return_value = {
        'resultCode': 0,
        'payUrl': 'http://mock-momo-url.com/pay',
        'qrCodeUrl': 'http://mock.com/qr',
        'amount': 1000000,
        'orderId': 'MOCK_ORDER',
        'orderInfo': 'Mock Order Info',
        'extraData': 'MockExtraData'
    }

    rt_a, rt_b, rt_c = specific_room_setup
    
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login("customer", "123456")
    
    page = BookingPage(selenium_driver)
    page.open_page(live_server.url, rt_a.id)
    
    page.select_quantity(1)
    page.select_payment_method("MOMO")
    page.submit_booking()
    
    time.sleep(2) # Wait for redirect
    assert "Thanh toán MoMo" in selenium_driver.page_source or "momo" in selenium_driver.current_url.lower() or "mock-momo-url" in selenium_driver.current_url.lower()

@patch('app.routes.booking.MoMoService.create_payment_request')
def test_momo_creation_failed(mock_create_payment, live_server, selenium_driver, sample_customer, specific_room_setup):
    mock_create_payment.return_value = {
        'resultCode': 1001,
        'message': 'Giao dịch bị từ chối bởi MoMo'
    }

    rt_a, rt_b, rt_c = specific_room_setup
    
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login("customer", "123456")
    
    page = BookingPage(selenium_driver)
    page.open_page(live_server.url, rt_a.id)
    
    page.select_quantity(1)
    page.select_payment_method("MOMO")
    page.submit_booking()
    
    toast = wait_for_toast(selenium_driver)
    assert "lỗi từ cổng thanh toán momo" in toast.lower() or "giao dịch bị từ chối" in toast.lower()

def test_reject_zero_quantity(live_server, selenium_driver, sample_customer, specific_room_setup):
    rt_a, rt_b, rt_c = specific_room_setup
    
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login("customer", "123456")
    
    page = BookingPage(selenium_driver)
    page.open_page(live_server.url, rt_a.id)
    
    # Bỏ qua validate HTML để test backend
    selenium_driver.execute_script("document.getElementById('quantity').innerHTML = '<option value=\"0\">0</option>';")
    page.select_quantity(0)
    page.submit_booking()
    
    toast = wait_for_toast(selenium_driver)
    assert "số lượng phòng" in toast.lower() or "không hợp lệ" in toast.lower()

def test_reject_exceed_available_quantity(live_server, selenium_driver, sample_customer, specific_room_setup):
    rt_a, rt_b, rt_c = specific_room_setup
    
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login("customer", "123456")
    
    page = BookingPage(selenium_driver)
    page.open_page(live_server.url, rt_a.id) # rt_a has 3 rooms
    
    # Bỏ qua validate HTML để test backend
    selenium_driver.execute_script("document.getElementById('quantity').innerHTML += '<option value=\"5\">5</option>';")
    page.select_quantity(5)
    page.submit_booking()
    
    toast = wait_for_toast(selenium_driver)
    assert "chỉ còn" in toast.lower() or "phòng trống" in toast.lower() or "không hợp lệ" in toast.lower()

def test_vnpay_not_supported(live_server, selenium_driver, sample_customer, specific_room_setup):
    rt_a, rt_b, rt_c = specific_room_setup
    
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login("customer", "123456")
    
    page = BookingPage(selenium_driver)
    page.open_page(live_server.url, rt_a.id)
    
    page.select_payment_method("VNPAY")
    page.submit_booking()
    
    toast = wait_for_toast(selenium_driver)
    assert "chưa được hỗ trợ" in toast.lower() or "not supported" in toast.lower()
