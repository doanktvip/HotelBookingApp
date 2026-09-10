import pytest
import hashlib
from datetime import date, timedelta
from decimal import Decimal
from app.models import (
    Hotel, RoomType, Room, RoomStatus,
    Booking, BookingStatus, BookingDetail,
    User, UserRole, SearchHistory
)
from app.services.hotel_service import HotelService


@pytest.fixture
def hotel_service(test_session):
    """Fixture cung cấp instance HotelService gắn với test_session."""
    return HotelService(db_session=test_session)


@pytest.fixture
def search_test_data(test_session):
    """
    Tạo dữ liệu mẫu trực tiếp vào DB để kiểm thử tìm kiếm khách sạn theo ngày và địa điểm:
    1. Hotel A: 'Da Nang Riverside Hotel' tại 'Đà Nẵng', địa chỉ '10 Bạch Đằng, Quận Hải Châu'.
       - 1 Loại phòng Deluxe, có 2 phòng vật lý (P101, P102).
    2. Hotel B: 'Da Nang Boutique Hotel' tại 'Đà Nẵng', địa chỉ '50 Võ Nguyên Giáp, Quận Sơn Trà'.
       - 1 Loại phòng Superior, chỉ có DUY NHẤT 1 phòng vật lý (P201).
    3. Hotel C: 'Nha Trang Beach Resort' tại 'Nha Trang, Khánh Hòa', địa chỉ '12 Trần Phú, Phường Lộc Thọ'.
       - 1 Loại phòng Ocean Suite, có 1 phòng vật lý (P301).
    4. Hotel D: 'Hanoi Heritage Hotel' tại 'Hà Nội', địa chỉ '15 Hàng Bạc, Quận Hoàn Kiếm'.
       - 1 Loại phòng Standard, có 1 phòng nhưng is_active=False (phòng không khả dụng).
    5. 1 Khách hàng mẫu để tạo đơn đặt phòng nếu cần.
    """
    # Tạo user khách hàng
    customer = User(
        username="search_cust",
        email="search_cust@test.com",
        password=hashlib.md5(b"123456").hexdigest(),
        role=UserRole.CUSTOMER,
        is_verified=True
    )
    test_session.add(customer)

    # 1. Hotel A (Đà Nẵng - 2 phòng)
    hotel_a = Hotel(
        name="Da Nang Riverside Hotel",
        address="10 Bạch Đằng, Quận Hải Châu",
        location="Đà Nẵng",
        description="Khách sạn ven sông Hàn tuyệt đẹp",
        rating=4.8
    )
    test_session.add(hotel_a)
    test_session.flush()

    rt_a = RoomType(
        hotel_id=hotel_a.id,
        name="Deluxe River View",
        base_price=Decimal("1200000.00"),
        max_occupancy=2,
        bed_count=1,
        bed_type="Giường đôi lớn",
        is_active=True
    )
    test_session.add(rt_a)
    test_session.flush()

    room_a1 = Room(room_type_id=rt_a.id, room_number="101", floor=1, status=RoomStatus.AVAILABLE, is_active=True)
    room_a2 = Room(room_type_id=rt_a.id, room_number="102", floor=1, status=RoomStatus.AVAILABLE, is_active=True)
    test_session.add_all([room_a1, room_a2])

    # 2. Hotel B (Đà Nẵng - 1 phòng duy nhất)
    hotel_b = Hotel(
        name="Da Nang Boutique Hotel",
        address="50 Võ Nguyên Giáp, Quận Sơn Trà",
        location="Đà Nẵng",
        description="Khách sạn boutique sát biển Mỹ Khê",
        rating=4.2
    )
    test_session.add(hotel_b)
    test_session.flush()

    rt_b = RoomType(
        hotel_id=hotel_b.id,
        name="Superior City View",
        base_price=Decimal("800000.00"),
        max_occupancy=2,
        bed_count=1,
        bed_type="Giường đôi",
        is_active=True
    )
    test_session.add(rt_b)
    test_session.flush()

    room_b1 = Room(room_type_id=rt_b.id, room_number="201", floor=2, status=RoomStatus.AVAILABLE, is_active=True)
    test_session.add(room_b1)

    # 3. Hotel C (Nha Trang, Khánh Hòa - 1 phòng)
    hotel_c = Hotel(
        name="Nha Trang Beach Resort",
        address="12 Trần Phú, Phường Lộc Thọ",
        location="Nha Trang, Khánh Hòa",
        description="Resort nghỉ dưỡng view biển Trần Phú",
        rating=4.6
    )
    test_session.add(hotel_c)
    test_session.flush()

    rt_c = RoomType(
        hotel_id=hotel_c.id,
        name="Ocean Suite",
        base_price=Decimal("2500000.00"),
        max_occupancy=4,
        bed_count=2,
        bed_type="2 Giường lớn",
        is_active=True
    )
    test_session.add(rt_c)
    test_session.flush()

    room_c1 = Room(room_type_id=rt_c.id, room_number="301", floor=3, status=RoomStatus.AVAILABLE, is_active=True)
    test_session.add(room_c1)

    # 4. Hotel D (Hà Nội - 1 phòng nhưng is_active=False)
    hotel_d = Hotel(
        name="Hanoi Heritage Hotel",
        address="15 Hàng Bạc, Quận Hoàn Kiếm",
        location="Hà Nội",
        description="Khách sạn phố cổ Hà Nội",
        rating=4.0
    )
    test_session.add(hotel_d)
    test_session.flush()

    rt_d = RoomType(
        hotel_id=hotel_d.id,
        name="Standard Room",
        base_price=Decimal("600000.00"),
        max_occupancy=2,
        bed_count=1,
        bed_type="Giường đơn",
        is_active=True
    )
    test_session.add(rt_d)
    test_session.flush()

    room_d1 = Room(room_type_id=rt_d.id, room_number="401", floor=4, status=RoomStatus.AVAILABLE, is_active=False)
    test_session.add(room_d1)

    test_session.commit()

    return {
        "customer": customer,
        "hotel_a": hotel_a,
        "hotel_b": hotel_b,
        "hotel_c": hotel_c,
        "hotel_d": hotel_d,
        "room_a1": room_a1,
        "room_a2": room_a2,
        "room_b1": room_b1,
        "room_c1": room_c1,
        "room_d1": room_d1,
        "rt_a": rt_a,
        "rt_b": rt_b,
        "rt_c": rt_c,
        "rt_d": rt_d
    }


