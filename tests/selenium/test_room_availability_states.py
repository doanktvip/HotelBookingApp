import sys
import os
import time
import hashlib
from datetime import date, timedelta
from decimal import Decimal
import pytest

# Đảm bảo đường dẫn root dự án có trong sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.models import (
    User, UserRole, Hotel, RoomType, Room, RoomStatus,
    Booking, BookingStatus, BookingDetail
)
from app.utils import get_vn_time
from tests.selenium.pages import HotelDetailPage, AuthPage, MyBookingsPage


@pytest.fixture(scope="function")
def setup_tc5_boundary_checkin(test_app, test_db):
    with test_app.app_context():
        test_db.create_all()
        timestamp = int(time.time() * 1000)

        customer = User(
            username=f"cust_tc5_{timestamp}",
            email=f"cust_tc5_{timestamp}@hotel.com",
            password=hashlib.md5("123456".encode('utf-8')).hexdigest(),
            role=UserRole.CUSTOMER,
            is_verified=True
        )
        test_db.session.add(customer)
        test_db.session.commit()

        hotel = Hotel(
            name=f"Khách sạn TC5 Boundary {timestamp}",
            address="123 Trần Phú",
            location="Nha Trang",
            description="Kiểm thử boundary check-in",
            rating=5.0,
            cancellation_policy_days=3
        )
        test_db.session.add(hotel)
        test_db.session.commit()

        room_type = RoomType(
            hotel_id=hotel.id,
            name=f"Phòng Standard Room A {timestamp}",
            description="Phòng Standard Room A ban công biển",
            base_price=Decimal("1200000.00"),
            max_occupancy=2,
            bed_count=1,
            bed_type="King Bed",
            is_active=True
        )
        test_db.session.add(room_type)
        test_db.session.commit()

        room_a = Room(
            room_type_id=room_type.id,
            room_number="Room-A-101",
            floor=1,
            status=RoomStatus.AVAILABLE,
            is_active=True
        )
        test_db.session.add(room_a)
        test_db.session.commit()

        booking = Booking(
            user_id=customer.id,
            hotel_id=hotel.id,
            room_type_id=room_type.id,
            check_in=date(2026, 10, 10),
            check_out=date(2026, 10, 12),
            total_price=Decimal("2400000.00"),
            status=BookingStatus.CONFIRMED
        )
        test_db.session.add(booking)
        test_db.session.commit()

        detail = BookingDetail(booking_id=booking.id, room_id=room_a.id, price_at_booking=Decimal("1200000.00"))
        test_db.session.add(detail)
        test_db.session.commit()

        data = {
            "hotel_id": hotel.id,
            "room_type_id": room_type.id,
            "room_type_name": room_type.name,
            "room_id": room_a.id,
            "booking_id": booking.id,
            "user_id": customer.id
        }

    yield data

    with test_app.app_context():
        try:
            test_db.session.query(BookingDetail).filter_by(booking_id=data["booking_id"]).delete(synchronize_session=False)
            test_db.session.query(Booking).filter_by(id=data["booking_id"]).delete(synchronize_session=False)
            test_db.session.query(Room).filter_by(id=data["room_id"]).delete(synchronize_session=False)
            test_db.session.query(RoomType).filter_by(id=data["room_type_id"]).delete(synchronize_session=False)
            test_db.session.query(Hotel).filter_by(id=data["hotel_id"]).delete(synchronize_session=False)
            test_db.session.query(User).filter_by(id=data["user_id"]).delete(synchronize_session=False)
            test_db.session.commit()
        except Exception:
            test_db.session.rollback()


