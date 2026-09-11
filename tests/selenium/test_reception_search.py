import sys
import os
import hashlib
from datetime import timedelta
from decimal import Decimal
import pytest
from unittest.mock import patch

# Đảm bảo đường dẫn root dự án có trong sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.models import (
    User, UserRole, Room, RoomStatus,
    Booking, BookingStatus, BookingDetail, Payment
)
from app.utils import get_vn_time
from app.services.checkout_service import CheckoutService
from tests.selenium.pages import AuthPage, ManageBookingsPage


@pytest.fixture(scope="module", autouse=True)
def disable_auto_checkout_during_search():
    """Tắt cơ chế auto checkout trong lúc kiểm thử tìm kiếm để đơn không bị chuyển trạng thái."""
    with patch.object(CheckoutService, "process_auto_checkout", return_value=None):
        yield


def test_access_denied_for_customer_role(live_server, selenium_driver, test_session, sample_customer, sample_receptionist, sample_booking):
    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(sample_customer.username, "123456")

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open(f"{live_server.url}/reception/bookings")

    manage_page.wait.until(lambda d: "403" in d.page_source or "Forbidden" in d.page_source or "Không có quyền truy cập" in d.page_source)

    page_source = selenium_driver.page_source
    assert "403" in page_source or "Forbidden" in page_source
    assert any(msg in page_source for msg in ["Không có quyền truy cập", "Forbidden", "You don't have the permission"])

    assert len(selenium_driver.find_elements(*manage_page.SEARCH_INPUT)) == 0
    assert len(selenium_driver.find_elements(*manage_page.TAB_LIST)) == 0
    manage_page.take_screenshot("reception_access_denied.png")


def test_priority_sorting_for_today_checkin_checkout(live_server, selenium_driver, test_session, sample_receptionist, sample_booking):
    from app.models import Booking
    from app.utils import get_vn_time
    from datetime import timedelta
    today = get_vn_time().date()
    b1 = test_session.query(Booking).filter_by(total_price=4000000).first()
    b2 = test_session.query(Booking).filter_by(total_price=2000000, check_in=today).first()
    b3 = test_session.query(Booking).filter_by(total_price=1000000).first()
    b4 = test_session.query(Booking).filter_by(total_price=2000000, check_in=today + timedelta(days=5)).first()
    
    bk1_code = f"BK{b1.id:03d}"
    bk2_code = f"BK{b2.id:03d}"
    bk3_code = f"BK{b3.id:03d}"
    bk4_code = f"BK{b4.id:03d}"
    expected_codes_map = {'bk1_code': bk1_code, 'bk2_code': bk2_code, 'bk3_code': bk3_code, 'bk4_code': bk4_code}

    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(sample_receptionist.username, "123456")

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)

    codes = manage_page.get_booking_codes()
    
    
    
    

    assert bk2_code in codes
    assert bk3_code in codes
    # bk4_code is on page 2 because it has lower priority and pagination is 10 items/page

    assert bk2_code in codes[:4]
    assert bk3_code in codes[:4]

    assert bk2_code in codes[:4]
    assert bk3_code in codes[:4]

    manage_page.take_screenshot("reception_priority_sorting.png")


def test_filter_bookings_by_status(live_server, selenium_driver, test_session, sample_receptionist, sample_booking):
    from app.models import Booking
    from app.utils import get_vn_time
    from datetime import timedelta
    today = get_vn_time().date()
    b1 = test_session.query(Booking).filter_by(total_price=4000000).first()
    b2 = test_session.query(Booking).filter_by(total_price=2000000, check_in=today).first()
    b3 = test_session.query(Booking).filter_by(total_price=1000000).first()
    b4 = test_session.query(Booking).filter_by(total_price=2000000, check_in=today + timedelta(days=5)).first()
    
    bk1_code = f"BK{b1.id:03d}"
    bk2_code = f"BK{b2.id:03d}"
    bk3_code = f"BK{b3.id:03d}"
    bk4_code = f"BK{b4.id:03d}"
    expected_codes_map = {'bk1_code': bk1_code, 'bk2_code': bk2_code, 'bk3_code': bk3_code, 'bk4_code': bk4_code}

    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(sample_receptionist.username, "123456")

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)
    manage_page.search(status="CHECKED_IN")

    codes = manage_page.get_booking_codes()

    assert bk1_code in codes
    assert bk3_code in codes
    # The other codes (b_owner_1, bk_in_use, b_boundary_1, b_bound_cancelled) might also be in codes
    # depending on their status and pagination. As long as bk1 and bk3 are found, the filter works.
    assert bk2_code not in codes
    assert bk4_code not in codes

    rows = manage_page.get_booking_rows()
    for row in rows:
        status_text = manage_page.get_row_status_text(row)
        assert "Đang sử dụng" in status_text

    manage_page.take_screenshot("reception_filter_status.png")


@pytest.mark.parametrize("scenario_id,keyword,expected_codes_key,screenshot_filename", [
    ("name", "Nguyễn Văn A", ["bk1_code"], "reception_search_name.png"),
    ("phone", "012345678", ["bk1_code"], "reception_search_phone.png"),
    ("not_found", "KhôngTồnTại999", [], "reception_search_not_found.png"),
    ("empty", "", ["bk1_code", "bk2_code", "bk3_code", "bk4_code"], "reception_search_empty.png"),
    ("partial", "Nguyễn", ["bk1_code"], "reception_search_partial.png"),
    ("whitespace", "  Nguyễn Văn A  ", ["bk1_code"], "reception_search_whitespace.png"),
])
def test_search_bookings_scenarios(
    live_server, selenium_driver, test_session, sample_receptionist, sample_booking,
    scenario_id, keyword, expected_codes_key, screenshot_filename
):
    from app.models import Booking
    from app.utils import get_vn_time
    from datetime import timedelta
    today = get_vn_time().date()
    b1 = test_session.query(Booking).filter_by(total_price=4000000).first()
    b2 = test_session.query(Booking).filter_by(total_price=2000000, check_in=today).first()
    b3 = test_session.query(Booking).filter_by(total_price=1000000).first()
    b4 = test_session.query(Booking).filter_by(total_price=2000000, check_in=today + timedelta(days=5)).first()
    
    bk1_code = f"BK{b1.id:03d}"
    bk2_code = f"BK{b2.id:03d}"
    bk3_code = f"BK{b3.id:03d}"
    bk4_code = f"BK{b4.id:03d}"
    expected_codes_map = {'bk1_code': bk1_code, 'bk2_code': bk2_code, 'bk3_code': bk3_code, 'bk4_code': bk4_code}

    auth_page = AuthPage(selenium_driver)
    auth_page.open_page(live_server.url)
    auth_page.login(sample_receptionist.username, "123456")

    manage_page = ManageBookingsPage(selenium_driver)
    manage_page.open_page(live_server.url)
    
    manage_page.search(text=keyword)

    if not expected_codes_key:
        assert manage_page.is_empty_message_displayed()
        assert "Không tìm thấy thông tin đặt chỗ phù hợp" in manage_page.get_empty_message_text()
        assert len(manage_page.get_booking_rows()) == 0
    else:
        expected_codes = [expected_codes_map[k] for k in expected_codes_key]
        actual_codes = manage_page.get_booking_codes()
        if scenario_id == "empty":
            assert len(actual_codes) == 10
        else:
            assert set(actual_codes) == set(expected_codes)

    manage_page.take_screenshot(screenshot_filename)
