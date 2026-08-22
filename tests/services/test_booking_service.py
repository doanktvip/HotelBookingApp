import pytest
from datetime import date, timedelta
from flask import g
from app.services.booking_service import BookingService
from app.models import BookingStatus, BookingDetail

@pytest.fixture
def booking_service(test_session):
    """Khởi tạo service (sẽ tự động dùng test_db do đã cấu hình trong conftest.py)"""
    return BookingService(db_session=test_session)

def test_parse_and_validate_dates(test_app, booking_service):
    """Test parse ngày trong Request Context thật"""
    with test_app.test_request_context():
        # Kiểm tra logic: nếu checkout trước checkin thì checkout = checkin + 1 ngày
        check_in, check_out = booking_service.parse_and_validate_dates("2026-08-25", "2026-08-20")
        
        assert check_in == date(2026, 8, 25)
        assert check_out == date(2026, 8, 26)

def test_create_booking_success(test_app, booking_service, sample_customer, sample_room_type, sample_rooms):
    """Test tạo đặt phòng thành công với Database (Integration Test)"""
    with test_app.test_request_context():
        # Gán biến global cho request
        g.tax_fee = 10
        g.max_rooms_per_booking = 5
        
        check_in = date.today() + timedelta(days=10)
        check_out = check_in + timedelta(days=12) # 2 đêm
        quantity = 2 # Đặt 2 phòng (có sẵn 3 phòng trong sample_rooms)
        
        booking = booking_service.create_booking(
            user_id=sample_customer.id,
            hotel_id=sample_room_type.hotel_id,
            room_type_id=sample_room_type.id,
            check_in=check_in,
            check_out=check_out,
            quantity=quantity,
            price_at_booking=sample_room_type.base_price
        )
        
        # Kiểm tra xem booking có được lưu vào DB không
        assert booking.id is not None
        assert booking.status == BookingStatus.CONFIRMED
        assert booking.user_id == sample_customer.id
        
        # Kiểm tra xem có 2 chi tiết phòng được tạo không
        details = booking_service.db.query(BookingDetail).filter_by(booking_id=booking.id).all()
        assert len(details) == 2

def test_create_booking_not_enough_rooms(test_app, booking_service, sample_customer, sample_room_type, sample_rooms):
    """Test lỗi khi số lượng đặt lớn hơn số lượng phòng trống thực tế"""
    with test_app.test_request_context():
        g.tax_fee = 10
        g.max_rooms_per_booking = 5
        
        check_in = date.today() + timedelta(days=10)
        check_out = check_in + timedelta(days=12)
        
        # sample_rooms chỉ có 3 phòng, nếu khách đặt 4 phòng sẽ báo lỗi
        with pytest.raises(ValueError, match="Chỉ còn 3 phòng trống trong khoảng thời gian này."):
            booking_service.create_booking(
                user_id=sample_customer.id,
                hotel_id=sample_room_type.hotel_id,
                room_type_id=sample_room_type.id,
                check_in=check_in,
                check_out=check_out,
                quantity=4,
                price_at_booking=sample_room_type.base_price
            )

def test_cancel_user_booking_late(test_app, booking_service, sample_booking):
    """Test trường hợp quá thời hạn hủy phòng (Chính sách 3 ngày, nhưng đặt phòng là ngày mai)"""
    with test_app.test_request_context():
        # sample_booking có check_in = ngày mai, trong khi chính sách của hotel là 3 ngày.
        # Nên thuộc tính can_cancel sẽ là False
        with pytest.raises(ValueError, match="Đã quá thời hạn hủy phòng theo chính sách của khách sạn."):
            booking_service.cancel_user_booking(
                booking_id=sample_booking.id,
                user_id=sample_booking.user_id
            )
