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
    b_id = create_booking('valid_far')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    
    card = page.get_booking_card(b_id)
    assert card is not None
    
    assert not page.is_cancel_button_disabled(card)
    page.click_cancel_button(card)
    
    modal = page.get_modal(b_id)
    assert modal is not None
    assert modal.is_displayed()
    page.take_screenshot("cancel_far_booking_modal.png")
    
def test_cancel_edge_booking(live_server, selenium_driver, test_db, sample_customer, create_booking):
    b_id = create_booking('valid_edge')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    
    card = page.get_booking_card(b_id)
    assert card is not None
    
    assert not page.is_cancel_button_disabled(card)
    page.click_cancel_button(card)
    
    modal = page.get_modal(b_id)
    assert modal is not None
    assert modal.is_displayed()
    page.take_screenshot("cancel_edge_booking_modal.png")

def test_cancel_close_booking_disabled(live_server, selenium_driver, test_db, sample_customer, create_booking):
    b_id = create_booking('invalid_close')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    
    card = page.get_booking_card(b_id)
    assert card is not None
    
    assert page.is_cancel_button_disabled(card)
    page.take_screenshot("cancel_close_booking_disabled.png")

def test_confirm_cancellation(live_server, selenium_driver, test_db, sample_customer, create_booking):
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
    page.take_screenshot("confirm_cancellation_success.png")

def test_close_cancellation_modal(live_server, selenium_driver, test_db, sample_customer, create_booking):
    b_id = create_booking('valid_far')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    card = page.get_booking_card(b_id)
    page.click_cancel_button(card)
    page.click_close_modal(b_id)
    
    card = page.get_booking_card(b_id)
    assert "Thành công" in card.text or "Đã xác nhận" in card.text or "Đã đặt" in card.text
    page.take_screenshot("close_cancellation_modal.png")

def test_cancelled_booking_cannot_be_cancelled_again(live_server, selenium_driver, test_db, sample_customer, create_booking):
    b_id = create_booking('cancelled')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    card = page.get_booking_card(b_id)
    assert not page.is_cancel_button_visible(card)
    page.take_screenshot("cancelled_cannot_cancel_again.png")

def test_checked_in_booking_cannot_be_cancelled(live_server, selenium_driver, test_db, sample_customer, create_booking):
    b_id = create_booking('checked_in')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    card = page.get_booking_card(b_id)
    assert not page.is_cancel_button_visible(card)
    page.take_screenshot("checked_in_cannot_cancel.png")

def test_checked_out_booking_cannot_be_cancelled(live_server, selenium_driver, test_db, sample_customer, create_booking):
    b_id = create_booking('checked_out')
    page = login_and_goto_bookings(live_server, selenium_driver, sample_customer)
    card = page.get_booking_card(b_id)
    assert not page.is_cancel_button_visible(card)
    page.take_screenshot("checked_out_cannot_cancel.png")
