import sys
import os
import hashlib
from datetime import date
from decimal import Decimal
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.models import (
    User, UserRole, Hotel, RoomType, Room, RoomStatus,
    Booking, BookingStatus, BookingDetail
)
from tests.selenium.pages import HotelDetailPage


@pytest.fixture(scope="function")
def setup_room_a_confirmed_booking(test_app, test_db):
    """
    Bước 1 (Precondition):
    Thiết lập một booking CONFIRMED cho Room A từ 2026-10-10 đến 2026-10-12 qua Direct DB.
    Kèm Teardown tự động xóa booking mẫu sau khi chạy xong để bảo đảm tính độc lập.
    """
    with test_app.app_context():
        test_db.create_all()

        # 1. Khách hàng mẫu
        customer = test_db.session.query(User).filter_by(username="test_customer_room_a").first()
        if not customer:
            customer = User(
                username="test_customer_room_a",
                email="test_customer_room_a@hotel.com",
                password=hashlib.md5("123456".encode('utf-8')).hexdigest(),
                role=UserRole.CUSTOMER,
                is_verified=True
            )
            test_db.session.add(customer)
            test_db.session.commit()

        # 2. Khách sạn mẫu
        hotel = test_db.session.query(Hotel).filter_by(name="Khách sạn Kiểm thử Room A").first()
        if not hotel:
            hotel = Hotel(
                name="Khách sạn Kiểm thử Room A",
                address="456 Trần Phú",
                location="Nha Trang",
                description="Khách sạn phục vụ kiểm thử tự động phòng",
                rating=5.0,
                cancellation_policy_days=3
            )
            test_db.session.add(hotel)
            test_db.session.commit()

        # 3. Loại phòng: "Room A"
        room_type = test_db.session.query(RoomType).filter_by(hotel_id=hotel.id, name="Room A").first()
        if not room_type:
            room_type = RoomType(
                hotel=hotel,
                name="Room A",
                description="Phòng Deluxe Room A cao cấp, ban công hướng biển",
                base_price=Decimal("1200000.00"),
                max_occupancy=2,
                bed_count=1,
                bed_type="Giường đôi cực lớn",
                is_active=True
            )
            test_db.session.add(room_type)
            test_db.session.commit()

        # 4. Phòng vật lý thuộc Room A (duy nhất 1 phòng để test tính khả dụng chặt chẽ)
        room = test_db.session.query(Room).filter_by(room_type_id=room_type.id, room_number="Room-A-101").first()
        if not room:
            room = Room(
                room_type=room_type,
                room_number="Room-A-101",
                floor=1,
                status=RoomStatus.AVAILABLE,
                is_active=True
            )
            test_db.session.add(room)
            test_db.session.commit()

        # 5. Thiết lập Booking CONFIRMED từ 2026-10-10 đến 2026-10-12
        confirmed_booking = Booking(
            customer=customer,
            hotel=hotel,
            room_type=room_type,
            check_in=date(2026, 10, 10),
            check_out=date(2026, 10, 12),
            total_price=Decimal("2400000.00"),
            status=BookingStatus.CONFIRMED
        )
        test_db.session.add(confirmed_booking)
        test_db.session.commit()

        detail = BookingDetail(
            booking_id=confirmed_booking.id,
            room_id=room.id,
            price_at_booking=room_type.base_price
        )
        test_db.session.add(detail)
        test_db.session.commit()

        booking_id = confirmed_booking.id
        room_type_id = room_type.id
        room_type_name = room_type.name
        hotel_id = hotel.id

        data = {
            "hotel_id": hotel_id,
            "room_type_id": room_type_id,
            "room_type_name": room_type_name,
            "booking_id": booking_id
        }

    yield data

    # Xử lý Teardown: Xóa booking mẫu sau khi chạy xong để bảo đảm tính độc lập
    with test_app.app_context():
        try:
            b = test_db.session.get(Booking, booking_id) if hasattr(test_db.session, 'get') else test_db.session.query(Booking).get(booking_id)
            if b:
                test_db.session.query(BookingDetail).filter_by(booking_id=booking_id).delete()
                test_db.session.delete(b)
                test_db.session.commit()
        except Exception:
            test_db.session.rollback()


def test_room_available_when_booking_on_checkout_date(
    live_server, selenium_driver, test_db, setup_room_a_confirmed_booking
):
    """
    Test Case: test_room_available_when_booking_on_checkout_date
    Kiểm tra phòng (Room A) hiển thị khả dụng khi tìm kiếm đặt phòng vào đúng ngày check-out
    của một đơn CONFIRMED trước đó (đơn cũ: 2026-10-10 -> 2026-10-12, tìm mới: 2026-10-12 -> 2026-10-14).
    Sử dụng Page Object Model HotelDetailPage.
    """
    room_type_id = setup_room_a_confirmed_booking["room_type_id"]
    room_type_name = setup_room_a_confirmed_booking["room_type_name"]
    hotel_id = setup_room_a_confirmed_booking["hotel_id"]

    page = HotelDetailPage(selenium_driver)
    page.open_page(live_server.url, hotel_id)

    # Điền Check-in: 2026-10-12, Check-out: 2026-10-14, bấm Tìm kiếm
    page.set_dates_and_check("2026-10-12", "2026-10-14")

    # Assertion 1: Room A xuất hiện trong danh sách kết quả khả dụng
    assert page.is_room_type_displayed(room_type_name), f"Phòng '{room_type_name}' không hiển thị trong danh sách kết quả!"

    # Assertion 2: Nhãn trạng thái phòng thể hiện phòng còn trống, không phải 'Hết phòng'
    badge_text = page.get_room_status_badge_text(room_type_id)
    assert badge_text is not None, "Không tìm thấy nhãn trạng thái phòng của Room A!"
    assert "Hết phòng" not in badge_text, f"Room A bị hiển thị 'Hết phòng': {badge_text}"
    assert "Còn" in badge_text or "trống" in badge_text, f"Room A không ở trạng thái khả dụng: {badge_text}"

    # Assertion 3: Không xuất hiện thông báo lỗi trùng lịch
    page_content_lower = selenium_driver.page_source.lower()
    assert "overlapping booking" not in page_content_lower, "Giao diện hiển thị lỗi 'Overlapping booking'!"
    assert "room unavailable" not in page_content_lower, "Giao diện hiển thị lỗi 'Room unavailable'!"
    assert "trùng lịch" not in page_content_lower, "Giao diện hiển thị thông báo lỗi trùng lịch!"

    # Assertion 4: Nút Đặt phòng của Room A ở trạng thái enabled
    assert page.is_book_button_enabled(room_type_id), "Nút 'Đặt phòng' bị vô hiệu hóa!"
    btn_text = page.get_book_button_text(room_type_id)
    assert "Đã hết" not in btn_text, f"Nút hiển thị trạng thái 'Đã hết': {btn_text}"
    assert "Đặt phòng" in btn_text or "Book Now" in btn_text, f"Text nút không đúng: {btn_text}"

    # Cuộn tới phòng và chụp ảnh minh chứng
    page.scroll_to_room_card(room_type_name)
    page.take_screenshot("test_room_available_when_booking_on_checkout_date.png")
