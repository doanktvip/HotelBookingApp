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

# Đảm bảo đường dẫn root dự án có trong sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.models import (
    User, UserRole, Hotel, RoomType, Floor, Room, RoomStatus,
    Booking, BookingStatus, BookingDetail, Payment, PaymentStatus
)
from app.utils import get_vn_time

# Khởi tạo ChromeDriver service
CHROMEDRIVER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../.venv/chromedriver.exe'))
if os.path.exists(CHROMEDRIVER_PATH):
    service = Service(executable_path=CHROMEDRIVER_PATH)
else:
    service = Service()

atexit.register(lambda: service.stop() if hasattr(service, 'process') and service.process else None)


@pytest.fixture(scope="function")
def driver():
    """Khởi tạo Chrome WebDriver hiển thị trực quan (non-headless) để theo dõi và chụp ảnh minh chứng."""
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


def login_user(driver, base_url, username, password):
    """Thực hiện đăng nhập qua form giao diện web (/login)."""
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

    # Chờ redirect ra khỏi trang login
    wait.until(lambda d: "/login" not in d.current_url)


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

        # 7. Đơn đặt phòng 1: Nguyễn Thị Mai - Phòng P301 - Đã xác nhận (CONFIRMED)
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


def test_tc4_hotel_owner_views_booking_list(live_server, driver, setup_tc4_hotel_owner_booking_data):
    """
    TC4: Chủ khách sạn xem danh sách đơn đặt phòng.
    - Precondition: Đã có tài khoản Chủ khách sạn và các đơn đặt phòng trong hệ thống.
    - Action:
        1. Đăng nhập bằng tài khoản Chủ khách sạn.
        2. Chọn 'Quản lý đơn đặt phòng' từ thanh menu điều hướng.
    - Assert:
        Hệ thống hiển thị danh sách đơn với đầy đủ thông tin:
        + Tên khách hàng
        + Số điện thoại
        + Loại phòng
        + Số phòng
        + Ngày giờ đến/đi (check-in / check-out)
        + Trạng thái đơn đặt phòng
    - Minh chứng: Chụp ảnh màn hình tc4_hotel_owner_view_bookings.png.
    """
    data = setup_tc4_hotel_owner_booking_data
    owner_user = data["owner_username"]
    owner_pass = data["owner_password"]
    b1_info = data["booking1"]
    b2_info = data["booking2"]

    wait = WebDriverWait(driver, 10)

    # --------------------------------------------------------------------------
    # Bước 1: Đăng nhập bằng tài khoản Chủ khách sạn
    # --------------------------------------------------------------------------
    login_user(driver, live_server.url, owner_user, owner_pass)

    # Xác thực đã đăng nhập thành công bằng cách kiểm tra dropdown tài khoản của Chủ khách sạn
    user_dropdown = wait.until(EC.visibility_of_element_located((By.XPATH, f"//span[contains(text(), '{owner_user}')]")))
    assert user_dropdown.is_displayed(), "Đăng nhập Chủ khách sạn không thành công!"

    # --------------------------------------------------------------------------
    # Bước 2: Chọn 'Quản lý đơn đặt phòng' từ thanh menu điều hướng
    # --------------------------------------------------------------------------
    manage_link = wait.until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//a[contains(., 'Quản lý đơn đặt phòng')] | //button[contains(., 'Quản lý đơn đặt phòng')]"
        ))
    )
    driver.execute_script("arguments[0].click();", manage_link)

    # Đảm bảo trang quản lý đơn mở ra và tab 'Danh sách đơn' hiển thị
    wait.until(lambda d: "/admin/bookings" in d.current_url or "/recept" in d.current_url)

    # Nếu tab danh sách đơn chưa active thì kích hoạt tab
    try:
        bookings_tab_pane = wait.until(EC.presence_of_element_located((By.ID, "bookings-content")))
        if "active" not in bookings_tab_pane.get_attribute("class"):
            tab_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-bs-target='#bookings-content']")))
            driver.execute_script("arguments[0].click();", tab_btn)
        wait.until(lambda d: "active" in d.find_element(By.ID, "bookings-content").get_attribute("class"))
    except Exception:
        pass

    # Chờ các dòng dữ liệu đơn đặt phòng xuất hiện trong bảng
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "tr.booking-row")))

    # --------------------------------------------------------------------------
    # Assert: Hệ thống hiển thị danh sách đơn với đầy đủ 6 thông tin bắt buộc
    # --------------------------------------------------------------------------
    # 1. Kiểm tra đơn đặt phòng 1 (Nguyễn Thị Mai)
    row_b1 = wait.until(
        EC.presence_of_element_located((
            By.XPATH, f"//tr[contains(@class, 'booking-row')][.//td[contains(@class, 'booking-code-cell') and contains(text(), '{b1_info['code']}')]]"
        ))
    )
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", row_b1)
    time.sleep(0.5)

    cust_name_1 = row_b1.find_element(By.CSS_SELECTOR, ".customer-name-cell").text.strip()
    cust_phone_1 = row_b1.find_element(By.CSS_SELECTOR, ".customer-phone-cell").text.strip()
    room_type_1 = row_b1.find_element(By.CSS_SELECTOR, ".room-type-cell").text.strip()
    room_number_1 = row_b1.find_element(By.CSS_SELECTOR, ".room-number-cell").text.strip()
    checkin_date_1 = row_b1.find_element(By.CSS_SELECTOR, ".checkin-date-cell").text.strip()
    checkout_date_1 = row_b1.find_element(By.CSS_SELECTOR, ".checkout-date-cell").text.strip()
    status_1 = row_b1.find_element(By.CSS_SELECTOR, ".status-cell").text.strip()

    # Kiểm tra tên khách hàng
    assert b1_info["customer_name"] in cust_name_1, f"Tên khách hàng sai! Kỳ vọng: '{b1_info['customer_name']}', Thực tế: '{cust_name_1}'"
    # Kiểm tra số điện thoại
    assert b1_info["phone"] in cust_phone_1, f"Số điện thoại sai! Kỳ vọng: '{b1_info['phone']}', Thực tế: '{cust_phone_1}'"
    # Kiểm tra loại phòng
    assert b1_info["room_type"] in room_type_1, f"Loại phòng sai! Kỳ vọng: '{b1_info['room_type']}', Thực tế: '{room_type_1}'"
    # Kiểm tra số phòng
    assert b1_info["room_number"] in room_number_1, f"Số phòng sai! Kỳ vọng: '{b1_info['room_number']}', Thực tế: '{room_number_1}'"
    # Kiểm tra ngày giờ đến/đi
    assert b1_info["check_in"] in checkin_date_1, f"Ngày nhận phòng sai! Kỳ vọng: '{b1_info['check_in']}', Thực tế: '{checkin_date_1}'"
    assert b1_info["check_out"] in checkout_date_1, f"Ngày trả phòng sai! Kỳ vọng: '{b1_info['check_out']}', Thực tế: '{checkout_date_1}'"
    # Kiểm tra trạng thái (Chấp nhận 'Đã đặt', 'Đã xác nhận', hoặc 'CONFIRMED')
    assert any(s in status_1 for s in [b1_info["status_text"], "Đã đặt", "Đã xác nhận", "CONFIRMED"]), f"Trạng thái sai! Kỳ vọng: '{b1_info['status_text']}', Thực tế: '{status_1}'"

    # 2. Kiểm tra đơn đặt phòng 2 (Trần Văn Bình)
    row_b2 = wait.until(
        EC.presence_of_element_located((
            By.XPATH, f"//tr[contains(@class, 'booking-row')][.//td[contains(@class, 'booking-code-cell') and contains(text(), '{b2_info['code']}')]]"
        ))
    )
    cust_name_2 = row_b2.find_element(By.CSS_SELECTOR, ".customer-name-cell").text.strip()
    cust_phone_2 = row_b2.find_element(By.CSS_SELECTOR, ".customer-phone-cell").text.strip()
    room_type_2 = row_b2.find_element(By.CSS_SELECTOR, ".room-type-cell").text.strip()
    room_number_2 = row_b2.find_element(By.CSS_SELECTOR, ".room-number-cell").text.strip()
    checkin_date_2 = row_b2.find_element(By.CSS_SELECTOR, ".checkin-date-cell").text.strip()
    checkout_date_2 = row_b2.find_element(By.CSS_SELECTOR, ".checkout-date-cell").text.strip()
    status_2 = row_b2.find_element(By.CSS_SELECTOR, ".status-cell").text.strip()

    assert b2_info["customer_name"] in cust_name_2, f"Tên khách hàng 2 sai! Kỳ vọng: '{b2_info['customer_name']}', Thực tế: '{cust_name_2}'"
    assert b2_info["phone"] in cust_phone_2, f"SĐT khách hàng 2 sai! Kỳ vọng: '{b2_info['phone']}', Thực tế: '{cust_phone_2}'"
    assert b2_info["room_type"] in room_type_2, f"Loại phòng 2 sai! Kỳ vọng: '{b2_info['room_type']}', Thực tế: '{room_type_2}'"
    assert b2_info["room_number"] in room_number_2, f"Số phòng 2 sai! Kỳ vọng: '{b2_info['room_number']}', Thực tế: '{room_number_2}'"
    assert b2_info["check_in"] in checkin_date_2, f"Ngày đến 2 sai! Kỳ vọng: '{b2_info['check_in']}', Thực tế: '{checkin_date_2}'"
    assert b2_info["check_out"] in checkout_date_2, f"Ngày đi 2 sai! Kỳ vọng: '{b2_info['check_out']}', Thực tế: '{checkout_date_2}'"
    assert any(s in status_2 for s in [b2_info["status_text"], "Đang sử dụng", "OCCUPIED"]), f"Trạng thái 2 sai! Thực tế: '{status_2}'"

    # Cuộn màn hình để hiển thị trọn vẹn bảng danh sách đơn đặt phòng
    try:
        table_el = driver.find_element(By.CSS_SELECTOR, "table")
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", table_el)
        time.sleep(0.5)
    except Exception:
        pass

    # Chụp ảnh màn hình giao diện danh sách đơn đặt phòng làm minh chứng
    capture_screenshot(driver, "tc4_hotel_owner_view_bookings.png")