@pytest.fixture(scope="function")
def setup_tc6_boundary_checkout(test_app, test_db):
    with test_app.app_context():
        test_db.create_all()
        timestamp = int(time.time() * 1000)

        customer = User(
            username=f"cust_tc6_{timestamp}",
            email=f"cust_tc6_{timestamp}@hotel.com",
            password=hashlib.md5("123456".encode('utf-8')).hexdigest(),
            role=UserRole.CUSTOMER,
            is_verified=True
        )
        test_db.session.add(customer)
        test_db.session.commit()

        hotel = Hotel(
            name=f"Khách sạn TC6 Boundary {timestamp}",
            address="123 Lê Duẩn",
            location="Đà Nẵng",
            description="Kiểm thử boundary check-out",
            rating=5.0,
            cancellation_policy_days=3
        )
        test_db.session.add(hotel)
        test_db.session.commit()

        room_type = RoomType(
            hotel_id=hotel.id,
            name=f"Phòng Deluxe Room A {timestamp}",
            description="Phòng Deluxe Room A view thành phố",
            base_price=Decimal("1500000.00"),
            max_occupancy=2,
            bed_count=1,
            bed_type="Queen Bed",
            is_active=True
        )
        test_db.session.add(room_type)
        test_db.session.commit()

        room_a = Room(
            room_type_id=room_type.id,
            room_number="Room-A-201",
            floor=2,
            status=RoomStatus.AVAILABLE,
            is_active=True
        )
        test_db.session.add(room_a)
        test_db.session.commit()

        booking = Booking(
            user_id=customer.id,
            hotel_id=hotel.id,
            room_type_id=room_type.id,
            check_in=date(2026, 10, 12),
            check_out=date(2026, 10, 14),
            total_price=Decimal("3000000.00"),
            status=BookingStatus.CONFIRMED
        )
        test_db.session.add(booking)
        test_db.session.commit()

        detail = BookingDetail(booking_id=booking.id, room_id=room_a.id, price_at_booking=Decimal("1500000.00"))
        test_db.session.add(detail)
        test_db.session.commit()

        data = {
            "hotel_id": hotel.id,
            "room_type_id": room_type.id,
            "room_type_name": room_type.name,
            "room_id": room_a.id,
            "booking_id": booking.id,
            "user_id": customer.id
        }

    yield data

    with test_app.app_context():
        try:
            test_db.session.query(BookingDetail).filter_by(booking_id=data["booking_id"]).delete(synchronize_session=False)
            test_db.session.query(Booking).filter_by(id=data["booking_id"]).delete(synchronize_session=False)
            test_db.session.query(Room).filter_by(id=data["room_id"]).delete(synchronize_session=False)
            test_db.session.query(RoomType).filter_by(id=data["room_type_id"]).delete(synchronize_session=False)
            test_db.session.query(Hotel).filter_by(id=data["hotel_id"]).delete(synchronize_session=False)
            test_db.session.query(User).filter_by(id=data["user_id"]).delete(synchronize_session=False)
            test_db.session.commit()
        except Exception:
            test_db.session.rollback()