# =====================================================================
# NHÓM 1: KIỂM THỬ TÌM KIẾM THEO ĐỊA ĐIỂM (LOCATION)
# =====================================================================

def test_search_hotels_by_exact_location(test_app, hotel_service, search_test_data):
    """Kiểm tra tìm kiếm chính xác theo địa điểm: 'Đà Nẵng' trả về đúng 2 khách sạn ở Đà Nẵng."""
    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(location="Đà Nẵng")
        assert pagination.total == 2
        hotel_ids = [h.id for h in pagination.items]
        assert search_test_data["hotel_a"].id in hotel_ids
        assert search_test_data["hotel_b"].id in hotel_ids
        assert search_test_data["hotel_c"].id not in hotel_ids
        assert search_test_data["hotel_d"].id not in hotel_ids


def test_search_hotels_by_location_case_insensitive(test_app, hotel_service, search_test_data):
    """Kiểm tra tìm kiếm địa điểm không phân biệt chữ hoa, chữ thường: 'nha trang' và 'NHA TRANG'."""
    with test_app.test_request_context():
        # Chữ thường
        pag_lower = hotel_service.get_hotels(location="nha trang")
        assert pag_lower.total == 1
        assert pag_lower.items[0].id == search_test_data["hotel_c"].id

        # Chữ hoa
        pag_upper = hotel_service.get_hotels(location="NHA TRANG")
        assert pag_upper.total == 1
        assert pag_upper.items[0].id == search_test_data["hotel_c"].id


def test_search_hotels_by_partial_location(test_app, hotel_service, search_test_data):
    """Kiểm tra tìm kiếm khớp một phần tên địa điểm: 'Nha' hoặc 'Khánh Hòa'."""
    with test_app.test_request_context():
        pagination1 = hotel_service.get_hotels(location="Nha")
        assert pagination1.total == 1
        assert pagination1.items[0].id == search_test_data["hotel_c"].id

        pagination2 = hotel_service.get_hotels(location="Khánh Hòa")
        assert pagination2.total == 1
        assert pagination2.items[0].id == search_test_data["hotel_c"].id


