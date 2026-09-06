import pytest
import time
from datetime import timedelta
from app.models import BookingStatus, RoomStatus
from app.utils import get_vn_time
from tests.selenium.pages.auth_page import AuthPage
from tests.selenium.pages.my_bookings_page import MyBookingsPage
from app.models import Booking, BookingDetail, Payment
import uuid

def login_and_goto_bookings(live_server, selenium_driver, customer):
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(customer.username, "123456")
    
    my_bookings_page = MyBookingsPage(selenium_driver)
    my_bookings_page.open_page(live_server.url)
    return my_bookings_page

def test_cancel_far_booking(live_server, selenium_driver, test_db, sample_customer, create_booking):
    """TC1: Hủy phòng khi thời gian hiện tại cách ngày check-in nhiều hơn 7 ngày"""
    b_id = create_booking('valid_far')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    
    card = page.get_booking_card(b_id)
    assert card is not None
    
    assert not page.is_cancel_button_disabled(card)
    page.click_cancel_button(card)
    
    modal = page.get_modal(b_id)
    assert modal is not None
    assert modal.is_displayed()
    
def test_cancel_edge_booking(live_server, selenium_driver, test_db, sample_customer, create_booking):
    """TC2: Kiểm tra biên: Thời gian hiện tại cách ngày check-in đúng 7 ngày"""
    b_id = create_booking('valid_edge')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    
    card = page.get_booking_card(b_id)
    assert card is not None
    
    assert not page.is_cancel_button_disabled(card)
    page.click_cancel_button(card)
    
    modal = page.get_modal(b_id)
    assert modal is not None
    assert modal.is_displayed()

def test_cancel_close_booking_disabled(live_server, selenium_driver, test_db, sample_customer, create_booking):
    """TC3: Hủy phòng khi thời gian hiện tại cách ngày check-in ít hơn 7 ngày"""
    b_id = create_booking('invalid_close')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    
    card = page.get_booking_card(b_id)
    assert card is not None
    
    assert page.is_cancel_button_disabled(card)

def test_confirm_cancellation(live_server, selenium_driver, test_db, sample_customer, create_booking):
    """TC4: Khách hàng xác nhận hủy thành công"""
    b_id = create_booking('valid_far')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    card = page.get_booking_card(b_id)
    page.click_cancel_button(card)
    page.click_confirm_cancel(b_id)
    
    # Chờ toast message
    toast = page.get_toast_message()
    assert "thành công" in toast.lower() or "hủy" in toast.lower()
    
    # Kiểm tra trạng thái đã chuyển sang Đã hủy
    card = page.get_booking_card(b_id)
    assert "Đã hủy" in card.text

def test_close_cancellation_modal(live_server, selenium_driver, test_db, sample_customer, create_booking):
    """TC5: Khách hàng nhấn Thoát trên hộp thoại xác nhận"""
    b_id = create_booking('valid_far')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    card = page.get_booking_card(b_id)
    page.click_cancel_button(card)
    page.click_close_modal(b_id)
    
    # Trạng thái giữ nguyên
    card = page.get_booking_card(b_id)
    assert "Thành công" in card.text or "Đã xác nhận" in card.text or "Đã đặt" in card.text

def test_cancelled_booking_cannot_be_cancelled_again(live_server, selenium_driver, test_db, sample_customer, create_booking):
    """TC6, TC9: Đơn đã ở trạng thái Đã hủy không hiển thị nút hủy"""
    b_id = create_booking('cancelled')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    card = page.get_booking_card(b_id)
    assert not page.is_cancel_button_visible(card)

def test_checked_in_booking_cannot_be_cancelled(live_server, selenium_driver, test_db, sample_customer, create_booking):
    """TC7: Đơn ở trạng thái Đang sử dụng không hiển thị nút hủy"""
    b_id = create_booking('checked_in')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    card = page.get_booking_card(b_id)
    assert not page.is_cancel_button_visible(card)

def test_checked_out_booking_cannot_be_cancelled(live_server, selenium_driver, test_db, sample_customer, create_booking):
    """TC8: Đơn ở trạng thái Đã hoàn tất không hiển thị nút hủy"""
    b_id = create_booking('checked_out')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    card = page.get_booking_card(b_id)
    assert not page.is_cancel_button_visible(card)
