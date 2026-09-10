import sys
import os
import time
import hashlib
from datetime import timedelta
from decimal import Decimal
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.models import (
    User, UserRole, Hotel, RoomType, Room, RoomStatus,
    Booking, BookingStatus, BookingDetail, Payment, PaymentMethod, PaymentStatus
)
from app.utils import get_vn_time
from tests.selenium.pages import AuthPage, ManageBookingsPage


@pytest.fixture(scope="function")
def seed_checkin_checkout_data(test_app, test_db):
    with test_app.app_context():
        test_db.create_all()

        timestamp = int(time.time() * 1000)

        # 1. Tạo Khách sạn mẫu
        hotel = Hotel(
            name=f"Khách sạn Test CI/CO {timestamp}",
            address="123 Đường Test CI/CO",
            location="Đà Nẵng",
            description="Phục vụ kiểm thử Check-in và Check-out",
            rating=5.0,
            cancellation_policy_days=3
        )
        test_db.session.add(hotel)
        test_db.session.commit()
        hotel_id = hotel.id

        # 2. Tạo tài khoản Lễ tân & Khách hàng
        hashed_pw = hashlib.md5("123456".encode('utf-8')).hexdigest()
        receptionist = User(
            username=f"recept_{timestamp}",
            email=f"recept_{timestamp}@hotel.com",
            password=hashed_pw,
            role=UserRole.RECEPTIONIST,
            is_verified=True,
            hotel_id=hotel_id
        )
        customer = User(
            username=f"cust_{timestamp}",
            email=f"cust_{timestamp}@hotel.com",
            phone="0911223344",
            password=hashed_pw,
            role=UserRole.CUSTOMER,
            is_verified=True
        )
        test_db.session.add_all([receptionist, customer])
        test_db.session.commit()

        # 3. Tạo Loại phòng mẫu
        room_type = RoomType(
            hotel_id=hotel_id,
            name=f"Phòng Deluxe CI/CO {timestamp}",
            description="Loại phòng kiểm thử",
            base_price=Decimal("1000000.00"),
            max_occupancy=2,
            bed_count=1,
            bed_type="King Bed",
            is_active=True
        )
        test_db.session.add(room_type)
        test_db.session.commit()
        room_type_id = room_type.id

        # 4. Tạo các phòng vật lý (Bao gồm Room-101 gắn với BK_IN_USE)
        room_101 = Room(
            room_type_id=room_type_id,
            room_number="Room-101",
            floor=1,
            status=RoomStatus.OCCUPIED,
            is_active=True
        )
        room_102 = Room(
            room_type_id=room_type_id,
            room_number="Room-102",
            floor=1,
            status=RoomStatus.AVAILABLE,
            is_active=True
        )
        room_103 = Room(
            room_type_id=room_type_id,
            room_number="Room-103",
            floor=1,
            status=RoomStatus.OCCUPIED,
            is_active=True
        )
        test_db.session.add_all([room_101, room_102, room_103])
        test_db.session.commit()

        today = get_vn_time().date()

        # 5. Khởi tạo 4 đơn tương ứng 4 kịch bản
        # BK_IN_USE: "Đang sử dụng", gắn Room-101 (OCCUPIED), đã thanh toán đủ
        bk_in_use = Booking(
            user_id=customer.id,
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            check_in=today - timedelta(days=1),
            check_out=today + timedelta(days=1),
            total_price=Decimal("2000000.00"),
            status=BookingStatus.CONFIRMED
        )
        test_db.session.add(bk_in_use)
        test_db.session.commit()
        bd_in_use = BookingDetail(booking_id=bk_in_use.id, room_id=room_101.id, price_at_booking=Decimal("1000000.00"))
        pm_in_use = Payment(
            booking_id=bk_in_use.id,
            amount=Decimal("2000000.00"),
            payment_method=PaymentMethod.MOMO,
            status=PaymentStatus.SUCCESS,
            transaction_id=f"TRANS_USE_{bk_in_use.id}"
        )
        test_db.session.add_all([bd_in_use, pm_in_use])

        # BK_CONFIRMED: "Đã đặt", gắn Room-102 (AVAILABLE), chưa check-in
        bk_confirmed = Booking(
            user_id=customer.id,
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            check_in=today,
            check_out=today + timedelta(days=2),
            total_price=Decimal("2000000.00"),
            status=BookingStatus.CONFIRMED
        )
        test_db.session.add(bk_confirmed)
        test_db.session.commit()
        bd_confirmed = BookingDetail(booking_id=bk_confirmed.id, room_id=room_102.id, price_at_booking=Decimal("1000000.00"))
        pm_confirmed = Payment(
            booking_id=bk_confirmed.id,
            amount=Decimal("2000000.00"),
            payment_method=PaymentMethod.MOMO,
            status=PaymentStatus.SUCCESS,
            transaction_id=f"TRANS_CONF_{bk_confirmed.id}"
        )
        test_db.session.add_all([bd_confirmed, pm_confirmed])

        # BK_CANCELLED: "Đã hủy"
        bk_cancelled = Booking(
            user_id=customer.id,
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            check_in=today,
            check_out=today + timedelta(days=2),
            total_price=Decimal("2000000.00"),
            status=BookingStatus.CANCELLED
        )
        test_db.session.add(bk_cancelled)

        # BK_CHECKOUT_UNPAID: "Đang sử dụng", gắn Room-103 (OCCUPIED), còn nợ tiền chưa thanh toán
        bk_unpaid = Booking(
            user_id=customer.id,
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            check_in=today - timedelta(days=2),
            check_out=today + timedelta(days=1),
            total_price=Decimal("3000000.00"),
            status=BookingStatus.CONFIRMED
        )
        test_db.session.add(bk_unpaid)
        test_db.session.commit()
        bd_unpaid = BookingDetail(booking_id=bk_unpaid.id, room_id=room_103.id, price_at_booking=Decimal("1000000.00"))
        pm_unpaid = Payment(
            booking_id=bk_unpaid.id,
            amount=Decimal("1000000.00"),
            payment_method=PaymentMethod.MOMO,
            status=PaymentStatus.PENDING,
            transaction_id=f"TRANS_UNP_{bk_unpaid.id}"
        )
        test_db.session.add_all([bd_unpaid, pm_unpaid])
        test_db.session.commit()

        seed_data = {
            "hotel_id": hotel_id,
            "receptionist_username": receptionist.username,
            "receptionist_password": "123456",
            "room_101_id": room_101.id,
            "room_102_id": room_102.id,
            "room_103_id": room_103.id,
            "bk_in_use_id": bk_in_use.id,
            "bk_confirmed_id": bk_confirmed.id,
            "bk_cancelled_id": bk_cancelled.id,
            "bk_unpaid_id": bk_unpaid.id,
            "booking_ids": [bk_in_use.id, bk_confirmed.id, bk_cancelled.id, bk_unpaid.id],
            "room_ids": [room_101.id, room_102.id, room_103.id],
            "room_type_id": room_type_id,
            "user_ids": [receptionist.id, customer.id]
        }

    yield seed_data

    # Teardown dọn dẹp Direct DB sau mỗi test function
    with test_app.app_context():
        try:
            b_ids = seed_data["booking_ids"]
            test_db.session.query(Payment).filter(Payment.booking_id.in_(b_ids)).delete(synchronize_session=False)
            test_db.session.query(BookingDetail).filter(BookingDetail.booking_id.in_(b_ids)).delete(synchronize_session=False)
            test_db.session.query(Booking).filter(Booking.id.in_(b_ids)).delete(synchronize_session=False)
            test_db.session.query(Room).filter(Room.id.in_(seed_data["room_ids"])).delete(synchronize_session=False)
            test_db.session.query(RoomType).filter(RoomType.id == seed_data["room_type_id"]).delete(synchronize_session=False)
            test_db.session.query(User).filter(User.id.in_(seed_data["user_ids"])).delete(synchronize_session=False)
            test_db.session.query(Hotel).filter(Hotel.id == seed_data["hotel_id"]).delete(synchronize_session=False)
            test_db.session.commit()
        except Exception:
            test_db.session.rollback()