@pytest.fixture(scope="function")
def setup_tc8_today_availability(test_app, test_db):
    with test_app.app_context():
        test_db.create_all()
        timestamp = int(time.time() * 1000)

        hotel = Hotel(
            name=f"Khách sạn TC8 Today {timestamp}",
            address="789 Hoàng Sa",
            location="Đà Nẵng",
            description="Kiểm thử phòng hôm nay",
            rating=5.0,
            cancellation_policy_days=3
        )
        test_db.session.add(hotel)
        test_db.session.commit()

        room_type = RoomType(
            hotel_id=hotel.id,
            name=f"Deluxe Suite {timestamp}",
            description="Loại phòng Deluxe Suite kiểm thử phòng trống hôm nay",
            base_price=Decimal("1800000.00"),
            max_occupancy=2,
            bed_count=1,
            bed_type="King Bed",
            is_active=True
        )
        test_db.session.add(room_type)
        test_db.session.commit()

        room_101 = Room(
            room_type_id=room_type.id,
            room_number="Phòng 101",
            floor=1,
            status=RoomStatus.AVAILABLE,
            is_active=True
        )
        room_102 = Room(
            room_type_id=room_type.id,
            room_number="Phòng 102",
            floor=1,
            status=RoomStatus.BOOKED,
            is_active=True
        )
        room_103 = Room(
            room_type_id=room_type.id,
            room_number="Phòng 103",
            floor=1,
            status=RoomStatus.OCCUPIED,
            is_active=True
        )
        test_db.session.add_all([room_101, room_102, room_103])
        test_db.session.commit()

        data = {
            "hotel_id": hotel.id,
            "room_type_id": room_type.id,
            "room_type_name": room_type.name,
            "room_ids": [room_101.id, room_102.id, room_103.id]
        }

    yield data

    with test_app.app_context():
        try:
            test_db.session.query(Room).filter(Room.id.in_(data["room_ids"])).delete(synchronize_session=False)
            test_db.session.query(RoomType).filter_by(id=data["room_type_id"]).delete(synchronize_session=False)
            test_db.session.query(Hotel).filter_by(id=data["hotel_id"]).delete(synchronize_session=False)
            test_db.session.commit()
        except Exception:
            test_db.session.rollback()


@pytest.fixture(scope="function")
def setup_tc6_cancelled_booking(test_app, test_db):
    with test_app.app_context():
        test_db.create_all()
        timestamp = int(time.time() * 1000)
        today = get_vn_time().date()

        customer = User(
            username=f"cust_cancel_{timestamp}",
            email=f"cust_cancel_{timestamp}@hotel.com",
            phone="0988776655",
            password=hashlib.md5("123456".encode('utf-8')).hexdigest(),
            role=UserRole.CUSTOMER,
            is_verified=True
        )
        test_db.session.add(customer)
        test_db.session.commit()

        hotel = Hotel(
            name=f"Khách sạn Huỷ Đơn {timestamp}",
            address="101 Nguyễn Văn Linh",
            location="Đà Nẵng",
            description="Kiểm thử đơn đã hủy",
            rating=5.0,
            cancellation_policy_days=3
        )
        test_db.session.add(hotel)
        test_db.session.commit()

        room_type = RoomType(
            hotel_id=hotel.id,
            name=f"Phòng Hủy Đơn {timestamp}",
            description="Loại phòng kiểm thử đơn hủy",
            base_price=Decimal("1500000.00"),
            max_occupancy=2,
            bed_count=1,
            bed_type="King Bed",
            is_active=True
        )
        test_db.session.add(room_type)
        test_db.session.commit()

        room = Room(
            room_type_id=room_type.id,
            room_number="Phòng 501",
            floor=5,
            status=RoomStatus.AVAILABLE,
            is_active=True
        )
        test_db.session.add(room)
        test_db.session.commit()

        cancelled_booking = Booking(
            user_id=customer.id,
            hotel_id=hotel.id,
            room_type_id=room_type.id,
            check_in=today + timedelta(days=5),
            check_out=today + timedelta(days=7),
            total_price=Decimal("3000000.00"),
            status=BookingStatus.CANCELLED
        )
        test_db.session.add(cancelled_booking)
        test_db.session.commit()

        detail = BookingDetail(booking_id=cancelled_booking.id, room_id=room.id, price_at_booking=Decimal("1500000.00"))
        test_db.session.add(detail)
        test_db.session.commit()

        data = {
            "customer_username": customer.username,
            "customer_password": "123456",
            "customer_id": customer.id,
            "booking_id": cancelled_booking.id,
            "hotel_id": hotel.id,
            "room_type_id": room_type.id,
            "room_id": room.id
        }

    yield data

    with test_app.app_context():
        try:
            test_db.session.query(BookingDetail).filter_by(booking_id=data["booking_id"]).delete(synchronize_session=False)
            test_db.session.query(Booking).filter_by(id=data["booking_id"]).delete(synchronize_session=False)
            test_db.session.query(Room).filter_by(id=data["room_id"]).delete(synchronize_session=False)
            test_db.session.query(RoomType).filter_by(id=data["room_type_id"]).delete(synchronize_session=False)
            test_db.session.query(Hotel).filter_by(id=data["hotel_id"]).delete(synchronize_session=False)
            test_db.session.query(User).filter_by(id=data["customer_id"]).delete(synchronize_session=False)
            test_db.session.commit()
        except Exception:
            test_db.session.rollback()


