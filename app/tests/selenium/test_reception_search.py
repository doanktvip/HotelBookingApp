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
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

# Đảm bảo đường dẫn root dự án có trong sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.models import (
    User, UserRole, Hotel, RoomType, Room, RoomStatus,
    Booking, BookingStatus, BookingDetail, Payment
)
from app.utils import get_vn_time

# Khởi tạo ChromeDriver service
CHROMEDRIVER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../.venv/chromedriver.exe'))
if os.path.exists(CHROMEDRIVER_PATH):
    service = Service(executable_path=CHROMEDRIVER_PATH)
else:
    service = Service()

# Tự động dừng ChromeDriver service khi kết thúc
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
    """Chụp và lưu ảnh màn hình vào thư mục screenshots/ làm minh chứng kết quả kiểm thử."""
    screenshots_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../screenshots"))
    os.makedirs(screenshots_dir, exist_ok=True)
    filepath = os.path.join(screenshots_dir, filename)
    driver.save_screenshot(filepath)
    return filepath


def login_user(driver, base_url, username, password):
    """Hỗ trợ đăng nhập qua giao diện web (/login)."""
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


def navigate_to_bookings_tab(driver, base_url):
    """Điều hướng đến tab 'Danh sách đơn' trên trang Quản lý của Lễ tân."""
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


