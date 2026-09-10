import sys
import os
import atexit
import time
import shutil
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
    Booking, BookingStatus, BookingDetail
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
            shutil.copy2(filepath, os.path.join(brain_dir, filename))
        except Exception:
            pass

    return filepath


def scroll_to_room_card(driver, room_type_name):
    """Cuộn màn hình đến chính giữa thẻ phòng để thấy rõ thông tin, nhãn trống và nút đặt phòng."""
    try:
        room_card = driver.find_element(
            By.XPATH, f"//div[contains(@class, 'custom-room-card')][.//h5[contains(text(), '{room_type_name}')]]"
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", room_card)
        time.sleep(0.5)
    except Exception:
        pass


def login_customer(driver, base_url, username, password):
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


def search_room_dates(driver, check_in_str, check_out_str):
    wait = WebDriverWait(driver, 10)
    check_in_input = wait.until(EC.presence_of_element_located((By.ID, "check_in")))
    check_out_input = wait.until(EC.presence_of_element_located((By.ID, "check_out")))

    driver.execute_script("""
        arguments[0].removeAttribute('min');
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
    """, check_in_input, check_in_str)

    driver.execute_script("""
        arguments[0].removeAttribute('min');
        arguments[0].value = arguments[1];
        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
    """, check_out_input, check_out_str)

    search_btn = wait.until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//button[@id='search-btn'] | //button[@type='submit' and (contains(text(), 'Tìm kiếm') or contains(text(), 'Kiểm tra'))] | //button[@type='submit']"
        ))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_btn)
    driver.execute_script("arguments[0].click();", search_btn)

    wait.until(EC.staleness_of(search_btn))
    wait.until(EC.presence_of_element_located((By.ID, "check_in")))
    wait.until(lambda d: d.find_element(By.ID, "check_in").get_attribute("value") == check_in_str)


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


def test_tc5_room_available_when_checkin_equals_previous_checkout(live_server, driver, setup_tc5_boundary_checkin):
    """
    TC5: Ngày check-in của đơn mới trùng với ngày check-out của đơn CONFIRMED trước đó (2026-10-12).
    Phòng không bị tính là trùng lịch và hiển thị khả dụng (Available), nút 'Đặt phòng' enabled.
    """
    data = setup_tc5_boundary_checkin
    hotel_id = data["hotel_id"]
    room_type_id = data["room_type_id"]
    room_type_name = data["room_type_name"]

    driver.get(f"{live_server.url}/rooms?hotel_id={hotel_id}")
    wait = WebDriverWait(driver, 10)

    search_room_dates(driver, "2026-10-12", "2026-10-14")

    # 1. Assert: Room A xuất hiện trong danh sách kết quả khả dụng
    room_title = wait.until(EC.visibility_of_element_located((By.XPATH, f"//h5[contains(text(), '{room_type_name}')]")))
    assert room_title.is_displayed(), f"Phòng '{room_type_name}' không hiển thị trong danh sách kết quả!"

    # 2. Assert: Nhãn trạng thái hiển thị phòng khả dụng (không phải 'Hết phòng')
    badge = wait.until(EC.presence_of_element_located((By.ID, f"room-avail-badge-{room_type_id}")))
    assert badge.is_displayed(), "Không tìm thấy nhãn trạng thái phòng!"
    badge_text = badge.text.strip()
    assert "Hết phòng" not in badge_text, f"Phòng bị hiển thị 'Hết phòng': {badge_text}"
    assert "Còn" in badge_text and "trống" in badge_text, f"Phòng không ở trạng thái khả dụng: {badge_text}"

    # 3. Assert: Không xuất hiện thông báo lỗi trùng lịch
    page_text_lower = driver.page_source.lower()
    assert "overlapping booking" not in page_text_lower
    assert "trùng lịch" not in page_text_lower

    # 4. Assert: Nút 'Đặt phòng' (Book Now) ở trạng thái enabled
    book_btn = wait.until(EC.presence_of_element_located((By.ID, f"room-book-btn-{room_type_id}")))
    assert book_btn.is_displayed(), "Nút 'Đặt phòng' không hiển thị!"
    assert book_btn.get_attribute("disabled") is None or book_btn.get_attribute("disabled") == "false"
    assert "disabled" not in (book_btn.get_attribute("class") or "")
    assert book_btn.is_enabled(), "Nút 'Đặt phòng' bị vô hiệu hóa!"
    assert "Đã hết" not in book_btn.text

    scroll_to_room_card(driver, room_type_name)
    capture_screenshot(driver, "tc5_room_available_when_checkin_equals_previous_checkout.png")


