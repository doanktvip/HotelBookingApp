import sys
import os
from datetime import date, timedelta
from decimal import Decimal
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.models import (
    RoomStatus, Booking, BookingStatus, BookingDetail
)
from app.utils import get_vn_time
from tests.selenium.pages import HotelDetailPage, AuthPage, MyBookingsPage


def test_room_available_when_checkin_equals_previous_checkout(live_server, selenium_driver, sample_hotel, sample_room_type, sample_booking, sample_customer):
    hotel_page = HotelDetailPage(selenium_driver)
    hotel_page.open_page(live_server.url, sample_hotel.id)
    hotel_page.set_dates_and_check("2026-10-12", "2026-10-14")

    assert hotel_page.is_room_type_displayed(sample_room_type.name), f"Phòng '{sample_room_type.name}' không hiển thị!"

    badge_text = hotel_page.get_room_status_badge_text(sample_room_type.id)
    assert badge_text is not None, "Không tìm thấy nhãn trạng thái phòng!"
    assert "Hết phòng" not in badge_text, f"Phòng bị hiển thị 'Hết phòng': {badge_text}"
    assert "Còn" in badge_text and "trống" in badge_text, f"Phòng không ở trạng thái khả dụng: {badge_text}"

    page_text_lower = selenium_driver.page_source.lower()
    assert "overlapping booking" not in page_text_lower
    assert "trùng lịch" not in page_text_lower

    assert hotel_page.is_book_button_enabled(sample_room_type.id), "Nút 'Đặt phòng' bị vô hiệu hóa!"
    hotel_page.scroll_to_room_card(sample_room_type.name)
    hotel_page.take_screenshot("room_available_when_checkin_equals_previous_checkout.png")


def test_room_available_when_checkout_equals_next_checkin(live_server, selenium_driver, sample_hotel, sample_room_type, sample_booking, sample_customer):
    hotel_page = HotelDetailPage(selenium_driver)
    hotel_page.open_page(live_server.url, sample_hotel.id)
    hotel_page.set_dates_and_check("2026-10-10", "2026-10-12")

    assert hotel_page.is_room_type_displayed(sample_room_type.name), f"Phòng '{sample_room_type.name}' không hiển thị!"

    badge_text = hotel_page.get_room_status_badge_text(sample_room_type.id)
    assert badge_text is not None, "Không tìm thấy nhãn trạng thái phòng!"
    assert "Hết phòng" not in badge_text, f"Phòng bị hiển thị 'Hết phòng': {badge_text}"
    assert "Còn" in badge_text and "trống" in badge_text, f"Phòng không ở trạng thái khả dụng: {badge_text}"

    page_text_lower = selenium_driver.page_source.lower()
    assert "overlapping booking" not in page_text_lower
    assert "trùng lịch" not in page_text_lower

    assert hotel_page.is_book_button_enabled(sample_room_type.id), "Nút 'Đặt phòng' bị vô hiệu hóa!"
    hotel_page.scroll_to_room_card(sample_room_type.name)


def test_only_available_status_rooms_counted_for_today_checkin(live_server, selenium_driver, sample_hotel, sample_room_type, sample_booking, sample_customer):
    hotel_page = HotelDetailPage(selenium_driver)
    hotel_page.open_page(live_server.url, sample_hotel.id)

    today = get_vn_time().date()
    tomorrow = today + timedelta(days=1)
    hotel_page.set_dates_and_check(today.strftime("%Y-%m-%d"), tomorrow.strftime("%Y-%m-%d"))

    assert hotel_page.is_room_type_displayed(sample_room_type.name), f"Loại phòng '{sample_room_type.name}' không hiển thị!"

    badge_text = hotel_page.get_room_status_badge_text(sample_room_type.id)
    assert badge_text is not None

    assert hotel_page.is_book_button_enabled(sample_room_type.id), "Nút 'Đặt phòng' bị vô hiệu hóa!"
    hotel_page.scroll_to_room_card(sample_room_type.name)
    hotel_page.take_screenshot("only_available_status_rooms_counted_for_today.png")


def test_cancelled_booking_cannot_perform_further_actions(live_server, selenium_driver, test_session, sample_hotel, sample_room_type, sample_booking, sample_customer):
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(sample_customer.username, "123456")

    my_bookings = MyBookingsPage(selenium_driver)
    my_bookings.open_page(live_server.url)

    b_cancelled = test_session.query(Booking).filter_by(status=BookingStatus.CANCELLED).first()
    card = my_bookings.get_booking_card(b_cancelled.id)
    assert card is not None, "Không tìm thấy thẻ đơn đặt phòng đã hủy!"
    my_bookings.scroll_to_card(card)

    status_text = my_bookings.get_status_badge_text(card)
    assert "Đã hủy" in status_text or "CANCELLED" in status_text, f"Trạng thái không phải 'Đã hủy': '{status_text}'"

    assert not my_bookings.is_cancel_button_visible(card), "Nút 'Hủy đặt phòng' vẫn hiển thị đối với đơn đã hủy!"
    assert not my_bookings.is_pay_button_visible(card), "Nút 'Thanh toán' vẫn hiển thị đối với đơn đã hủy!"
    my_bookings.take_screenshot("cancelled_booking_cannot_perform_further_actions.png")
