import sys
import os
import time
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


def test_cannot_checkin_non_confirmed_booking(live_server, selenium_driver, test_session, sample_receptionist, sample_booking):
    from app.models import Booking, BookingStatus, Room
    from app.utils import get_vn_time
    from datetime import timedelta
    today = get_vn_time().date()
    bk_in_use_id = test_session.query(Booking).filter_by(check_in=today - timedelta(days=1), check_out=today + timedelta(days=1), total_price=2000000).first().id
    bk_confirmed_id = test_session.query(Booking).filter_by(check_in=today, check_out=today + timedelta(days=2), total_price=2000000, status=BookingStatus.CONFIRMED).first().id
    bk_cancelled_id = test_session.query(Booking).filter_by(status=BookingStatus.CANCELLED, total_price=2000000).first().id
    bk_unpaid_id = test_session.query(Booking).filter_by(total_price=3000000).first().id
    room_101_id = test_session.query(Room).filter_by(room_number='101').first().id

    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(sample_receptionist.username, "123456")

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)

    row = manage_page.get_booking_row_by_id(bk_in_use_id)
    assert "Đang sử dụng" in manage_page.get_row_status_text(row)
    assert not manage_page.has_checkin_button(row), "Nút Check-in vẫn xuất hiện!"
    manage_page.take_screenshot("reception_cannot_checkin_non_confirmed.png")


def test_cannot_checkin_cancelled_booking(live_server, selenium_driver, test_session, sample_receptionist, sample_booking):
    from app.models import Booking, BookingStatus, Room
    from app.utils import get_vn_time
    from datetime import timedelta
    today = get_vn_time().date()
    bk_in_use_id = test_session.query(Booking).filter_by(check_in=today - timedelta(days=1), check_out=today + timedelta(days=1), total_price=2000000).first().id
    bk_confirmed_id = test_session.query(Booking).filter_by(check_in=today, check_out=today + timedelta(days=2), total_price=2000000, status=BookingStatus.CONFIRMED).first().id
    bk_cancelled_id = test_session.query(Booking).filter_by(status=BookingStatus.CANCELLED, total_price=2000000).first().id
    bk_unpaid_id = test_session.query(Booking).filter_by(total_price=3000000).first().id
    room_101_id = test_session.query(Room).filter_by(room_number='101').first().id

    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(sample_receptionist.username, "123456")

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)

    row = manage_page.get_booking_row_by_id(bk_cancelled_id)
    assert "Đã hủy" in manage_page.get_row_status_text(row)
    assert not manage_page.has_checkin_button(row), "Nút Check-in vẫn xuất hiện!"
    manage_page.take_screenshot("reception_cannot_checkin_cancelled.png")


def test_booking_status_completed_after_successful_checkout(live_server, selenium_driver, test_session, sample_receptionist, sample_booking):
    from app.models import Booking, BookingStatus, Room
    from app.utils import get_vn_time
    from datetime import timedelta
    today = get_vn_time().date()
    bk_in_use_id = test_session.query(Booking).filter_by(check_in=today - timedelta(days=1), check_out=today + timedelta(days=1), total_price=2000000).first().id
    bk_confirmed_id = test_session.query(Booking).filter_by(check_in=today, check_out=today + timedelta(days=2), total_price=2000000, status=BookingStatus.CONFIRMED).first().id
    bk_cancelled_id = test_session.query(Booking).filter_by(status=BookingStatus.CANCELLED, total_price=2000000).first().id
    bk_unpaid_id = test_session.query(Booking).filter_by(total_price=3000000).first().id
    room_101_id = test_session.query(Room).filter_by(room_number='101').first().id

    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(sample_receptionist.username, "123456")

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)

    manage_page.click_checkout(bk_in_use_id)
    manage_page.confirm_checkout()

    manage_page.open_page(live_server.url)

    row = manage_page.get_booking_row_by_id(bk_in_use_id)
    status_text = manage_page.get_row_status_text(row)
    assert any(s in status_text for s in ["Hoàn thành", "Đã hoàn tất", "COMPLETED"])
    manage_page.take_screenshot("reception_checkout_success_completed.png")

    test_session.expire_all()
    room = test_session.get(Room, room_101_id)
    booking = test_session.get(Booking, bk_in_use_id)
    assert room.status == RoomStatus.AVAILABLE
    assert booking.status == BookingStatus.COMPLETED