@pytest.fixture(scope="module")
def seed_reception_test_data(test_app, test_db):
    """
    Fixture Direct DB tạo dữ liệu kiểm thử quản lý đơn của Lễ tân:
    - 1 tài khoản Lễ tân (role=RECEPTIONIST, hotel_id=hotel.id)
    - 1 tài khoản Khách hàng (role=CUSTOMER)
    - 4 khách hàng mẫu (Nguyễn Văn A, Trần Thị B, Lê Văn C, Phạm Văn D)
    - 4 phòng vật lý (P101, P102, P103, P104)
    - 4 đơn mẫu có ID chuẩn 1..4 (BK001, BK002, BK003, BK004):
        * BK001: Khách "Nguyễn Văn A", SĐT "012345678", trạng thái "Đang sử dụng" (P101 OCCUPIED).
        * BK002: Khách "Trần Thị B", SĐT "098765432", CONFIRMED, check-in HÔM NAY.
        * BK003: Khách "Lê Văn C", SĐT "0333444555", trạng thái "Đang sử dụng" (P103 OCCUPIED), check-out HÔM NAY.
        * BK004: Khách "Phạm Văn D", SĐT "0777888999", CONFIRMED, check-in tương lai (+5 ngày).
    """
    with test_app.app_context():
        test_db.create_all()

        # Dọn dẹp dữ liệu trùng lặp nếu có từ trước
        old_bookings = test_db.session.query(Booking).filter(Booking.id.in_([1, 2, 3, 4])).all()
        for b in old_bookings:
            test_db.session.query(BookingDetail).filter_by(booking_id=b.id).delete()
            test_db.session.query(Payment).filter_by(booking_id=b.id).delete()
            test_db.session.delete(b)
        test_db.session.commit()

        # 1. Khách sạn mẫu
        hotel = test_db.session.query(Hotel).filter_by(name="Khách sạn Kiểm Thử Lễ Tân").first()
        if not hotel:
            hotel = Hotel(
                name="Khách sạn Kiểm Thử Lễ Tân",
                address="123 Đường Kiểm Thử Lễ Tân",
                location="TP Hồ Chí Minh",
                description="Khách sạn phục vụ kiểm thử tự động Lễ tân",
                rating=5.0,
                cancellation_policy_days=3
            )
            test_db.session.add(hotel)
            test_db.session.commit()
        hotel_id = hotel.id

        # 2. Tài khoản Lễ tân & Khách hàng
        hashed_pw = hashlib.md5("123456".encode('utf-8')).hexdigest()

        receptionist = test_db.session.query(User).filter_by(username="test_receptionist").first()
        if not receptionist:
            receptionist = User(
                username="test_receptionist",
                email="test_receptionist@hotel.com",
                password=hashed_pw,
                role=UserRole.RECEPTIONIST,
                is_verified=True,
                hotel_id=hotel_id
            )
            test_db.session.add(receptionist)
        else:
            receptionist.hotel_id = hotel_id
            receptionist.role = UserRole.RECEPTIONIST
            receptionist.password = hashed_pw

        customer = test_db.session.query(User).filter_by(username="test_customer").first()
        if not customer:
            customer = User(
                username="test_customer",
                email="test_customer@hotel.com",
                password=hashed_pw,
                role=UserRole.CUSTOMER,
                is_verified=True
            )
            test_db.session.add(customer)
        else:
            customer.role = UserRole.CUSTOMER
            customer.password = hashed_pw

        test_db.session.commit()

        # 3. 4 Khách hàng mẫu cho 4 đơn đặt phòng
        cust_a = test_db.session.query(User).filter_by(username="Nguyễn Văn A").first()
        if not cust_a:
            cust_a = User(
                username="Nguyễn Văn A",
                email="nguyenvana@hotel.com",
                phone="012345678",
                password=hashed_pw,
                role=UserRole.CUSTOMER,
                is_verified=True
            )
            test_db.session.add(cust_a)
        else:
            cust_a.phone = "012345678"

        cust_b = test_db.session.query(User).filter_by(username="Trần Thị B").first()
        if not cust_b:
            cust_b = User(
                username="Trần Thị B",
                email="tranthib@hotel.com",
                phone="098765432",
                password=hashed_pw,
                role=UserRole.CUSTOMER,
                is_verified=True
            )
            test_db.session.add(cust_b)
        else:
            cust_b.phone = "098765432"

        cust_c = test_db.session.query(User).filter_by(username="Lê Văn C").first()
        if not cust_c:
            cust_c = User(
                username="Lê Văn C",
                email="levanc@hotel.com",
                phone="0333444555",
                password=hashed_pw,
                role=UserRole.CUSTOMER,
                is_verified=True
            )
            test_db.session.add(cust_c)
        else:
            cust_c.phone = "0333444555"

        cust_d = test_db.session.query(User).filter_by(username="Phạm Văn D").first()
        if not cust_d:
            cust_d = User(
                username="Phạm Văn D",
                email="phamvand@hotel.com",
                phone="0777888999",
                password=hashed_pw,
                role=UserRole.CUSTOMER,
                is_verified=True
            )
            test_db.session.add(cust_d)
        else:
            cust_d.phone = "0777888999"

        test_db.session.commit()

        # 4. Loại phòng mẫu
        room_type = test_db.session.query(RoomType).filter_by(hotel_id=hotel_id, name="Phòng Standard Lễ Tân").first()
        if not room_type:
            room_type = RoomType(
                hotel_id=hotel_id,
                name="Phòng Standard Lễ Tân",
                description="Phòng Standard kiểm thử tìm kiếm đơn",
                base_price=Decimal("1000000.00"),
                max_occupancy=2,
                bed_count=1,
                bed_type="King Size",
                is_active=True
            )
            test_db.session.add(room_type)
            test_db.session.commit()
        room_type_id = room_type.id

        # 5. 4 Phòng vật lý
        def get_or_create_room(number, status):
            r = test_db.session.query(Room).filter_by(room_type_id=room_type_id, room_number=number).first()
            if not r:
                r = Room(room_type_id=room_type_id, room_number=number, floor=1, status=status, is_active=True)
                test_db.session.add(r)
                test_db.session.commit()
            else:
                r.status = status
                test_db.session.commit()
            return r

        r101 = get_or_create_room("P101", RoomStatus.OCCUPIED)
        r102 = get_or_create_room("P102", RoomStatus.AVAILABLE)
        r103 = get_or_create_room("P103", RoomStatus.OCCUPIED)
        r104 = get_or_create_room("P104", RoomStatus.AVAILABLE)

        # 6. 4 Đơn đặt phòng với ID 1, 2, 3, 4
        today = get_vn_time().date()

        b1 = Booking(
            id=1,
            user_id=cust_a.id,
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            check_in=today - timedelta(days=2),
            check_out=today + timedelta(days=2),
            total_price=Decimal("4000000.00"),
            status=BookingStatus.CONFIRMED
        )
        b2 = Booking(
            id=2,
            user_id=cust_b.id,
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            check_in=today,
            check_out=today + timedelta(days=2),
            total_price=Decimal("2000000.00"),
            status=BookingStatus.CONFIRMED
        )
        b3 = Booking(
            id=3,
            user_id=cust_c.id,
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            check_in=today - timedelta(days=1),
            check_out=today,
            total_price=Decimal("1000000.00"),
            status=BookingStatus.CONFIRMED
        )
        b4 = Booking(
            id=4,
            user_id=cust_d.id,
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            check_in=today + timedelta(days=5),
            check_out=today + timedelta(days=7),
            total_price=Decimal("2000000.00"),
            status=BookingStatus.CONFIRMED
        )
        test_db.session.add_all([b1, b2, b3, b4])
        test_db.session.commit()

        bd1 = BookingDetail(booking_id=1, room_id=r101.id, price_at_booking=room_type.base_price)
        bd2 = BookingDetail(booking_id=2, room_id=r102.id, price_at_booking=room_type.base_price)
        bd3 = BookingDetail(booking_id=3, room_id=r103.id, price_at_booking=room_type.base_price)
        bd4 = BookingDetail(booking_id=4, room_id=r104.id, price_at_booking=room_type.base_price)
        test_db.session.add_all([bd1, bd2, bd3, bd4])
        test_db.session.commit()

        seed_data = {
            "hotel_id": hotel_id,
            "room_type_id": room_type_id,
            "booking_ids": [1, 2, 3, 4]
        }

    yield seed_data

    # Teardown dọn dẹp sau khi tất cả test kết thúc
    with test_app.app_context():
        try:
            test_db.session.query(BookingDetail).filter(BookingDetail.booking_id.in_([1, 2, 3, 4])).delete(synchronize_session=False)
            test_db.session.query(Booking).filter(Booking.id.in_([1, 2, 3, 4])).delete(synchronize_session=False)
            test_db.session.commit()
        except Exception:
            test_db.session.rollback()