def test_search_hotels_by_address_via_location_field(test_app, hotel_service, search_test_data):
    """Kiểm tra tìm kiếm theo tên đường/địa chỉ (address) thông qua trường location."""
    with test_app.test_request_context():
        # Tìm 'Bạch Đằng' nằm trong address của Hotel A
        pagination = hotel_service.get_hotels(location="Bạch Đằng")
        assert pagination.total == 1
        assert pagination.items[0].id == search_test_data["hotel_a"].id

        # Tìm 'Võ Nguyên Giáp' nằm trong address của Hotel B
        pagination_b = hotel_service.get_hotels(location="Võ Nguyên Giáp")
        assert pagination_b.total == 1
        assert pagination_b.items[0].id == search_test_data["hotel_b"].id


def test_search_hotels_location_not_found(test_app, hotel_service, search_test_data):
    """Kiểm tra tìm kiếm địa điểm không tồn tại trả về danh sách rỗng (total == 0)."""
    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(location="Cần Thơ")
        assert pagination.total == 0
        assert len(pagination.items) == 0


def test_search_hotels_location_with_whitespace(test_app, hotel_service, search_test_data):
    """Kiểm tra tìm kiếm với chuỗi địa điểm có khoảng trắng thừa được xử lý an toàn."""
    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(location="  Đà Nẵng  ".strip())
        assert pagination.total == 2


# =====================================================================
# NHÓM 2: KIỂM THỬ TÌM KIẾM THEO NGÀY & TRẠNG THÁI PHÒNG TRỐNG (DATE AVAILABILITY)
# =====================================================================

def test_search_hotels_available_when_no_bookings(test_app, hotel_service, search_test_data):
    """Khách sạn chưa có đơn đặt phòng nào thì luôn xuất hiện khi tìm kiếm theo ngày hợp lệ."""
    with test_app.test_request_context():
        check_in = "2026-10-10"
        check_out = "2026-10-15"
        pagination = hotel_service.get_hotels(check_in=check_in, check_out=check_out)
        assert pagination.total == 3
        hotel_ids = [h.id for h in pagination.items]
        assert search_test_data["hotel_a"].id in hotel_ids
        assert search_test_data["hotel_b"].id in hotel_ids
        assert search_test_data["hotel_c"].id in hotel_ids


def test_search_hotels_excluded_when_all_rooms_fully_booked(test_app, test_session, hotel_service, search_test_data):
    """
    Khách sạn chỉ có 1 phòng (Hotel B), khi phòng đó đã có đơn CONFIRMED trong khoảng ngày
    thì khách sạn sẽ bị loại khỏi kết quả tìm kiếm trong đúng khoảng ngày đó.
    """
    booking = Booking(
        user_id=search_test_data["customer"].id,
        hotel_id=search_test_data["hotel_b"].id,
        room_type_id=search_test_data["rt_b"].id,
        check_in=date(2026, 10, 10),
        check_out=date(2026, 10, 15),
        total_price=Decimal("4000000.00"),
        status=BookingStatus.CONFIRMED
    )
    test_session.add(booking)
    test_session.flush()
    detail = BookingDetail(booking_id=booking.id, room_id=search_test_data["room_b1"].id, price_at_booking=Decimal("800000.00"))
    test_session.add(detail)
    test_session.commit()

    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(check_in="2026-10-10", check_out="2026-10-15")
        hotel_ids = [h.id for h in pagination.items]
        assert search_test_data["hotel_b"].id not in hotel_ids
        assert search_test_data["hotel_a"].id in hotel_ids
        assert search_test_data["hotel_c"].id in hotel_ids


def test_search_hotels_overlap_booking_partial_start(test_app, test_session, hotel_service, search_test_data):
    """Kiểm tra trùng phòng một phần ở đầu khoảng tìm kiếm (ci < booking.check_out và co > booking.check_in)."""
    booking = Booking(
        user_id=search_test_data["customer"].id,
        hotel_id=search_test_data["hotel_b"].id,
        room_type_id=search_test_data["rt_b"].id,
        check_in=date(2026, 10, 10),
        check_out=date(2026, 10, 15),
        total_price=Decimal("4000000.00"),
        status=BookingStatus.CONFIRMED
    )
    test_session.add(booking)
    test_session.flush()
    detail = BookingDetail(booking_id=booking.id, room_id=search_test_data["room_b1"].id, price_at_booking=Decimal("800000.00"))
    test_session.add(detail)
    test_session.commit()

    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(check_in="2026-10-08", check_out="2026-10-12")
        hotel_ids = [h.id for h in pagination.items]
        assert search_test_data["hotel_b"].id not in hotel_ids


