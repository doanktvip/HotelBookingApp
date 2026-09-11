import pytest
from datetime import timedelta
import uuid
from app.models import BookingStatus, RoomStatus
from app.utils import get_vn_time
from tests.selenium.pages.auth_page import AuthPage
from tests.selenium.pages.manage_bookings_page import ManageBookingsPage
from unittest.mock import patch
from app.models import User, UserRole, Booking, BookingDetail, Payment
from app.models import Booking
from app.extensions import db
import datetime


def login_and_goto_manage(live_server, selenium_driver, user):
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(user.username, "123456")
    page = ManageBookingsPage(selenium_driver)
    page.open(f"{live_server.url}{page.URL}")
    return page

def test_receptionist_view_bookings(live_server, selenium_driver, setup_recept_data):
    recept, _, create_b = setup_recept_data
    create_b('confirmed_today')
    page = login_and_goto_manage(live_server, selenium_driver, recept)
    
    rows = page.get_booking_rows()
    assert len(rows) > 0, "Danh sách không được trống"
    page.take_screenshot("recept_view_bookings.png")

def test_customer_access_denied(live_server, selenium_driver, sample_customer):
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(sample_customer.username, "123456")
    
    page = ManageBookingsPage(selenium_driver)
    page.open(f"{live_server.url}{page.URL}")
    
    # Phải bị đá về trang nào đó hoặc lỗi 403. Nếu 403, title sẽ là Error hoặc về trang chủ
    assert "403" in selenium_driver.page_source or "Quản lý phòng" not in selenium_driver.title
    auth_page.take_screenshot("customer_manage_booking_denied.png")

def test_search_booking(live_server, selenium_driver, setup_recept_data, sample_customer):
    recept, _, create_b = setup_recept_data
    b_id = create_b('confirmed_today')
    page = login_and_goto_manage(live_server, selenium_driver, recept)
    
    # TC5: Search by ID
    page.search(text=f"BK-{b_id}")
    assert len(page.get_booking_rows()) == 1
    
    # TC6 & TC10: Search by name part
    page.search(text=sample_customer.username[:3])
    assert len(page.get_booking_rows()) >= 1
    
    # TC7: Search by phone
    page.search(text=sample_customer.phone)
    assert len(page.get_booking_rows()) >= 1
    
    # TC8: Not found
    page.search(text="NOT_FOUND_QUERY")
    assert len(page.get_booking_rows()) == 0
    assert page.is_empty_message_displayed()
    
    # TC9: Empty search
    page.search(text="")
    assert len(page.get_booking_rows()) >= 1
    page.take_screenshot("search_booking.png")

def test_filter_status_and_date(live_server, selenium_driver, setup_recept_data):
    recept, _, create_b = setup_recept_data
    create_b('confirmed_today')
    create_b('cancelled')
    
    page = login_and_goto_manage(live_server, selenium_driver, recept)
    
    # Filter 'CONFIRMED'
    page.search(status="CONFIRMED")
    assert len(page.get_booking_rows()) >= 1
    
    # Filter 'CANCELLED'
    page.search(status="CANCELLED")
    assert len(page.get_booking_rows()) >= 1
    
    # Filter Date = today
    page.search(status="ALL", date="today")
    assert len(page.get_booking_rows()) >= 2
    page.take_screenshot("filter_status_and_date.png")

def test_checkin(live_server, selenium_driver, setup_recept_data):
    recept, _, create_b = setup_recept_data
    b1 = create_b('confirmed_today') # TC14
    b2 = create_b('occupied') # TC15
    b3 = create_b('cancelled') # TC16
    
    page = login_and_goto_manage(live_server, selenium_driver, recept)
    
    # TC14: Valid checkin
    page.click_checkin(b1)
    
    # Thao tác click_checkin sẽ reload trang. Trạng thái hiển thị sẽ thành 'Đang sử dụng'
    page.open(f"{live_server.url}{page.URL}")
    page.search(text=f"BK-{b1}")
    row_html = page.get_booking_rows()[0].get_attribute('innerHTML')
    assert ("Đang dùng" in row_html) or ("Đang sử dụng" in row_html)
    
    # TC15: Already occupied -> should not have checkin button
    page.search(text=f"BK-{b2}")
    row_html = page.get_booking_rows()[0].get_attribute('innerHTML')
    assert "value=\"checkin\"" not in row_html
    
    # TC16: Cancelled -> should not have checkin button
    page.search(text=f"BK-{b3}")
    row_html = page.get_booking_rows()[0].get_attribute('innerHTML')
    assert "value=\"checkin\"" not in row_html
    page.take_screenshot("checkin_flow.png")

def test_checkout_flow(live_server, selenium_driver, setup_recept_data):
    recept, _, create_b = setup_recept_data
    b1 = create_b('occupied')
    
    page = login_and_goto_manage(live_server, selenium_driver, recept)
    
    # Tìm đơn đang ở
    page.search(text=f"BK-{b1}")
    
    # TC17: Thực hiện check-out trực tiếp
    page.click_checkout(b1)
    page.confirm_checkout()
    
    # Sau khi xác nhận, reload danh sách
    page.open(f"{live_server.url}{page.URL}")
    page.search(text=f"BK-{b1}")
    row_html = page.get_booking_rows()[0].get_attribute('innerHTML')
    assert "Hoàn thành" in row_html
    page.take_screenshot("checkout_flow.png")