# ==============================================================================
# TEST CASES
# ==============================================================================

def test_tc3_access_denied_for_customer_role(live_server, driver, seed_reception_test_data):
    """
    TC3: Kiểm thử phân quyền truy cập:
    - Precondition: Đăng nhập tài khoản Customer (role=CUSTOMER).
    - Action: Truy cập trực tiếp URL /reception/bookings.
    - Assert: Bị từ chối truy cập (HTTP 403 / thông báo 'Không có quyền truy cập'),
      không hiển thị bảng điều khiển lễ tân.
    - Minh chứng: Chụp ảnh reception_tc3_access_denied.png.
    """
    login_user(driver, live_server.url, "test_customer", "123456")

    # Truy cập URL của Lễ tân
    driver.get(f"{live_server.url}/reception/bookings")

    wait = WebDriverWait(driver, 10)
    # Chờ trang lỗi 403 hiển thị
    wait.until(lambda d: "403" in d.page_source or "Forbidden" in d.page_source or "Không có quyền truy cập" in d.page_source)

    # Lưu ảnh minh chứng
    capture_screenshot(driver, "reception_tc3_access_denied.png")

    # Assert 1: Thông báo lỗi 403 và thông điệp chặn truy cập
    page_source = driver.page_source
    assert "403" in page_source or "Forbidden" in page_source, "Không tìm thấy mã lỗi 403 hoặc Forbidden trên giao diện!"
    assert any(msg in page_source for msg in ["Không có quyền truy cập", "Forbidden", "You don't have the permission"]), \
        "Giao diện không hiển thị thông báo lỗi chặn truy cập 403!"

    # Assert 2: Không hiển thị bảng hay bộ lọc lễ tân
    assert len(driver.find_elements(By.ID, "search-input")) == 0, "Giao diện vẫn hiển thị ô tìm kiếm lễ tân!"
    assert len(driver.find_elements(By.ID, "receptionTabsContent")) == 0, "Giao diện vẫn hiển thị nội dung phân hệ lễ tân!"
    time.sleep(1)