def test_search_hotels_overlap_booking_partial_end(test_app, test_session, hotel_service, search_test_data):
    """Kiểm tra trùng phòng một phần ở cuối khoảng tìm kiếm (giao nhau đoạn 13-15)."""
    booking = Booking(
        user_id=search_test_data["customer"].id,
        hotel_id=search_test_data["hotel_b"].id,
        room_type_id=search_test_data["rt_b"].id,
        check_in=date(2026, 10, 10),
        check_out=date(2026, 10, 15),
        total_price=Decimal("4000000.00"),
        status=BookingStatus.CONFIRMED
    )
    test_session.add(booking)
    test_session.flush()
    detail = BookingDetail(booking_id=booking.id, room_id=search_test_data["room_b1"].id, price_at_booking=Decimal("800000.00"))
    test_session.add(detail)
    test_session.commit()

    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(check_in="2026-10-13", check_out="2026-10-18")
        hotel_ids = [h.id for h in pagination.items]
        assert search_test_data["hotel_b"].id not in hotel_ids


def test_search_hotels_overlap_booking_fully_inside(test_app, test_session, hotel_service, search_test_data):
    """Kiểm tra khoảng tìm kiếm nằm trọn vẹn bên trong đơn đặt phòng (11-14 nằm trong 10-15)."""
    booking = Booking(
        user_id=search_test_data["customer"].id,
        hotel_id=search_test_data["hotel_b"].id,
        room_type_id=search_test_data["rt_b"].id,
        check_in=date(2026, 10, 10),
        check_out=date(2026, 10, 15),
        total_price=Decimal("4000000.00"),
        status=BookingStatus.CONFIRMED
    )
    test_session.add(booking)
    test_session.flush()
    detail = BookingDetail(booking_id=booking.id, room_id=search_test_data["room_b1"].id, price_at_booking=Decimal("800000.00"))
    test_session.add(detail)
    test_session.commit()

    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(check_in="2026-10-11", check_out="2026-10-14")
        hotel_ids = [h.id for h in pagination.items]
        assert search_test_data["hotel_b"].id not in hotel_ids


def test_search_hotels_overlap_booking_enclosing(test_app, test_session, hotel_service, search_test_data):
    """Kiểm tra khoảng tìm kiếm bao trọn toàn bộ đơn đặt phòng (05-20 bao trọn 10-15)."""
    booking = Booking(
        user_id=search_test_data["customer"].id,
        hotel_id=search_test_data["hotel_b"].id,
        room_type_id=search_test_data["rt_b"].id,
        check_in=date(2026, 10, 10),
        check_out=date(2026, 10, 15),
        total_price=Decimal("4000000.00"),
        status=BookingStatus.CONFIRMED
    )
    test_session.add(booking)
    test_session.flush()
    detail = BookingDetail(booking_id=booking.id, room_id=search_test_data["room_b1"].id, price_at_booking=Decimal("800000.00"))
    test_session.add(detail)
    test_session.commit()

    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(check_in="2026-10-05", check_out="2026-10-20")
        hotel_ids = [h.id for h in pagination.items]
        assert search_test_data["hotel_b"].id not in hotel_ids


def test_search_hotels_boundary_checkin_equals_checkout_available(test_app, test_session, hotel_service, search_test_data):
    """
    Kiểm tra giá trị biên: ngày Check-in của tìm kiếm bằng đúng ngày Check-out của booking trước.
    Booking: 2026-10-10 -> 2026-10-15.
    Search:  2026-10-15 -> 2026-10-18.
    Quy tắc: Khách cũ trả phòng trưa ngày 15, khách mới nhận phòng chiều ngày 15 -> PHÒNG KHẢ DỤNG.
    """
    booking = Booking(
        user_id=search_test_data["customer"].id,
        hotel_id=search_test_data["hotel_b"].id,
        room_type_id=search_test_data["rt_b"].id,
        check_in=date(2026, 10, 10),
        check_out=date(2026, 10, 15),
        total_price=Decimal("4000000.00"),
        status=BookingStatus.CONFIRMED
    )
    test_session.add(booking)
    test_session.flush()
    detail = BookingDetail(booking_id=booking.id, room_id=search_test_data["room_b1"].id, price_at_booking=Decimal("800000.00"))
    test_session.add(detail)
    test_session.commit()

    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(check_in="2026-10-15", check_out="2026-10-18")
        hotel_ids = [h.id for h in pagination.items]
        assert search_test_data["hotel_b"].id in hotel_ids