def test_cannot_checkout_non_checked_in_booking(live_server, selenium_driver, test_session, sample_receptionist, sample_booking):
    from app.models import Booking, BookingStatus, Room
    from app.utils import get_vn_time
    from datetime import timedelta
    today = get_vn_time().date()
    bk_in_use_id = test_session.query(Booking).filter_by(check_in=today - timedelta(days=1), check_out=today + timedelta(days=1), total_price=2000000).first().id
    bk_confirmed_id = test_session.query(Booking).filter_by(check_in=today, check_out=today + timedelta(days=2), total_price=2000000, status=BookingStatus.CONFIRMED).first().id
    bk_cancelled_id = test_session.query(Booking).filter_by(status=BookingStatus.CANCELLED, total_price=2000000).first().id
    bk_unpaid_id = test_session.query(Booking).filter_by(total_price=3000000).first().id
    room_101_id = test_session.query(Room).filter_by(room_number='101').first().id

    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(sample_receptionist.username, "123456")

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)

    row = manage_page.get_booking_row_by_id(bk_confirmed_id)
    assert "Đang sử dụng" not in manage_page.get_row_status_text(row)
    assert not manage_page.has_checkout_button(row)
    manage_page.take_screenshot("reception_cannot_checkout_non_checked_in.png")


def test_cannot_checkout_when_payment_incomplete(live_server, selenium_driver, test_session, sample_receptionist, sample_booking):
    from app.models import Booking, BookingStatus, Room
    from app.utils import get_vn_time
    from datetime import timedelta
    today = get_vn_time().date()
    bk_in_use_id = test_session.query(Booking).filter_by(check_in=today - timedelta(days=1), check_out=today + timedelta(days=1), total_price=2000000).first().id

    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(sample_receptionist.username, "123456")

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)

    # Giảm số tiền đã thanh toán của bk_in_use để tạo balance > 0
    bk_in_use = test_session.get(Booking, bk_in_use_id)
    if bk_in_use and bk_in_use.payment:
        bk_in_use.payment.amount = bk_in_use.total_price - 500000
        test_session.commit()

    manage_page.search(text=f"BK{bk_in_use_id:03d}")
    manage_page.click_checkout(bk_in_use_id)

    details = manage_page.get_checkout_modal_details()
    assert details["balance"] != "0 đ"
    assert details["is_confirm_disabled"] is True
    assert details["alert_displayed"] is True

    manage_page.close_checkout_modal()
    manage_page.take_screenshot("reception_cannot_checkout_unpaid.png")

    test_session.expire_all()
    booking = test_session.get(Booking, bk_in_use_id)
    assert booking.status == BookingStatus.CONFIRMED


def test_cancel_checkout_modal_action(live_server, selenium_driver, test_session, sample_receptionist, sample_booking):
    from app.models import Booking, BookingStatus, Room
    from app.utils import get_vn_time
    from datetime import timedelta
    today = get_vn_time().date()
    bk_in_use_id = test_session.query(Booking).filter_by(check_in=today - timedelta(days=1), check_out=today + timedelta(days=1), total_price=2000000).first().id
    bk_confirmed_id = test_session.query(Booking).filter_by(check_in=today, check_out=today + timedelta(days=2), total_price=2000000, status=BookingStatus.CONFIRMED).first().id
    bk_cancelled_id = test_session.query(Booking).filter_by(status=BookingStatus.CANCELLED, total_price=2000000).first().id
    bk_unpaid_id = test_session.query(Booking).filter_by(total_price=3000000).first().id
    room_101_id = test_session.query(Room).filter_by(room_number='101').first().id

    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(sample_receptionist.username, "123456")

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)

    manage_page.click_checkout(bk_in_use_id)
    manage_page.close_checkout_modal()

    row = manage_page.get_booking_row_by_id(bk_in_use_id)
    assert "Đang sử dụng" in manage_page.get_row_status_text(row)
    manage_page.take_screenshot("reception_cancel_checkout_modal.png")

    test_session.expire_all()
    room = test_session.get(Room, room_101_id)
    booking = test_session.get(Booking, bk_in_use_id)
    assert room.status == RoomStatus.OCCUPIED
    assert booking.status == BookingStatus.CONFIRMED