def test_tc2_priority_sorting_for_today_checkin_checkout(live_server, driver, seed_reception_test_data):
    """
    TC2: Kiểm thử sắp xếp ưu tiên đơn check-in/out trong ngày:
    - Precondition: Đăng nhập tài khoản Receptionist (role=RECEPTIONIST), mở danh sách đơn.
    - Action: Xem danh sách mặc định (không tìm kiếm / không lọc).
    - Assert: Đơn check-in hôm nay (BK002) và check-out hôm nay (BK003) được ưu tiên
      hiển thị ở các hàng đầu tiên trước đơn tương lai (BK004).
    - Minh chứng: Chụp ảnh reception_tc2_priority_sorting.png.
    """
    login_user(driver, live_server.url, "test_receptionist", "123456")
    navigate_to_bookings_tab(driver, live_server.url)

    wait = WebDriverWait(driver, 10)
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".booking-code-cell")))

    code_cells = driver.find_elements(By.CSS_SELECTOR, ".booking-code-cell")
    codes = [cell.text.strip() for cell in code_cells]

    # Assert 1: Các đơn mẫu xuất hiện đầy đủ
    assert "BK002" in codes, "Đơn BK002 (check-in hôm nay) không có trong danh sách!"
    assert "BK003" in codes, "Đơn BK003 (check-out hôm nay) không có trong danh sách!"
    assert "BK004" in codes, "Đơn BK004 (check-in tương lai) không có trong danh sách!"

    # Assert 2: BK002 và BK003 nằm ở 2 dòng đầu tiên (ưu tiên check-in/out hôm nay)
    assert set(codes[:2]) == {"BK002", "BK003"}, f"2 dòng đầu không phải là BK002 và BK003! Thực tế: {codes[:2]}"

    # Assert 3: BK004 (tương lai) nằm sau các đơn ưu tiên hôm nay
    assert codes.index("BK002") < codes.index("BK004"), "BK002 không được ưu tiên trước BK004!"
    assert codes.index("BK003") < codes.index("BK004"), "BK003 không được ưu tiên trước BK004!"

    # Lưu ảnh minh chứng
    capture_screenshot(driver, "reception_tc2_priority_sorting.png")
    time.sleep(1)


def test_tc12_filter_bookings_by_status(live_server, driver, seed_reception_test_data):
    """
    TC12: Kiểm thử bộ lọc trạng thái đơn:
    - Precondition: Đăng nhập Lễ tân, mở danh sách đơn.
    - Action: Chọn bộ lọc 'Đang sử dụng' (CHECKED_IN), bấm Lọc.
    - Assert: Bảng chỉ hiển thị đơn có phòng đang sử dụng (BK001, BK003);
      các đơn CONFIRMED chưa ở (BK002, BK004) bị ẩn hoàn toàn.
    - Minh chứng: Chụp ảnh reception_tc12_filter_status.png.
    """
    login_user(driver, live_server.url, "test_receptionist", "123456")
    navigate_to_bookings_tab(driver, live_server.url)

    wait = WebDriverWait(driver, 10)
    status_select_el = wait.until(EC.presence_of_element_located((By.ID, "status-filter")))
    select = Select(status_select_el)
    select.select_by_value("CHECKED_IN")

    search_btn = driver.find_element(By.ID, "search-btn")
    driver.execute_script("arguments[0].click();", search_btn)

    # Chờ danh sách tải lại sau khi lọc
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".booking-code-cell")))

    code_cells = driver.find_elements(By.CSS_SELECTOR, ".booking-code-cell")
    codes = [cell.text.strip() for cell in code_cells]

    # Assert 1: Chỉ BK001 và BK003 hiển thị
    assert set(codes) == {"BK001", "BK003"}, f"Danh sách sau lọc không khớp với {'BK001', 'BK003'}! Thực tế: {codes}"

    # Assert 2: Các đơn CONFIRMED (BK002, BK004) không được hiển thị
    assert "BK002" not in codes, "BK002 (chưa nhận phòng) vẫn hiển thị khi lọc 'Đang sử dụng'!"
    assert "BK004" not in codes, "BK004 (chưa nhận phòng) vẫn hiển thị khi lọc 'Đang sử dụng'!"

    # Assert 3: Nhãn trạng thái hiển thị đúng 'Đang sử dụng'
    status_badges = driver.find_elements(By.CSS_SELECTOR, ".status-cell")
    for badge in status_badges:
        assert "Đang sử dụng" in badge.text, f"Nhãn trạng thái không phải 'Đang sử dụng': {badge.text}"

    # Lưu ảnh minh chứng
    capture_screenshot(driver, "reception_tc12_filter_status.png")
    time.sleep(1)