def test_tc15_cannot_checkin_non_confirmed_booking(live_server, selenium_driver, seed_checkin_checkout_data):
    """
    TC15: Không thể Check-in đơn không ở trạng thái 'Đã đặt' (đơn đang sử dụng / CHECKED_IN).
    """
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(
        seed_checkin_checkout_data["receptionist_username"],
        seed_checkin_checkout_data["receptionist_password"]
    )

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)

    row = manage_page.get_booking_row_by_id(seed_checkin_checkout_data["bk_in_use_id"])
    assert "Đang sử dụng" in manage_page.get_row_status_text(row)
    assert not manage_page.has_checkin_button(row), \
        "Nút Check-in vẫn xuất hiện hoặc đang khả dụng cho đơn đã nhận phòng (Đang sử dụng)!"

    manage_page.take_screenshot("reception_tc15_cannot_checkin_non_confirmed.png")


def test_tc16_cannot_checkin_cancelled_booking(live_server, selenium_driver, seed_checkin_checkout_data):
    """
    TC16: Chặn hoàn toàn thao tác nhận phòng đối với đơn đã bị hủy (CANCELLED).
    """
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(
        seed_checkin_checkout_data["receptionist_username"],
        seed_checkin_checkout_data["receptionist_password"]
    )

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)

    row = manage_page.get_booking_row_by_id(seed_checkin_checkout_data["bk_cancelled_id"])
    assert "Đã hủy" in manage_page.get_row_status_text(row)
    assert not manage_page.has_checkin_button(row), \
        "Nút Check-in vẫn xuất hiện cho đơn đã bị hủy (CANCELLED)!"

    manage_page.take_screenshot("reception_tc16_cannot_checkin_cancelled.png")