def test_tc6_room_available_when_checkout_equals_next_checkin(live_server, driver, setup_tc6_boundary_checkout):
    """
    TC6: Ngày check-out của đơn mới trùng với ngày check-in của đơn CONFIRMED kế tiếp (2026-10-12).
    Phòng không bị xem là trùng lịch với đơn sau và hiển thị trong danh sách phòng trống khả dụng.
    """
    data = setup_tc6_boundary_checkout
    hotel_id = data["hotel_id"]
    room_type_id = data["room_type_id"]
    room_type_name = data["room_type_name"]

    driver.get(f"{live_server.url}/rooms?hotel_id={hotel_id}")
    wait = WebDriverWait(driver, 10)

    search_room_dates(driver, "2026-10-10", "2026-10-12")

    # 1. Assert: Room A hiển thị trong danh sách kết quả khả dụng
    room_title = wait.until(EC.visibility_of_element_located((By.XPATH, f"//h5[contains(text(), '{room_type_name}')]")))
    assert room_title.is_displayed(), f"Phòng '{room_type_name}' không hiển thị trong danh sách kết quả!"

    # 2. Assert: Nhãn trạng thái phòng thể hiện phòng khả dụng
    badge = wait.until(EC.presence_of_element_located((By.ID, f"room-avail-badge-{room_type_id}")))
    assert badge.is_displayed(), "Không tìm thấy nhãn trạng thái phòng!"
    badge_text = badge.text.strip()
    assert "Hết phòng" not in badge_text, f"Phòng bị hiển thị 'Hết phòng': {badge_text}"
    assert "Còn" in badge_text and "trống" in badge_text, f"Phòng không ở trạng thái khả dụng: {badge_text}"

    # 3. Assert: Không xuất hiện thông báo lỗi trùng lịch
    page_text_lower = driver.page_source.lower()
    assert "overlapping booking" not in page_text_lower
    assert "trùng lịch" not in page_text_lower

    # 4. Assert: Nút 'Đặt phòng' ở trạng thái enabled
    book_btn = wait.until(EC.presence_of_element_located((By.ID, f"room-book-btn-{room_type_id}")))
    assert book_btn.is_displayed(), "Nút 'Đặt phòng' không hiển thị!"
    assert book_btn.get_attribute("disabled") is None or book_btn.get_attribute("disabled") == "false"
    assert "disabled" not in (book_btn.get_attribute("class") or "")
    assert book_btn.is_enabled(), "Nút 'Đặt phòng' bị vô hiệu hóa!"
    assert "Đã hết" not in book_btn.text

    scroll_to_room_card(driver, room_type_name)
    capture_screenshot(driver, "tc6_room_available_when_checkout_equals_next_checkin.png")


