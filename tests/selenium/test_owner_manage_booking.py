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
    User, UserRole, Hotel, RoomType, Floor, Room, RoomStatus,
    Booking, BookingStatus, BookingDetail
)
from app.utils import get_vn_time
from tests.selenium.pages import AuthPage, ManageBookingsPage


@pytest.fixture(scope="function")
def setup_tc4_hotel_owner_booking_data(test_app, test_db):
    """
    Direct DB Fixture khởi tạo dữ liệu cho TC4:
    - 1 Khách sạn: 'Khách sạn Biển Xanh Premium'
    - 1 Tài khoản Chủ khách sạn (role=ADMIN, hotel_id=hotel.id)
    - 2 Khách hàng (Nguyễn Thị Mai, Trần Văn Bình)
    - 2 Loại phòng & Phòng vật lý (Deluxe Hướng Biển P301, Suite Gia Đình P302)
    - 2 Đơn đặt phòng với đầy đủ thông tin: tên khách, SĐT, loại phòng, số phòng, ngày đến/đi, trạng thái
    - Teardown dọn dẹp dữ liệu sạch sẽ sau khi test hoàn thành.
    """
    with test_app.app_context():
        test_db.create_all()
        timestamp = int(time.time() * 1000)
        hashed_pw = hashlib.md5("123456".encode('utf-8')).hexdigest()

        # 1. Khách sạn
        hotel = Hotel(
            name=f"Khách sạn Biển Xanh Premium {timestamp}",
            address="456 Đường Võ Nguyên Giáp",
            location="Đà Nẵng",
            description="Khách sạn 5 sao mặt biển",
            rating=5.0,
            cancellation_policy_days=3
        )
        test_db.session.add(hotel)
        test_db.session.commit()

        # 2. Tầng
        floor_3 = Floor(
            hotel_id=hotel.id,
            floor_number=3,
            name="Tầng 3"
        )
        test_db.session.add(floor_3)
        test_db.session.commit()

        # 3. Tài khoản Chủ khách sạn
        owner_username = f"owner_tc4_{timestamp}"
        owner = User(
            username=owner_username,
            email=f"owner_{timestamp}@hotel.com",
            phone="0909123456",
            password=hashed_pw,
            role=UserRole.ADMIN,
            hotel_id=hotel.id,
            is_verified=True
        )
        test_db.session.add(owner)

        # 4. Khách hàng 1: Nguyễn Thị Mai
        cust1 = User(
            username=f"Nguyễn Thị Mai {timestamp}",
            email=f"mai_{timestamp}@gmail.com",
            phone="0912345678",
            password=hashed_pw,
            role=UserRole.CUSTOMER,
            is_verified=True
        )
        # Khách hàng 2: Trần Văn Bình
        cust2 = User(
            username=f"Trần Văn Bình {timestamp}",
            email=f"binh_{timestamp}@gmail.com",
            phone="0987654321",
            password=hashed_pw,
            role=UserRole.CUSTOMER,
            is_verified=True
        )
        test_db.session.add_all([cust1, cust2])
        test_db.session.commit()

        # 5. Loại phòng 1: Phòng Deluxe Hướng Biển
        rt_deluxe = RoomType(
            hotel_id=hotel.id,
            name=f"Deluxe Hướng Biển {timestamp}",
            description="Phòng Deluxe view trực diện biển",
            base_price=Decimal("1500000.00"),
            max_occupancy=2,
            bed_count=1,
            bed_type="King Bed",
            is_active=True
        )
        # Loại phòng 2: Suite Gia Đình
        rt_suite = RoomType(
            hotel_id=hotel.id,
            name=f"Suite Gia Đình {timestamp}",
            description="Phòng Suite rộng rãi cho cả gia đình",
            base_price=Decimal("2500000.00"),
            max_occupancy=4,
            bed_count=2,
            bed_type="2 Queen Beds",
            is_active=True
        )
        test_db.session.add_all([rt_deluxe, rt_suite])
        test_db.session.commit()

        # 6. Phòng vật lý
        room_p301 = Room(
            room_type_id=rt_deluxe.id,
            room_number="P301",
            floor=3,
            floor_id=floor_3.id,
            status=RoomStatus.AVAILABLE,
            is_active=True
        )
        room_p302 = Room(
            room_type_id=rt_suite.id,
            room_number="P302",
            floor=3,
            floor_id=floor_3.id,
            status=RoomStatus.OCCUPIED,
            is_active=True
        )
        test_db.session.add_all([room_p301, room_p302])
        test_db.session.commit()

        # 7. Đơn đặt phòng 1: Nguyễn Thị Mai - Phòng P301 - Đã đặt (CONFIRMED)
        check_in_1 = date(2026, 9, 15)
        check_out_1 = date(2026, 9, 18)
        booking1 = Booking(
            user_id=cust1.id,
            hotel_id=hotel.id,
            room_type_id=rt_deluxe.id,
            check_in=check_in_1,
            check_out=check_out_1,
            total_price=Decimal("4500000.00"),
            status=BookingStatus.CONFIRMED
        )
        # Đơn đặt phòng 2: Trần Văn Bình - Phòng P302 - Đang sử dụng (OCCUPIED / Stay today)
        today = get_vn_time().date()
        booking2 = Booking(
            user_id=cust2.id,
            hotel_id=hotel.id,
            room_type_id=rt_suite.id,
            check_in=today - timedelta(days=1),
            check_out=today + timedelta(days=2),
            total_price=Decimal("7500000.00"),
            status=BookingStatus.CONFIRMED
        )
        test_db.session.add_all([booking1, booking2])
        test_db.session.commit()

        # Chi tiết đặt phòng
        bd1 = BookingDetail(booking_id=booking1.id, room_id=room_p301.id, price_at_booking=rt_deluxe.base_price)
        bd2 = BookingDetail(booking_id=booking2.id, room_id=room_p302.id, price_at_booking=rt_suite.base_price)
        test_db.session.add_all([bd1, bd2])
        test_db.session.commit()

        data = {
            "owner_username": owner_username,
            "owner_password": "123456",
            "owner_id": owner.id,
            "hotel_id": hotel.id,
            "floor_id": floor_3.id,
            "user_ids": [owner.id, cust1.id, cust2.id],
            "room_type_ids": [rt_deluxe.id, rt_suite.id],
            "room_ids": [room_p301.id, room_p302.id],
            "booking_ids": [booking1.id, booking2.id],
            "booking1": {
                "id": booking1.id,
                "code": f"BK{booking1.id:03d}",
                "customer_name": cust1.username,
                "phone": cust1.phone,
                "room_type": rt_deluxe.name,
                "room_number": room_p301.room_number,
                "check_in": check_in_1.strftime('%d/%m/%Y'),
                "check_out": check_out_1.strftime('%d/%m/%Y'),
                "status_text": "Đã đặt"
            },
            "booking2": {
                "id": booking2.id,
                "code": f"BK{booking2.id:03d}",
                "customer_name": cust2.username,
                "phone": cust2.phone,
                "room_type": rt_suite.name,
                "room_number": room_p302.room_number,
                "check_in": (today - timedelta(days=1)).strftime('%d/%m/%Y'),
                "check_out": (today + timedelta(days=2)).strftime('%d/%m/%Y'),
                "status_text": "Đang sử dụng"
            }
        }

    yield data

    # Teardown: Dọn dẹp cơ sở dữ liệu sau khi chạy test
    with test_app.app_context():
        try:
            test_db.session.query(BookingDetail).filter(BookingDetail.booking_id.in_(data["booking_ids"])).delete(synchronize_session=False)
            test_db.session.query(Booking).filter(Booking.id.in_(data["booking_ids"])).delete(synchronize_session=False)
            test_db.session.query(Room).filter(Room.id.in_(data["room_ids"])).delete(synchronize_session=False)
            test_db.session.query(RoomType).filter(RoomType.id.in_(data["room_type_ids"])).delete(synchronize_session=False)
            test_db.session.query(Floor).filter_by(id=data["floor_id"]).delete(synchronize_session=False)
            test_db.session.query(Hotel).filter_by(id=data["hotel_id"]).delete(synchronize_session=False)
            test_db.session.query(User).filter(User.id.in_(data["user_ids"])).delete(synchronize_session=False)
            test_db.session.commit()
        except Exception:
            test_db.session.rollback()


