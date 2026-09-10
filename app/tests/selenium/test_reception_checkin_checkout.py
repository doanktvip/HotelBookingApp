import sys
import os
import atexit
import time
import hashlib
from datetime import date, timedelta
from decimal import Decimal
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.models import (
    User, UserRole, Hotel, RoomType, Room, RoomStatus,
    Booking, BookingStatus, BookingDetail, Payment, PaymentMethod, PaymentStatus
)
from app.utils import get_vn_time

CHROMEDRIVER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../.venv/chromedriver.exe'))
if os.path.exists(CHROMEDRIVER_PATH):
    service = Service(executable_path=CHROMEDRIVER_PATH)
else:
    service = Service()

atexit.register(lambda: service.stop() if hasattr(service, 'process') and service.process else None)


@pytest.fixture(scope="function")
def driver():
    options = webdriver.ChromeOptions()
    if os.environ.get('SELENIUM_HEADLESS', '0') == '1':
        options.add_argument('--headless=new')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1600,1000')

    driver_instance = webdriver.Chrome(service=service, options=options)
    driver_instance.implicitly_wait(10)
    yield driver_instance
    driver_instance.quit()


def capture_screenshot(driver, filename):
    """Chụp và lưu ảnh màn hình vào thư mục screenshots/ và đồng bộ sang brain artifacts."""
    screenshots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../screenshots"))
    os.makedirs(screenshots_dir, exist_ok=True)
    filepath = os.path.join(screenshots_dir, filename)
    driver.save_screenshot(filepath)

    brain_dir = r"C:\Users\Admin\.gemini\antigravity\brain\b1b75c48-d695-459b-8509-7a4460c89c54"
    if os.path.exists(brain_dir):
        try:
            import shutil
            shutil.copy2(filepath, os.path.join(brain_dir, filename))
        except Exception:
            pass

    return filepath


def login_receptionist(driver, base_url, username, password):
    driver.get(f"{base_url}/login")
    wait = WebDriverWait(driver, 10)
    user_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form[action='/login'] input[name='username']")))
    pass_input = driver.find_element(By.CSS_SELECTOR, "form[action='/login'] input[name='password']")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "form[action='/login'] button[type='submit']")

    user_input.clear()
    user_input.send_keys(username)
    pass_input.clear()
    pass_input.send_keys(password)
    submit_btn.click()

    wait.until(lambda d: "/login" not in d.current_url)


def navigate_to_bookings_tab(driver, base_url):
    driver.get(f"{base_url}/reception/bookings?tab=list")
    wait = WebDriverWait(driver, 10)
    try:
        tab_pane = wait.until(EC.presence_of_element_located((By.ID, "bookings-content")))
        if "active" not in tab_pane.get_attribute("class"):
            tab_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-bs-target="#bookings-content"]')))
            driver.execute_script("arguments[0].click();", tab_btn)
        wait.until(lambda d: "active" in d.find_element(By.ID, "bookings-content").get_attribute("class"))
    except Exception:
        pass


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


def get_booking_row(driver, booking_id):
    booking_code = f"BK{booking_id:03d}"
    xpath = f"//tr[contains(@data-booking-code, '{booking_code}') or .//td[contains(text(), '{booking_code}')]]"
    wait = WebDriverWait(driver, 10)
    row = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row)
    return row


def get_status_text(row):
    status_el = row.find_element(By.CSS_SELECTOR, ".status-cell")
    text = (status_el.text or "").strip()
    if not text:
        text = (status_el.get_attribute("textContent") or "").strip()
    return text


def test_tc15_cannot_checkin_non_confirmed_booking(live_server, driver, seed_checkin_checkout_data):
    """
    TC15: Không thể Check-in đơn không ở trạng thái 'Đã đặt' (đơn đang sử dụng / CHECKED_IN).
    """
    login_receptionist(
        driver, live_server.url,
        seed_checkin_checkout_data["receptionist_username"],
        seed_checkin_checkout_data["receptionist_password"]
    )
    navigate_to_bookings_tab(driver, live_server.url)

    row = get_booking_row(driver, seed_checkin_checkout_data["bk_in_use_id"])
    assert "Đang sử dụng" in get_status_text(row)

    checkin_btns = row.find_elements(By.CSS_SELECTOR, "button[value='checkin'], .checkin-btn")
    assert len(checkin_btns) == 0 or not checkin_btns[0].is_displayed() or checkin_btns[0].get_attribute("disabled") is not None, \
        "Nút Check-in vẫn xuất hiện hoặc đang khả dụng cho đơn đã nhận phòng (Đang sử dụng)!"

    capture_screenshot(driver, "reception_tc15_cannot_checkin_non_confirmed.png")