def test_tc18_booking_status_completed_after_successful_checkout(live_server, selenium_driver, test_app, test_db, seed_checkin_checkout_data):
    """
    TC18: Check-out thành công chuyển trạng thái đơn sang 'Hoàn thành' (COMPLETED)
    và giải phóng phòng Room-101 về trạng thái AVAILABLE.
    """
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(
        seed_checkin_checkout_data["receptionist_username"],
        seed_checkin_checkout_data["receptionist_password"]
    )

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)

    manage_page.click_checkout(seed_checkin_checkout_data["bk_in_use_id"])
    manage_page.confirm_checkout()

    manage_page.open_page(live_server.url)

    row = manage_page.get_booking_row_by_id(seed_checkin_checkout_data["bk_in_use_id"])
    status_text = manage_page.get_row_status_text(row)
    assert any(s in status_text for s in ["Hoàn thành", "Đã hoàn tất", "COMPLETED"]), \
        f"Trạng thái hiển thị trên giao diện chưa đổi thành Hoàn tất! Thực tế: {status_text}"

    manage_page.take_screenshot("reception_tc18_checkout_success_completed.png")

    with test_app.app_context():
        test_db.session.expire_all()
        room = test_db.session.get(Room, seed_checkin_checkout_data["room_101_id"])
        booking = test_db.session.get(Booking, seed_checkin_checkout_data["bk_in_use_id"])
        assert room.status == RoomStatus.AVAILABLE, f"Phòng Room-101 chưa được giải phóng về AVAILABLE! Thực tế: {room.status}"
        assert booking.status == BookingStatus.COMPLETED, f"Trạng thái đơn trong DB chưa là COMPLETED! Thực tế: {booking.status}"