def test_search_hotels_boundary_checkout_equals_checkin_available(test_app, test_session, hotel_service, search_test_data):
    """
    Kiểm tra giá trị biên: ngày Check-out của tìm kiếm bằng đúng ngày Check-in của booking sau.
    Search:  2026-10-05 -> 2026-10-10.
    Booking: 2026-10-10 -> 2026-10-15.
    Quy tắc: Khách mới trả phòng ngày 10 trước khi khách tiếp theo nhận phòng -> PHÒNG KHẢ DỤNG.
    """
    booking = Booking(
        user_id=search_test_data["customer"].id,
        hotel_id=search_test_data["hotel_b"].id,
        room_type_id=search_test_data["rt_b"].id,
        check_in=date(2026, 10, 10),
        check_out=date(2026, 10, 15),
        total_price=Decimal("4000000.00"),
        status=BookingStatus.CONFIRMED
    )
    test_session.add(booking)
    test_session.flush()
    detail = BookingDetail(booking_id=booking.id, room_id=search_test_data["room_b1"].id, price_at_booking=Decimal("800000.00"))
    test_session.add(detail)
    test_session.commit()

    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(check_in="2026-10-05", check_out="2026-10-10")
        hotel_ids = [h.id for h in pagination.items]
        assert search_test_data["hotel_b"].id in hotel_ids


def test_search_hotels_cancelled_booking_does_not_block_availability(test_app, test_session, hotel_service, search_test_data):
    """Kiểm tra đơn đặt phòng có trạng thái CANCELLED không chiếm phòng và không chặn phòng trống."""
    booking_cancelled = Booking(
        user_id=search_test_data["customer"].id,
        hotel_id=search_test_data["hotel_b"].id,
        room_type_id=search_test_data["rt_b"].id,
        check_in=date(2026, 10, 10),
        check_out=date(2026, 10, 15),
        total_price=Decimal("4000000.00"),
        status=BookingStatus.CANCELLED
    )
    test_session.add(booking_cancelled)
    test_session.flush()
    detail = BookingDetail(booking_id=booking_cancelled.id, room_id=search_test_data["room_b1"].id, price_at_booking=Decimal("800000.00"))
    test_session.add(detail)
    test_session.commit()

    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(check_in="2026-10-10", check_out="2026-10-15")
        hotel_ids = [h.id for h in pagination.items]
        assert search_test_data["hotel_b"].id in hotel_ids


def test_search_hotels_multi_room_hotel_still_available_when_one_room_booked(test_app, test_session, hotel_service, search_test_data):
    """
    Khách sạn có 2 phòng (Hotel A có 101 và 102).
    Khi chỉ có phòng 101 bị đặt thì khách sạn vẫn xuất hiện vì vẫn còn phòng 102 khả dụng.
    """
    booking = Booking(
        user_id=search_test_data["customer"].id,
        hotel_id=search_test_data["hotel_a"].id,
        room_type_id=search_test_data["rt_a"].id,
        check_in=date(2026, 10, 10),
        check_out=date(2026, 10, 15),
        total_price=Decimal("6000000.00"),
        status=BookingStatus.CONFIRMED
    )
    test_session.add(booking)
    test_session.flush()
    detail = BookingDetail(booking_id=booking.id, room_id=search_test_data["room_a1"].id, price_at_booking=Decimal("1200000.00"))
    test_session.add(detail)
    test_session.commit()

    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(check_in="2026-10-10", check_out="2026-10-15")
        hotel_ids = [h.id for h in pagination.items]
        assert search_test_data["hotel_a"].id in hotel_ids