def test_tc16_cannot_checkin_cancelled_booking(live_server, driver, seed_checkin_checkout_data):
    """
    TC16: Chặn hoàn toàn thao tác nhận phòng đối với đơn đã bị hủy (CANCELLED).
    """
    login_receptionist(
        driver, live_server.url,
        seed_checkin_checkout_data["receptionist_username"],
        seed_checkin_checkout_data["receptionist_password"]
    )
    navigate_to_bookings_tab(driver, live_server.url)

    row = get_booking_row(driver, seed_checkin_checkout_data["bk_cancelled_id"])
    assert "Đã hủy" in get_status_text(row)

    checkin_btns = row.find_elements(By.CSS_SELECTOR, "button[value='checkin'], .checkin-btn")
    assert len(checkin_btns) == 0 or not checkin_btns[0].is_displayed(), \
        "Nút Check-in vẫn xuất hiện cho đơn đã bị hủy (CANCELLED)!"

    capture_screenshot(driver, "reception_tc16_cannot_checkin_cancelled.png")


def test_tc18_booking_status_completed_after_successful_checkout(live_server, driver, test_app, test_db, seed_checkin_checkout_data):
    """
    TC18: Check-out thành công chuyển trạng thái đơn sang 'Hoàn thành' (COMPLETED)
    và giải phóng phòng Room-101 về trạng thái AVAILABLE.
    """
    login_receptionist(
        driver, live_server.url,
        seed_checkin_checkout_data["receptionist_username"],
        seed_checkin_checkout_data["receptionist_password"]
    )
    navigate_to_bookings_tab(driver, live_server.url)

    wait = WebDriverWait(driver, 10)
    checkout_btn = wait.until(EC.element_to_be_clickable((By.ID, f"checkout-btn-{seed_checkin_checkout_data['bk_in_use_id']}")))
    driver.execute_script("arguments[0].click();", checkout_btn)

    wait.until(EC.visibility_of_element_located((By.ID, "checkoutModal")))

    confirm_btn = wait.until(EC.element_to_be_clickable((By.ID, "confirmCheckoutBtn")))
    driver.execute_script("arguments[0].click();", confirm_btn)

    wait.until(EC.staleness_of(confirm_btn))

    navigate_to_bookings_tab(driver, live_server.url)

    row = get_booking_row(driver, seed_checkin_checkout_data["bk_in_use_id"])
    status_text = get_status_text(row)
    assert any(s in status_text for s in ["Hoàn thành", "Đã hoàn tất", "COMPLETED"]), \
        f"Trạng thái hiển thị trên giao diện chưa đổi thành Hoàn tất! Thực tế: {status_text}"

    capture_screenshot(driver, "reception_tc18_checkout_success_completed.png")

    with test_app.app_context():
        test_db.session.expire_all()
        room = test_db.session.get(Room, seed_checkin_checkout_data["room_101_id"])
        booking = test_db.session.get(Booking, seed_checkin_checkout_data["bk_in_use_id"])
        assert room.status == RoomStatus.AVAILABLE, f"Phòng Room-101 chưa được giải phóng về AVAILABLE! Thực tế: {room.status}"
        assert booking.status == BookingStatus.COMPLETED, f"Trạng thái đơn trong DB chưa là COMPLETED! Thực tế: {booking.status}"


def test_tc19_cannot_checkout_non_checked_in_booking(live_server, driver, seed_checkin_checkout_data):
    """
    TC19: Không thể thực hiện trả phòng khi khách chưa check-in (đơn ở trạng thái CONFIRMED).
    """
    login_receptionist(
        driver, live_server.url,
        seed_checkin_checkout_data["receptionist_username"],
        seed_checkin_checkout_data["receptionist_password"]
    )
    navigate_to_bookings_tab(driver, live_server.url)

    row = get_booking_row(driver, seed_checkin_checkout_data["bk_confirmed_id"])
    assert "Đang sử dụng" not in get_status_text(row)

    checkout_btns = row.find_elements(By.CSS_SELECTOR, "button[onclick*='openCheckoutModal'], .checkout-btn")
    assert len(checkout_btns) == 0 or not checkout_btns[0].is_displayed() or checkout_btns[0].get_attribute("disabled") is not None, \
        "Nút Check-out vẫn xuất hiện hoặc đang khả dụng cho đơn chưa nhận phòng (CONFIRMED)!"

    capture_screenshot(driver, "reception_tc19_cannot_checkout_non_checked_in.png")