def test_tc19_cannot_checkout_non_checked_in_booking(live_server, selenium_driver, seed_checkin_checkout_data):
    """
    TC19: Không thể thực hiện trả phòng khi khách chưa check-in (đơn ở trạng thái CONFIRMED).
    """
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(
        seed_checkin_checkout_data["receptionist_username"],
        seed_checkin_checkout_data["receptionist_password"]
    )

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)

    row = manage_page.get_booking_row_by_id(seed_checkin_checkout_data["bk_confirmed_id"])
    assert "Đang sử dụng" not in manage_page.get_row_status_text(row)
    assert not manage_page.has_checkout_button(row), \
        "Nút Check-out vẫn xuất hiện hoặc đang khả dụng cho đơn chưa nhận phòng (CONFIRMED)!"

    manage_page.take_screenshot("reception_tc19_cannot_checkout_non_checked_in.png")


def test_tc20_cannot_checkout_when_payment_incomplete(live_server, selenium_driver, test_app, test_db, seed_checkin_checkout_data):
    """
    TC20: Hệ thống hiển thị cảnh báo yêu cầu thanh toán đầy đủ trước khi trả phòng;
    đơn giữ nguyên trạng thái 'Đang sử dụng' (CHECKED_IN).
    """
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(
        seed_checkin_checkout_data["receptionist_username"],
        seed_checkin_checkout_data["receptionist_password"]
    )

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)

    manage_page.click_checkout(seed_checkin_checkout_data["bk_unpaid_id"])
    details = manage_page.get_checkout_modal_details()
    assert details["balance"] != "0 đ", "Số dư cần thanh toán phải lớn hơn 0 đối với đơn chưa trả đủ tiền!"
    assert details["is_confirm_disabled"] or details["alert_displayed"], \
        "Hệ thống không chặn hoặc cảnh báo khi đơn còn khoản nợ chưa thanh toán!"

    manage_page.take_screenshot("reception_tc20_checkout_unpaid_warning.png")

    manage_page.close_checkout_modal()

    row = manage_page.get_booking_row_by_id(seed_checkin_checkout_data["bk_unpaid_id"])
    assert "Đang sử dụng" in manage_page.get_row_status_text(row)

    with test_app.app_context():
        test_db.session.expire_all()
        booking = test_db.session.get(Booking, seed_checkin_checkout_data["bk_unpaid_id"])
        assert booking.status == BookingStatus.CONFIRMED, "Trạng thái đơn bị thay đổi dù chưa thanh toán đủ!"


def test_tc21_cancel_checkout_modal_action(live_server, selenium_driver, test_app, test_db, seed_checkin_checkout_data):
    """
    TC21: Hủy hoặc đóng modal thanh toán: modal đóng, trạng thái đơn giữ nguyên 'Đang sử dụng',
    phòng Room-101 vẫn giữ nguyên OCCUPIED.
    """
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(
        seed_checkin_checkout_data["receptionist_username"],
        seed_checkin_checkout_data["receptionist_password"]
    )

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)

    manage_page.click_checkout(seed_checkin_checkout_data["bk_in_use_id"])
    manage_page.close_checkout_modal()

    row = manage_page.get_booking_row_by_id(seed_checkin_checkout_data["bk_in_use_id"])
    assert "Đang sử dụng" in manage_page.get_row_status_text(row)

    manage_page.take_screenshot("reception_tc21_cancel_checkout_modal.png")

    with test_app.app_context():
        test_db.session.expire_all()
        room = test_db.session.get(Room, seed_checkin_checkout_data["room_101_id"])
        booking = test_db.session.get(Booking, seed_checkin_checkout_data["bk_in_use_id"])
        assert room.status == RoomStatus.OCCUPIED, f"Phòng Room-101 bị đổi trạng thái trái phép! Thực tế: {room.status}"
        assert booking.status == BookingStatus.CONFIRMED, f"Đơn bị đổi trạng thái dù đã hủy modal! Thực tế: {booking.status}"