def test_tc5_room_available_when_checkin_equals_previous_checkout(live_server, selenium_driver, setup_tc5_boundary_checkin):
    """
    TC5: Ngày check-in của đơn mới trùng với ngày check-out của đơn CONFIRMED trước đó (2026-10-12).
    Sử dụng HotelDetailPage theo chuẩn Page Object Model.
    """
    data = setup_tc5_boundary_checkin
    hotel_page = HotelDetailPage(selenium_driver)
    hotel_page.open_page(live_server.url, data["hotel_id"])
    hotel_page.set_dates_and_check("2026-10-12", "2026-10-14")

    # 1. Assert: Room A xuất hiện trong danh sách kết quả khả dụng
    assert hotel_page.is_room_type_displayed(data["room_type_name"]), f"Phòng '{data['room_type_name']}' không hiển thị!"

    # 2. Assert: Nhãn trạng thái phòng thể hiện phòng khả dụng
    badge_text = hotel_page.get_room_status_badge_text(data["room_type_id"])
    assert badge_text is not None, "Không tìm thấy nhãn trạng thái phòng!"
    assert "Hết phòng" not in badge_text, f"Phòng bị hiển thị 'Hết phòng': {badge_text}"
    assert "Còn" in badge_text and "trống" in badge_text, f"Phòng không ở trạng thái khả dụng: {badge_text}"

    # 3. Assert: Không có thông báo lỗi trùng lịch
    page_text_lower = selenium_driver.page_source.lower()
    assert "overlapping booking" not in page_text_lower
    assert "trùng lịch" not in page_text_lower

    # 4. Assert: Nút Đặt phòng enabled
    assert hotel_page.is_book_button_enabled(data["room_type_id"]), "Nút 'Đặt phòng' bị vô hiệu hóa!"

    hotel_page.scroll_to_room_card(data["room_type_name"])
    hotel_page.take_screenshot("tc5_room_available_when_checkin_equals_previous_checkout.png")


def test_tc6_room_available_when_checkout_equals_next_checkin(live_server, selenium_driver, setup_tc6_boundary_checkout):
    """
    TC6: Ngày check-out của đơn mới trùng với ngày check-in của đơn CONFIRMED kế tiếp (2026-10-12).
    Sử dụng HotelDetailPage theo chuẩn Page Object Model.
    """
    data = setup_tc6_boundary_checkout
    hotel_page = HotelDetailPage(selenium_driver)
    hotel_page.open_page(live_server.url, data["hotel_id"])
    hotel_page.set_dates_and_check("2026-10-10", "2026-10-12")

    # 1. Assert: Room A hiển thị trong danh sách kết quả khả dụng
    assert hotel_page.is_room_type_displayed(data["room_type_name"]), f"Phòng '{data['room_type_name']}' không hiển thị!"

    # 2. Assert: Nhãn trạng thái phòng thể hiện phòng khả dụng
    badge_text = hotel_page.get_room_status_badge_text(data["room_type_id"])
    assert badge_text is not None, "Không tìm thấy nhãn trạng thái phòng!"
    assert "Hết phòng" not in badge_text, f"Phòng bị hiển thị 'Hết phòng': {badge_text}"
    assert "Còn" in badge_text and "trống" in badge_text, f"Phòng không ở trạng thái khả dụng: {badge_text}"

    # 3. Assert: Không xuất hiện thông báo lỗi trùng lịch
    page_text_lower = selenium_driver.page_source.lower()
    assert "overlapping booking" not in page_text_lower
    assert "trùng lịch" not in page_text_lower

    # 4. Assert: Nút 'Đặt phòng' ở trạng thái enabled
    assert hotel_page.is_book_button_enabled(data["room_type_id"]), "Nút 'Đặt phòng' bị vô hiệu hóa!"

    hotel_page.scroll_to_room_card(data["room_type_name"])
    hotel_page.take_screenshot("tc6_room_available_when_checkout_equals_next_checkin.png")