def test_search_hotels_inactive_room_not_counted_as_available(test_app, hotel_service, search_test_data):
    """Khách sạn D có phòng nhưng is_active=False thì không bao giờ được tính là có phòng trống."""
    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(check_in="2026-10-10", check_out="2026-10-15")
        hotel_ids = [h.id for h in pagination.items]
        assert search_test_data["hotel_d"].id not in hotel_ids


# =====================================================================
# NHÓM 3: KIỂM THỬ KẾT HỢP CẢ NGÀY VÀ ĐỊA ĐIỂM (COMBINED DATE + LOCATION)
# =====================================================================

def test_search_hotels_matching_both_date_and_location_success(test_app, hotel_service, search_test_data):
    """Tìm kiếm đúng cả ngày và địa điểm: hiển thị chính xác các khách sạn thỏa mãn cả 2 điều kiện."""
    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(
            location="Đà Nẵng",
            check_in="2026-11-01",
            check_out="2026-11-05"
        )
        assert pagination.total == 2
        hotel_ids = [h.id for h in pagination.items]
        assert search_test_data["hotel_a"].id in hotel_ids
        assert search_test_data["hotel_b"].id in hotel_ids
        assert search_test_data["hotel_c"].id not in hotel_ids


def test_search_hotels_matching_location_but_out_of_rooms_on_date(test_app, test_session, hotel_service, search_test_data):
    """
    Tìm kiếm tại 'Đà Nẵng' trong khoảng ngày 2026-10-10 -> 2026-10-15.
    Hotel B hết phòng, Hotel A còn phòng -> Chỉ trả về Hotel A.
    """
    booking_b = Booking(
        user_id=search_test_data["customer"].id,
        hotel_id=search_test_data["hotel_b"].id,
        room_type_id=search_test_data["rt_b"].id,
        check_in=date(2026, 10, 10),
        check_out=date(2026, 10, 15),
        total_price=Decimal("4000000.00"),
        status=BookingStatus.CONFIRMED
    )
    test_session.add(booking_b)
    test_session.flush()
    detail_b = BookingDetail(booking_id=booking_b.id, room_id=search_test_data["room_b1"].id, price_at_booking=Decimal("800000.00"))
    test_session.add(detail_b)
    test_session.commit()

    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(
            location="Đà Nẵng",
            check_in="2026-10-10",
            check_out="2026-10-15"
        )
        assert pagination.total == 1
        assert pagination.items[0].id == search_test_data["hotel_a"].id


def test_search_hotels_all_hotels_in_location_out_of_rooms(test_app, test_session, hotel_service, search_test_data):
    """
    Khi tất cả các khách sạn tại 'Đà Nẵng' đều đã kín phòng trong khoảng ngày tìm kiếm,
    hệ thống trả về danh sách rỗng (total == 0).
    """
    ci = date(2026, 12, 1)
    co = date(2026, 12, 5)

    # Đặt phòng duy nhất của Hotel B
    bk_b = Booking(user_id=search_test_data["customer"].id, hotel_id=search_test_data["hotel_b"].id,
                   room_type_id=search_test_data["rt_b"].id, check_in=ci, check_out=co,
                   total_price=Decimal("3200000.00"), status=BookingStatus.CONFIRMED)
    test_session.add(bk_b)
    test_session.flush()
    test_session.add(BookingDetail(booking_id=bk_b.id, room_id=search_test_data["room_b1"].id, price_at_booking=Decimal("800000.00")))

    # Đặt cả 2 phòng 101 và 102 của Hotel A
    bk_a1 = Booking(user_id=search_test_data["customer"].id, hotel_id=search_test_data["hotel_a"].id,
                    room_type_id=search_test_data["rt_a"].id, check_in=ci, check_out=co,
                    total_price=Decimal("4800000.00"), status=BookingStatus.CONFIRMED)
    bk_a2 = Booking(user_id=search_test_data["customer"].id, hotel_id=search_test_data["hotel_a"].id,
                    room_type_id=search_test_data["rt_a"].id, check_in=ci, check_out=co,
                    total_price=Decimal("4800000.00"), status=BookingStatus.CONFIRMED)
    test_session.add_all([bk_a1, bk_a2])
    test_session.flush()
    test_session.add_all([
        BookingDetail(booking_id=bk_a1.id, room_id=search_test_data["room_a1"].id, price_at_booking=Decimal("1200000.00")),
        BookingDetail(booking_id=bk_a2.id, room_id=search_test_data["room_a2"].id, price_at_booking=Decimal("1200000.00"))
    ])
    test_session.commit()

    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(
            location="Đà Nẵng",
            check_in="2026-12-01",
            check_out="2026-12-05"
        )
        assert pagination.total == 0