def test_tc8_only_available_status_rooms_counted_for_today_checkin(live_server, driver, setup_tc8_today_availability):
    """
    TC8: Chỉ tính phòng có trạng thái vật lý AVAILABLE khi check-in trong ngày hôm nay.
    Các phòng BOOKED và OCCUPIED bị loại trừ, số lượng phòng trống hiển thị chỉ bằng 1.
    """
    data = setup_tc8_today_availability
    hotel_id = data["hotel_id"]
    room_type_id = data["room_type_id"]
    room_type_name = data["room_type_name"]

    driver.get(f"{live_server.url}/rooms?hotel_id={hotel_id}")
    wait = WebDriverWait(driver, 10)

    today = get_vn_time().date()
    tomorrow = today + timedelta(days=1)
    today_str = today.strftime("%Y-%m-%d")
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")

    search_room_dates(driver, today_str, tomorrow_str)

    # 1. Assert: Loại phòng hiển thị
    room_title = wait.until(EC.visibility_of_element_located((By.XPATH, f"//h5[contains(text(), '{room_type_name}')]")))
    assert room_title.is_displayed(), f"Loại phòng '{room_type_name}' không hiển thị!"

    # 2. Assert: Số lượng phòng trống hiển thị cho loại phòng này chỉ bằng 1 (chỉ tính Phòng 101 AVAILABLE)
    badge = wait.until(EC.presence_of_element_located((By.ID, f"room-avail-badge-{room_type_id}")))
    assert badge.is_displayed(), "Không tìm thấy nhãn trạng thái phòng!"
    badge_text = badge.text.strip()
    assert badge_text == "Còn 1 trống", f"Số lượng phòng trống không phải là 1! Thực tế hiển thị: '{badge_text}'"

    # 3. Assert: Nút đặt phòng vẫn enabled
    book_btn = wait.until(EC.presence_of_element_located((By.ID, f"room-book-btn-{room_type_id}")))
    assert book_btn.is_enabled(), "Nút 'Đặt phòng' bị vô hiệu hóa dù còn 1 phòng AVAILABLE!"

    scroll_to_room_card(driver, room_type_name)
    capture_screenshot(driver, "tc8_only_available_status_rooms_counted_for_today.png")


def test_tc6_cancelled_booking_cannot_perform_further_actions(live_server, driver, setup_tc6_cancelled_booking):
    """
    TC6 (Cancelled Booking): Đơn đặt phòng ở trạng thái CANCELLED ('Đã hủy') bị khóa mọi thao tác:
    - Huy hiệu trạng thái hiển thị rõ là 'Đã hủy'.
    - Nút 'Hủy đặt phòng' và nút 'Thanh toán' hoàn toàn không hiển thị trên giao diện.
    """
    data = setup_tc6_cancelled_booking
    username = data["customer_username"]
    password = data["customer_password"]
    booking_id = data["booking_id"]

    # Đăng nhập bằng tài khoản khách hàng
    login_customer(driver, live_server.url, username, password)

    # Truy cập trang Đơn của tôi (/my-bookings)
    driver.get(f"{live_server.url}/my-bookings")
    wait = WebDriverWait(driver, 10)

    # Tìm card của đơn đã hủy (chứa mã booking #booking_id)
    booking_card = wait.until(
        EC.presence_of_element_located((
            By.XPATH, f"//div[contains(@class, 'card')][.//span[contains(text(), '#{booking_id}')]]"
        ))
    )
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", booking_card)
    time.sleep(0.5)

    # 1. Assert: Huy hiệu trạng thái của đơn hiển thị rõ là 'Đã hủy' (hoặc CANCELLED)
    status_badge = booking_card.find_element(By.XPATH, ".//span[contains(@class, 'badge') and (contains(text(), 'Đã hủy') or contains(text(), 'CANCELLED'))]")
    assert status_badge.is_displayed(), "Không tìm thấy huy hiệu trạng thái 'Đã hủy' của đơn!"
    assert "Đã hủy" in status_badge.text or "CANCELLED" in status_badge.text

    # 2. Assert: Nút 'Hủy đặt phòng' hoàn toàn không hiển thị trên giao diện đối với đơn này
    cancel_btns = booking_card.find_elements(By.XPATH, ".//button[contains(text(), 'Hủy đặt phòng')] | .//a[contains(text(), 'Hủy đặt phòng')]")
    visible_cancel_btns = [b for b in cancel_btns if b.is_displayed()]
    assert len(visible_cancel_btns) == 0, "Nút 'Hủy đặt phòng' vẫn hiển thị đối với đơn đã hủy!"

    # 3. Assert: Nút 'Thanh toán' hoàn toàn không hiển thị trên giao diện đối với đơn này
    pay_btns = booking_card.find_elements(By.XPATH, ".//button[contains(text(), 'Thanh toán')] | .//a[contains(text(), 'Thanh toán')]")
    visible_pay_btns = [b for b in pay_btns if b.is_displayed()]
    assert len(visible_pay_btns) == 0, "Nút 'Thanh toán' vẫn hiển thị đối với đơn đã hủy!"

    capture_screenshot(driver, "tc6_cancelled_booking_cannot_perform_further_actions.png")