def test_tc8_only_available_status_rooms_counted_for_today_checkin(live_server, selenium_driver, setup_tc8_today_availability):
    """
    TC8: Chỉ tính phòng có trạng thái vật lý AVAILABLE khi check-in hôm nay.
    Sử dụng HotelDetailPage theo chuẩn Page Object Model.
    """
    data = setup_tc8_today_availability
    hotel_page = HotelDetailPage(selenium_driver)
    hotel_page.open_page(live_server.url, data["hotel_id"])

    today = get_vn_time().date()
    tomorrow = today + timedelta(days=1)
    hotel_page.set_dates_and_check(today.strftime("%Y-%m-%d"), tomorrow.strftime("%Y-%m-%d"))

    # 1. Assert: Loại phòng hiển thị
    assert hotel_page.is_room_type_displayed(data["room_type_name"]), f"Loại phòng '{data['room_type_name']}' không hiển thị!"

    # 2. Assert: Số lượng phòng trống hiển thị chỉ bằng 1
    badge_text = hotel_page.get_room_status_badge_text(data["room_type_id"])
    assert badge_text == "Còn 1 trống", f"Số lượng phòng trống không phải là 1! Thực tế: '{badge_text}'"

    # 3. Assert: Nút đặt phòng enabled
    assert hotel_page.is_book_button_enabled(data["room_type_id"]), "Nút 'Đặt phòng' bị vô hiệu hóa!"

    hotel_page.scroll_to_room_card(data["room_type_name"])
    hotel_page.take_screenshot("tc8_only_available_status_rooms_counted_for_today.png")


def test_tc6_cancelled_booking_cannot_perform_further_actions(live_server, selenium_driver, setup_tc6_cancelled_booking):
    """
    TC6 (Cancelled Booking): Đơn CANCELLED ('Đã hủy') bị khóa mọi thao tác.
    Sử dụng AuthPage và MyBookingsPage theo chuẩn Page Object Model.
    """
    data = setup_tc6_cancelled_booking

    # Đăng nhập bằng AuthPage
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(data["customer_username"], data["customer_password"])

    # Điều hướng tới MyBookingsPage
    my_bookings = MyBookingsPage(selenium_driver)
    my_bookings.open_page(live_server.url)

    # Tìm thẻ đơn đặt phòng
    card = my_bookings.get_booking_card(data["booking_id"])
    assert card is not None, "Không tìm thấy thẻ đơn đặt phòng đã hủy!"
    my_bookings.scroll_to_card(card)

    # 1. Assert: Trạng thái hiển thị 'Đã hủy' hoặc 'CANCELLED'
    status_text = my_bookings.get_status_badge_text(card)
    assert "Đã hủy" in status_text or "CANCELLED" in status_text, f"Trạng thái không phải 'Đã hủy': '{status_text}'"

    # 2. Assert: Nút 'Hủy đặt phòng' không hiển thị
    assert not my_bookings.is_cancel_button_visible(card), "Nút 'Hủy đặt phòng' vẫn hiển thị đối với đơn đã hủy!"

    # 3. Assert: Nút 'Thanh toán' không hiển thị
    assert not my_bookings.is_pay_button_visible(card), "Nút 'Thanh toán' vẫn hiển thị đối với đơn đã hủy!"

    my_bookings.take_screenshot("tc6_cancelled_booking_cannot_perform_further_actions.png")