def test_tc4_hotel_owner_views_booking_list(live_server, selenium_driver, setup_tc4_hotel_owner_booking_data):
    data = setup_tc4_hotel_owner_booking_data
    owner_user = data["owner_username"]
    owner_pass = data["owner_password"]
    b1_info = data["booking1"]
    b2_info = data["booking2"]

    # 1. Đăng nhập qua AuthPage
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(owner_user, owner_pass)
    assert auth_page.is_logged_in_as(owner_user), "Đăng nhập Chủ khách sạn không thành công!"

    # 2. Điều hướng tới Quản lý đơn đặt phòng qua ManageBookingsPage
    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.click_manage_booking_nav()

    # Chờ danh sách đơn xuất hiện
    rows = manage_page.get_booking_rows()
    assert len(rows) >= 2, "Danh sách đơn đặt phòng không hiển thị đầy đủ!"

    # 3. Assert thông tin Đơn 1 (Nguyễn Thị Mai)
    row_b1 = manage_page.get_booking_row_by_code(b1_info["code"])
    data_1 = manage_page.get_row_data(row_b1)

    assert b1_info["customer_name"] in data_1["customer_name"], f"Tên khách sai! Kì vọng: '{b1_info['customer_name']}', Thực tế: '{data_1['customer_name']}'"
    assert b1_info["phone"] in data_1["phone"], f"SĐT sai! Kì vọng: '{b1_info['phone']}', Thực tế: '{data_1['phone']}'"
    assert b1_info["room_type"] in data_1["room_type"], f"Loại phòng sai! Kì vọng: '{b1_info['room_type']}', Thực tế: '{data_1['room_type']}'"
    assert b1_info["room_number"] in data_1["room_number"], f"Số phòng sai! Kì vọng: '{b1_info['room_number']}', Thực tế: '{data_1['room_number']}'"
    assert b1_info["check_in"] in data_1["check_in"], f"Ngày nhận phòng sai! Kì vọng: '{b1_info['check_in']}', Thực tế: '{data_1['check_in']}'"
    assert b1_info["check_out"] in data_1["check_out"], f"Ngày trả phòng sai! Kì vọng: '{b1_info['check_out']}', Thực tế: '{data_1['check_out']}'"
    assert any(s in data_1["status"] for s in [b1_info["status_text"], "Đã đặt", "Đã xác nhận", "CONFIRMED"]), f"Trạng thái sai! Kì vọng: '{b1_info['status_text']}', Thực tế: '{data_1['status']}'"

    # 4. Assert thông tin Đơn 2 (Trần Văn Bình)
    row_b2 = manage_page.get_booking_row_by_code(b2_info["code"])
    data_2 = manage_page.get_row_data(row_b2)

    assert b2_info["customer_name"] in data_2["customer_name"], f"Tên khách 2 sai! Kì vọng: '{b2_info['customer_name']}', Thực tế: '{data_2['customer_name']}'"
    assert b2_info["phone"] in data_2["phone"], f"SĐT 2 sai! Kì vọng: '{b2_info['phone']}', Thực tế: '{data_2['phone']}'"
    assert b2_info["room_type"] in data_2["room_type"], f"Loại phòng 2 sai! Kì vọng: '{b2_info['room_type']}', Thực tế: '{data_2['room_type']}'"
    assert b2_info["room_number"] in data_2["room_number"], f"Số phòng 2 sai! Kì vọng: '{b2_info['room_number']}', Thực tế: '{data_2['room_number']}'"
    assert b2_info["check_in"] in data_2["check_in"], f"Ngày đến 2 sai! Kì vọng: '{b2_info['check_in']}', Thực tế: '{data_2['check_in']}'"
    assert b2_info["check_out"] in data_2["check_out"], f"Ngày đi 2 sai! Kì vọng: '{b2_info['check_out']}', Thực tế: '{data_2['check_out']}'"
    assert any(s in data_2["status"] for s in [b2_info["status_text"], "Đang sử dụng", "OCCUPIED"]), f"Trạng thái 2 sai! Thực tế: '{data_2['status']}'"

    # Lưu ảnh minh chứng
    manage_page.take_screenshot("tc4_hotel_owner_view_bookings.png")
