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


def test_hotel_owner_views_booking_list(live_server, selenium_driver, test_session, sample_admin, sample_booking, sample_rooms):
    from app.models import Booking
    from datetime import date
    
    owner_user = sample_admin.username
    owner_pass = "123456"
    
    b1 = test_session.query(Booking).filter_by(check_in=date(2026, 9, 15)).first()
    b2 = test_session.query(Booking).filter_by(total_price=7500000.00).first()
    
    b1_info = {
        "code": f"BK{b1.id:03d}", "customer_name": "customer", "phone": "",
        "room_type": "Deluxe Ocean View", "room_number": "101", "check_in": "15/09/2026", "check_out": "18/09/2026", "status_text": "Đang sử dụng"
    }
    b2_info = {
        "code": f"BK{b2.id:03d}", "customer_name": "Trần Văn Bình", "phone": "0987654321",
        "room_type": "Suite Gia Đình", "room_number": "P302", "check_in": b2.check_in.strftime('%d/%m/%Y'), "check_out": b2.check_out.strftime('%d/%m/%Y'), "status_text": "Đang sử dụng"
    }

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

    # 3. Assert thông tin Đơn 1
    row_b1 = manage_page.get_booking_row_by_code(b1_info["code"])
    data_1 = manage_page.get_row_data(row_b1)

    assert b1_info["customer_name"] in data_1["customer_name"], f"Tên khách sai! Kì vọng: '{b1_info['customer_name']}', Thực tế: '{data_1['customer_name']}'"
    assert b1_info["room_type"] in data_1["room_type"], f"Loại phòng sai! Kì vọng: '{b1_info['room_type']}', Thực tế: '{data_1['room_type']}'"
    assert b1_info["room_number"] in data_1["room_number"], f"Số phòng sai! Kì vọng: '{b1_info['room_number']}', Thực tế: '{data_1['room_number']}'"
    assert b1_info["check_in"] in data_1["check_in"], f"Ngày nhận phòng sai! Kì vọng: '{b1_info['check_in']}', Thực tế: '{data_1['check_in']}'"
    assert b1_info["check_out"] in data_1["check_out"], f"Ngày trả phòng sai! Kì vọng: '{b1_info['check_out']}', Thực tế: '{data_1['check_out']}'"
    assert any(s in data_1["status"] for s in [b1_info["status_text"], "Đã đặt", "Đã xác nhận", "CONFIRMED"]), f"Trạng thái sai! Kì vọng: '{b1_info['status_text']}', Thực tế: '{data_1['status']}'"

    # 4. Assert thông tin Đơn 2
    row_b2 = manage_page.get_booking_row_by_code(b2_info["code"])
    data_2 = manage_page.get_row_data(row_b2)

    assert b2_info["customer_name"] in data_2["customer_name"], f"Tên khách 2 sai! Kì vọng: '{b2_info['customer_name']}', Thực tế: '{data_2['customer_name']}'"
    assert b2_info["room_type"] in data_2["room_type"], f"Loại phòng 2 sai! Kì vọng: '{b2_info['room_type']}', Thực tế: '{data_2['room_type']}'"
    assert b2_info["room_number"] in data_2["room_number"], f"Số phòng 2 sai! Kì vọng: '{b2_info['room_number']}', Thực tế: '{data_2['room_number']}'"
    assert b2_info["check_in"] in data_2["check_in"], f"Ngày đến 2 sai! Kì vọng: '{b2_info['check_in']}', Thực tế: '{data_2['check_in']}'"
    assert b2_info["check_out"] in data_2["check_out"], f"Ngày đi 2 sai! Kì vọng: '{b2_info['check_out']}', Thực tế: '{data_2['check_out']}'"
    assert any(s in data_2["status"] for s in [b2_info["status_text"], "Đang sử dụng", "OCCUPIED"]), f"Trạng thái 2 sai! Thực tế: '{data_2['status']}'"

    manage_page.take_screenshot("hotel_owner_view_bookings.png")