def test_tc20_cannot_checkout_when_payment_incomplete(live_server, driver, test_app, test_db, seed_checkin_checkout_data):
    """
    TC20: Hệ thống hiển thị cảnh báo yêu cầu thanh toán đầy đủ trước khi trả phòng;
    đơn giữ nguyên trạng thái 'Đang sử dụng' (CHECKED_IN).
    """
    login_receptionist(
        driver, live_server.url,
        seed_checkin_checkout_data["receptionist_username"],
        seed_checkin_checkout_data["receptionist_password"]
    )
    navigate_to_bookings_tab(driver, live_server.url)

    wait = WebDriverWait(driver, 10)
    checkout_btn = wait.until(EC.element_to_be_clickable((By.ID, f"checkout-btn-{seed_checkin_checkout_data['bk_unpaid_id']}")))
    driver.execute_script("arguments[0].click();", checkout_btn)

    wait.until(EC.visibility_of_element_located((By.ID, "checkoutModal")))

    wait.until(lambda d: d.find_element(By.ID, "checkout_balance").text != "0 đ")

    balance_text = driver.find_element(By.ID, "checkout_balance").text
    assert balance_text != "0 đ", "Số dư cần thanh toán phải lớn hơn 0 đối với đơn chưa trả đủ tiền!"

    confirm_btn = driver.find_element(By.ID, "confirmCheckoutBtn")
    alert_box = driver.find_element(By.ID, "checkout_alert")
    is_btn_blocked = (confirm_btn.get_attribute("disabled") is not None) or (not confirm_btn.is_enabled())
    is_warning_shown = alert_box.is_displayed() or ("Yêu cầu thanh toán thêm" in confirm_btn.text)
    assert is_btn_blocked or is_warning_shown, "Hệ thống không chặn hoặc cảnh báo khi đơn còn khoản nợ chưa thanh toán!"

    capture_screenshot(driver, "reception_tc20_checkout_unpaid_warning.png")

    close_btn = driver.find_element(By.CSS_SELECTOR, "#checkoutModal .btn-close")
    driver.execute_script("arguments[0].click();", close_btn)
    wait.until(EC.invisibility_of_element_located((By.ID, "checkoutModal")))

    row = get_booking_row(driver, seed_checkin_checkout_data["bk_unpaid_id"])
    assert "Đang sử dụng" in get_status_text(row)

    with test_app.app_context():
        test_db.session.expire_all()
        booking = test_db.session.get(Booking, seed_checkin_checkout_data["bk_unpaid_id"])
        assert booking.status == BookingStatus.CONFIRMED, "Trạng thái đơn bị thay đổi dù chưa thanh toán đủ!"


def test_tc21_cancel_checkout_modal_action(live_server, driver, test_app, test_db, seed_checkin_checkout_data):
    """
    TC21: Hủy hoặc đóng modal thanh toán: modal đóng, trạng thái đơn giữ nguyên 'Đang sử dụng',
    phòng Room-101 vẫn giữ nguyên OCCUPIED.
    """
    login_receptionist(
        driver, live_server.url,
        seed_checkin_checkout_data["receptionist_username"],
        seed_checkin_checkout_data["receptionist_password"]
    )
    navigate_to_bookings_tab(driver, live_server.url)

    wait = WebDriverWait(driver, 10)
    checkout_btn = wait.until(EC.element_to_be_clickable((By.ID, f"checkout-btn-{seed_checkin_checkout_data['bk_in_use_id']}")))
    driver.execute_script("arguments[0].click();", checkout_btn)

    wait.until(EC.visibility_of_element_located((By.ID, "checkoutModal")))

    cancel_btn = driver.find_element(By.ID, "cancelCheckoutBtn")
    driver.execute_script("arguments[0].click();", cancel_btn)

    wait.until(EC.invisibility_of_element_located((By.ID, "checkoutModal")))

    row = get_booking_row(driver, seed_checkin_checkout_data["bk_in_use_id"])
    assert "Đang sử dụng" in get_status_text(row)

    capture_screenshot(driver, "reception_tc21_cancel_checkout_modal.png")

    with test_app.app_context():
        test_db.session.expire_all()
        room = test_db.session.get(Room, seed_checkin_checkout_data["room_101_id"])
        booking = test_db.session.get(Booking, seed_checkin_checkout_data["bk_in_use_id"])
        assert room.status == RoomStatus.OCCUPIED, f"Phòng Room-101 bị đổi trạng thái trái phép! Thực tế: {room.status}"
        assert booking.status == BookingStatus.CONFIRMED, f"Đơn bị đổi trạng thái dù đã hủy modal! Thực tế: {booking.status}"
