from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import sys
import os
import atexit
import hashlib
from datetime import date, timedelta
from decimal import Decimal
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

service = Service(executable_path='../../../.venv/chromedriver.exe')
service.start()

# Đảm bảo đường dẫn root dự án có trong sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.models import (
    User, UserRole, Hotel, RoomType, Room, RoomStatus,
    Booking, BookingStatus, BookingDetail
)

# Tự động dừng ChromeDriver service khi kết thúc tiến trình test
atexit.register(lambda: service.stop() if hasattr(service, 'process') and service.process else None)


@pytest.fixture(scope="function")
def driver():
    """Khởi tạo Chrome WebDriver hiển thị trực quan (non-headless) để người dùng xem và chụp ảnh."""
    options = webdriver.ChromeOptions()
    # Mặc định tắt headless để hiển thị cửa sổ Chrome trực quan
    if os.environ.get('SELENIUM_HEADLESS', '0') == '1':
        options.add_argument('--headless=new')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    driver_instance = webdriver.Chrome(service=service, options=options)
    driver_instance.implicitly_wait(10)
    yield driver_instance
    driver_instance.quit()


@pytest.fixture(scope="function")
def selenium_driver(driver):
    """Fixture alias tương thích ngược."""
    return driver


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
    live_server, driver, test_db, setup_room_a_confirmed_booking
):
    """
    Test Case: test_room_available_when_booking_on_checkout_date
    Kiểm tra phòng (Room A) hiển thị khả dụng khi tìm kiếm đặt phòng vào đúng ngày check-out
    của một đơn CONFIRMED trước đó (đơn cũ: 2026-10-10 -> 2026-10-12, tìm mới: 2026-10-12 -> 2026-10-14).
    """
    room_type_id = setup_room_a_confirmed_booking["room_type_id"]
    room_type_name = setup_room_a_confirmed_booking["room_type_name"]
    booking_id = setup_room_a_confirmed_booking["booking_id"]

    try:
        # Bước 2: Dùng WebDriver điều hướng đến trang tìm kiếm phòng (/rooms hoặc /search)
        search_url = f"{live_server.url}/rooms"
        driver.get(search_url)

        wait = WebDriverWait(driver, 10)

        # Bước 3: Điền Check-in: 2026-10-12, Check-out: 2026-10-14, bấm nút "Tìm kiếm"
        check_in_input = wait.until(EC.presence_of_element_located((By.ID, "check_in")))
        check_out_input = wait.until(EC.presence_of_element_located((By.ID, "check_out")))

        new_check_in = "2026-10-12"
        new_check_out = "2026-10-14"

        # Thiết lập giá trị ngày qua JavaScript để đồng bộ chuẩn xác với HTML5 date picker
        driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        """, check_in_input, new_check_in)

        driver.execute_script("""
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        """, check_out_input, new_check_out)

        # Bấm nút "Tìm kiếm"
        search_btn = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//button[@id='search-btn'] | //button[@type='submit' and (contains(text(), 'Tìm kiếm') or contains(text(), 'Kiểm tra'))] | //button[@type='submit']"
            ))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", search_btn)
        import time
        time.sleep(0.5)
        try:
            search_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", search_btn)

        # Bước 4: Kiểm tra kết quả

        # --- Assertion 1: Room A xuất hiện trong danh sách kết quả khả dụng ---
        # 1.1 Tên phòng "Room A" xuất hiện trong danh sách kết quả
        room_title = wait.until(
            EC.visibility_of_element_located((
                By.XPATH, f"//h5[contains(text(), '{room_type_name}')]"
            ))
        )
        assert room_title.is_displayed(), f"Phòng '{room_type_name}' không hiển thị trong danh sách kết quả!"

        # 1.2 Nhãn trạng thái phòng thể hiện phòng còn trống (khả dụng), không phải 'Hết phòng'
        badge = wait.until(
            EC.presence_of_element_located((By.ID, f"room-avail-badge-{room_type_id}"))
        )
        assert badge.is_displayed(), "Không tìm thấy nhãn trạng thái phòng của Room A!"
        badge_text = badge.text.strip()
        assert "Hết phòng" not in badge_text, f"Room A bị hiển thị 'Hết phòng': {badge_text}"
        assert "Còn" in badge_text or "trống" in badge_text, f"Room A không ở trạng thái khả dụng: {badge_text}"

        # --- Assertion 2: Không xuất hiện thông báo lỗi trùng lịch ("Overlapping booking" / "Room unavailable") ---
        error_alerts = driver.find_elements(By.CSS_SELECTOR, ".alert-danger, .toast, .alert-text, .alert")
        for alert in error_alerts:
            if alert.is_displayed():
                msg = alert.text.strip().lower()
                assert "overlapping booking" not in msg, f"Xuất hiện thông báo lỗi trùng lịch: {msg}"
                assert "room unavailable" not in msg, f"Xuất hiện thông báo phòng không khả dụng: {msg}"
                assert "trùng lịch" not in msg, f"Xuất hiện thông báo lỗi trùng lịch: {msg}"

        page_content_lower = driver.page_source.lower()
        assert "overlapping booking" not in page_content_lower, "Giao diện hiển thị lỗi 'Overlapping booking'!"
        assert "room unavailable" not in page_content_lower, "Giao diện hiển thị lỗi 'Room unavailable'!"
        assert "trùng lịch" not in page_content_lower, "Giao diện hiển thị thông báo lỗi trùng lịch!"

        # --- Assertion 3: Nút "Đặt phòng" (Book Now) của Room A ở trạng thái enabled ---
        book_btn = wait.until(
            EC.presence_of_element_located((By.ID, f"room-book-btn-{room_type_id}"))
        )
        assert book_btn.is_displayed(), "Nút 'Đặt phòng' của Room A không hiển thị!"

        # Kiểm tra nút ở trạng thái enabled (không có disabled attribute, class không chứa disabled)
        disabled_attr = book_btn.get_attribute("disabled")
        assert disabled_attr is None or disabled_attr == "false", "Nút 'Đặt phòng' đang có thuộc tính disabled!"

        btn_classes = book_btn.get_attribute("class") or ""
        assert "disabled" not in btn_classes, f"Nút 'Đặt phòng' có class disabled: {btn_classes}"

        assert book_btn.is_enabled(), "Nút 'Đặt phòng' bị vô hiệu hóa (is_enabled == False)!"

        btn_text = book_btn.text.strip()
        assert "Đã hết" not in btn_text, f"Nút hiển thị trạng thái 'Đã hết': {btn_text}"
        assert "Đặt phòng" in btn_text or "Book Now" in btn_text, f"Text nút không đúng: {btn_text}"

        # Cuộn màn hình đến vị trí Room A để ảnh chụp thấy rõ tên phòng, badge còn phòng và nút Đặt phòng
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", book_btn)
        time.sleep(0.5)

        # Tự động chụp và lưu ảnh màn hình minh chứng kết quả kiểm thử vào thư mục screenshots/
        screenshots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../screenshots"))
        os.makedirs(screenshots_dir, exist_ok=True)
        screenshot_file = os.path.join(screenshots_dir, "test_room_available_when_booking_on_checkout_date.png")
        driver.save_screenshot(screenshot_file)

        # Dừng 3 giây để người dùng quan sát trực tiếp trên giao diện trình duyệt trước khi đóng
        time.sleep(3)

    finally:
        # Teardown: Đảm bảo xóa booking mẫu sau khi chạy xong để bảo đảm tính độc lập
        try:
            b = test_db.session.get(Booking, booking_id) if hasattr(test_db.session, 'get') else test_db.session.query(Booking).get(booking_id)
            if b:
                test_db.session.query(BookingDetail).filter_by(booking_id=booking_id).delete()
                test_db.session.delete(b)
                test_db.session.commit()
        except Exception:
            test_db.session.rollback()