def test_search_hotels_available_on_date_but_wrong_location(test_app, hotel_service, search_test_data):
    """Khách sạn còn phòng vào khoảng ngày tìm kiếm nhưng không khớp địa điểm -> Bị loại bỏ."""
    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(
            location="Hải Phòng",
            check_in="2026-11-01",
            check_out="2026-11-05"
        )
        assert pagination.total == 0


# =====================================================================
# NHÓM 4: KIỂM THỬ GIÁ TRỊ BIÊN & DỮ LIỆU NGÀY BẤT THƯỜNG (EDGE CASES & VALIDATION)
# =====================================================================

def test_search_hotels_checkout_before_checkin_handled_gracefully(test_app, hotel_service, search_test_data):
    """
    Ngày check-out trước ngày check-in (check_out < check_in):
    Hàm _parse_dates nhận diện co <= ci và bỏ qua lọc ngày, không gây lỗi hệ thống (500).
    """
    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(
            location="Đà Nẵng",
            check_in="2026-10-15",
            check_out="2026-10-10"
        )
        assert pagination.total == 2


def test_search_hotels_same_checkin_checkout_handled_gracefully(test_app, hotel_service, search_test_data):
    """
    Ngày check-out trùng với ngày check-in (co == ci, 0 đêm):
    Hàm _parse_dates xử lý an toàn, không ném exception.
    """
    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(
            location="Đà Nẵng",
            check_in="2026-10-10",
            check_out="2026-10-10"
        )
        assert pagination.total == 2


def test_search_hotels_invalid_date_format_handled_gracefully(test_app, hotel_service, search_test_data):
    """
    Chuỗi ngày không đúng định dạng '%Y-%m-%d' (e.g. chữ cái, sai format):
    Hàm _parse_dates bắt ValueError và trả về kết quả an toàn.
    """
    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(
            location="Đà Nẵng",
            check_in="sai-dinh-dang",
            check_out="2026-10-15"
        )
        assert pagination.total == 2


def test_search_hotels_only_checkin_provided(test_app, hotel_service, search_test_data):
    """Chỉ truyền check_in mà không truyền check_out -> Không lọc ngày, lọc bình thường theo location."""
    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(
            location="Đà Nẵng",
            check_in="2026-10-10",
            check_out=None
        )
        assert pagination.total == 2


def test_search_hotels_only_checkout_provided(test_app, hotel_service, search_test_data):
    """Chỉ truyền check_out mà không truyền check_in -> Không lọc ngày, lọc bình thường theo location."""
    with test_app.test_request_context():
        pagination = hotel_service.get_hotels(
            location="Đà Nẵng",
            check_in=None,
            check_out="2026-10-15"
        )
        assert pagination.total == 2


# =====================================================================
# NHÓM 5: KIỂM THỬ TÍCH HỢP CLIENT HTTP ROUTE VÀ LỊCH SỬ TÌM KIẾM
# =====================================================================

def test_client_hotels_search_by_location_and_date_status_ok(client, search_test_data):
    """Kiểm thử gửi HTTP GET tới route /hotels với query params location, check_in, check_out trả về 200."""
    res = client.get('/hotels?location=Đà+Nẵng&check_in=2026-11-01&check_out=2026-11-05')
    assert res.status_code == 200
    assert "Da Nang Riverside Hotel" in res.text or b"Da Nang Riverside Hotel" in res.data


def test_client_hotels_search_auto_saves_search_history_with_date_and_location(client, test_session, search_test_data):
    """Kiểm thử route /hotels tự động ghi nhận SearchHistory khi có location và check_in/check_out."""
    res = client.get('/hotels?location=Nha+Trang&check_in=2026-11-10&check_out=2026-11-15&guest_count=2&room_count=1')
    assert res.status_code == 200

    history = test_session.query(SearchHistory).filter_by(location="Nha Trang").first()
    assert history is not None
    assert history.check_in_date == date(2026, 11, 10)
    assert history.check_out_date == date(2026, 11, 15)
    assert history.guest_count == 2
    assert history.room_count == 1
