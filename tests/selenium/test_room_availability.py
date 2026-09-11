import sys
import os
from datetime import date
from decimal import Decimal
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.models import (
    RoomStatus, Booking, BookingStatus, BookingDetail
)
from tests.selenium.pages import HotelDetailPage


def test_room_available_when_booking_on_checkout_date(
    live_server, selenium_driver, sample_hotel, sample_room_type, sample_booking
):
    room_type_id = sample_room_type.id
    room_type_name = sample_room_type.name
    hotel_id = sample_hotel.id

    page = HotelDetailPage(selenium_driver)
    page.open_page(live_server.url, hotel_id)

    page.set_dates_and_check("2026-10-12", "2026-10-14")

    assert page.is_room_type_displayed(room_type_name), f"Phòng '{room_type_name}' không hiển thị trong danh sách kết quả!"

    badge_text = page.get_room_status_badge_text(room_type_id)
    assert badge_text is not None, "Không tìm thấy nhãn trạng thái phòng!"
    assert "Hết phòng" not in badge_text, f"Phòng bị hiển thị 'Hết phòng': {badge_text}"
    assert "Còn" in badge_text or "trống" in badge_text, f"Phòng không ở trạng thái khả dụng: {badge_text}"

    page_content_lower = selenium_driver.page_source.lower()
    assert "overlapping booking" not in page_content_lower, "Giao diện hiển thị lỗi 'Overlapping booking'!"
    assert "room unavailable" not in page_content_lower, "Giao diện hiển thị lỗi 'Room unavailable'!"
    assert "trùng lịch" not in page_content_lower, "Giao diện hiển thị thông báo lỗi trùng lịch!"

    assert page.is_book_button_enabled(room_type_id), "Nút 'Đặt phòng' bị vô hiệu hóa!"
    btn_text = page.get_book_button_text(room_type_id)
    assert "Đã hết" not in btn_text, f"Nút hiển thị trạng thái 'Đã hết': {btn_text}"
    assert "Đặt phòng" in btn_text or "Book Now" in btn_text, f"Text nút không đúng: {btn_text}"

    page.scroll_to_room_card(room_type_name)
    page.take_screenshot("test_room_available_when_booking_on_checkout_date.png")