@pytest.mark.parametrize("tc_id,keyword,expected_codes,screenshot_filename", [
    ("tc6_name", "Nguyễn Văn A", ["BK001"], "reception_tc6_search_name.png"),
    ("tc7_phone", "012345678", ["BK001"], "reception_tc7_search_phone.png"),
    ("tc8_not_found", "KhôngTồnTại999", [], "reception_tc8_search_not_found.png"),
    ("tc9_empty", "", ["BK001", "BK002", "BK003", "BK004"], "reception_tc9_search_empty.png"),
    ("tc10_partial", "Nguyễn", ["BK001"], "reception_tc10_search_partial.png"),
    ("tc11_whitespace", "  BK001  ", ["BK001"], "reception_tc11_search_whitespace.png"),
])
def test_search_bookings_scenarios(
    live_server, driver, seed_reception_test_data,
    tc_id, keyword, expected_codes, screenshot_filename
):
    """
    Parametrized Test Scenarios (TC6 - TC11):
    - TC6: Tìm kiếm theo tên khách hàng chính xác -> BK001
    - TC7: Tìm kiếm theo số điện thoại -> BK001
    - TC8: Tìm kiếm từ khóa không tồn tại -> Bảng rỗng, hiển thị 'Không tìm thấy thông tin đặt chỗ phù hợp'
    - TC9: Bỏ trống ô tìm kiếm -> Hiển thị toàn bộ danh sách đơn (BK001..BK004)
    - TC10: Tìm kiếm gần đúng/một phần tên -> BK001
    - TC11: Tìm kiếm có khoảng trắng thừa -> Hệ thống tự strip khoảng trắng và trả về BK001
    Mỗi kịch bản đều lưu ảnh chụp màn hình minh chứng riêng biệt vào screenshots/.
    """
    login_user(driver, live_server.url, "test_receptionist", "123456")
    navigate_to_bookings_tab(driver, live_server.url)

    wait = WebDriverWait(driver, 10)
    search_input = wait.until(EC.presence_of_element_located((By.ID, "search-input")))
    search_input.clear()
    if keyword:
        search_input.send_keys(keyword)

    search_btn = driver.find_element(By.ID, "search-btn")
    driver.execute_script("arguments[0].click();", search_btn)

    if not expected_codes:
        # Trường hợp không tìm thấy kết quả (TC8)
        empty_cell = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".empty-bookings-cell")))
        assert "Không tìm thấy thông tin đặt chỗ phù hợp" in empty_cell.text, \
            f"Thông báo bảng rỗng không đúng! Thực tế: {empty_cell.text}"
        booking_rows = driver.find_elements(By.CSS_SELECTOR, ".booking-row")
        assert len(booking_rows) == 0, f"Vẫn còn hàng hiển thị khi tìm kiếm không ra kết quả: {len(booking_rows)}"
    else:
        # Trường hợp có kết quả trả về
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".booking-code-cell")))
        code_cells = driver.find_elements(By.CSS_SELECTOR, ".booking-code-cell")
        actual_codes = [c.text.strip() for c in code_cells]
        assert set(actual_codes) == set(expected_codes), \
            f"[{tc_id}] Kết quả tìm kiếm cho '{keyword}' không khớp! Mong đợi: {expected_codes}, Thực tế: {actual_codes}"

    # Chụp và lưu ảnh minh chứng cho từng case
    capture_screenshot(driver, screenshot_filename)
    time.sleep(1)
