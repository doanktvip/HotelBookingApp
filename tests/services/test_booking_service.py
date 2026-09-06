import pytest
from datetime import date, timedelta
from flask import g
from app.services.booking_service import BookingService
from app.models import BookingStatus, BookingDetail
import base64
import json
from unittest.mock import patch
from app.models import Room, RoomStatus, Payment, RoomType
from decimal import Decimal
from app.models import Booking
from app.models import RefundLog


@pytest.fixture
def booking_service(test_session):
    """Khởi tạo service (sẽ tự động dùng test_db do đã cấu hình trong conftest.py)"""
    return BookingService(db_session=test_session)

def test_parse_and_validate_dates(test_app, booking_service):
    """Test parse ngày trong Request Context thật"""
    with test_app.test_request_context():
        # Kiểm tra logic: nếu checkout trước checkin thì checkout = checkin + 1 ngày
        # Sử dụng ngày tương lai để tránh bị auto-correct về today
        check_in_str = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")
        check_out_str = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
        
        check_in, check_out = booking_service.parse_and_validate_dates(check_in_str, check_out_str)
        
        assert check_in == date.today() + timedelta(days=10)
        assert check_out == date.today() + timedelta(days=11)

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

# ==============================================================================
# GROUP 4 & 5: THANH TOÁN VÀ PHÂN BỔ PHÒNG (TC20 - TC26)
# =============================================================================

def get_base64_extra_data(booking_data):
    json_str = json.dumps(booking_data)
    return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

@pytest.fixture(scope='function')
def ipn_test_setup(test_session, sample_hotel, sample_customer):
    """Setup dữ liệu cho các test IPN"""
    rt = RoomType(hotel=sample_hotel, name="Room Type IPN", base_price=Decimal("1000000"), max_occupancy=2, bed_count=1)
    test_session.add(rt)
    test_session.commit()
    
    rooms = [
        Room(room_type=rt, room_number="IPN1", status=RoomStatus.AVAILABLE),
        Room(room_type=rt, room_number="IPN2", status=RoomStatus.AVAILABLE),
        Room(room_type=rt, room_number="IPN3", status=RoomStatus.AVAILABLE)
    ]
    test_session.add_all(rooms)
    test_session.commit()
    
    check_in = date.today() + timedelta(days=1)
    check_out = date.today() + timedelta(days=2)
    
    booking_data = {
        'user_id': sample_customer.id,
        'hotel_id': sample_hotel.id,
        'room_type_id': rt.id,
        'check_in': check_in.strftime('%d/%m/%Y'),
        'check_out': check_out.strftime('%d/%m/%Y'),
        'quantity': 2,
        'total_price': float(rt.base_price * 2 * 1),
        'price_at_booking': float(rt.base_price)
    }
    
    return rt, booking_data

@patch('app.routes.booking.MoMoService.verify_ipn_signature', return_value=True)
def test_tc20_tc24_tc25_valid_ipn_success(mock_verify, test_client, ipn_test_setup, test_session):
    """
    TC20: Tạo Booking và Payment thành công
    TC24: Tạo booking đúng số lượng phòng đã chọn
    TC25: Booking được tạo ở trạng thái CONFIRMED
    """
    rt, booking_data = ipn_test_setup
    extra_data = get_base64_extra_data(booking_data)
    
    ipn_payload = {
        'resultCode': 0,
        'extraData': extra_data,
        'amount': 2000000,
        'transId': 'TRANS_123',
        'orderId': 'ORDER_123'
    }
    
    response = test_client.post('/booking/momo-ipn', json=ipn_payload)
    assert response.status_code == 204
    
    # Kiểm tra DB
    booking = test_session.query(Booking).filter_by(room_type_id=rt.id).first()
    assert booking is not None
    assert booking.status.name == 'CONFIRMED' # TC25
    
    payment = test_session.query(Payment).filter_by(booking_id=booking.id).first()
    assert payment is not None
    assert payment.transaction_id == 'TRANS_123'
    assert payment.status.name == 'SUCCESS'
    
    details = test_session.query(BookingDetail).filter_by(booking_id=booking.id).all()
    assert len(details) == 2 # TC24 (quantity = 2)

@patch('app.routes.booking.MoMoService.verify_ipn_signature', return_value=True)
def test_tc21_duplicate_ipn(mock_verify, test_client, ipn_test_setup, test_session):
    """TC21: Không tạo booking trùng khi MoMo gửi lại IPN cùng transaction_id"""
    rt, booking_data = ipn_test_setup
    extra_data = get_base64_extra_data(booking_data)
    
    ipn_payload = {
        'resultCode': 0,
        'extraData': extra_data,
        'amount': 2000000,
        'transId': 'TRANS_DUPLICATE',
        'orderId': 'ORDER_DUP'
    }
    
    # Lần 1
    test_client.post('/booking/momo-ipn', json=ipn_payload)
    
    # Lần 2 (trùng)
    test_client.post('/booking/momo-ipn', json=ipn_payload)
    
    # Chỉ có 1 booking và 1 payment
    bookings = test_session.query(Booking).filter_by(room_type_id=rt.id).all()
    payments = test_session.query(Payment).filter_by(transaction_id='TRANS_DUPLICATE').all()
    
    assert len(bookings) == 1
    assert len(payments) == 1

@patch('app.routes.booking.MoMoService.verify_ipn_signature', return_value=True)
def test_tc22_insufficient_amount(mock_verify, test_client, ipn_test_setup, test_session):
    """TC22: Xử lý thanh toán không đủ số tiền bằng lỗi và không xác nhận booking"""
    rt, booking_data = ipn_test_setup
    extra_data = get_base64_extra_data(booking_data)
    
    ipn_payload = {
        'resultCode': 0,
        'extraData': extra_data,
        'amount': 1500000, # < 2000000 (Thiếu tiền)
        'transId': 'TRANS_SHORT',
        'orderId': 'ORDER_SHORT'
    }
    
    test_client.post('/booking/momo-ipn', json=ipn_payload)
    
    # Sẽ rollback, không tạo booking
    booking = test_session.query(Booking).filter_by(room_type_id=rt.id).first()
    assert booking is None
    
    # RefundLog được tạo
    refund = test_session.query(RefundLog).filter_by(trans_id='TRANS_SHORT').first()
    assert refund is not None
    assert "số tiền thanh toán không đủ" in refund.reason.lower() or "không đủ" in refund.reason.lower()

@patch('app.routes.booking.MoMoService.verify_ipn_signature', return_value=True)
def test_tc23_tc26_room_not_available(mock_verify, test_client, ipn_test_setup, test_session):
    """
    TC23: Hoàn tiền khi thanh toán thành công nhưng phòng đã hết ở thời điểm xử lý IPN
    TC26: Không tạo booking nếu số phòng trống giảm xuống dưới quantity ở lần kiểm tra cuối
    """
    rt, booking_data = ipn_test_setup
    
    # Cố ý set quantity = 5 (vượt quá 3 phòng hiện có)
    booking_data['quantity'] = 5
    booking_data['total_price'] = 5000000
    
    extra_data = get_base64_extra_data(booking_data)
    
    ipn_payload = {
        'resultCode': 0,
        'extraData': extra_data,
        'amount': 5000000,
        'transId': 'TRANS_LATE',
        'orderId': 'ORDER_LATE'
    }
    
    test_client.post('/booking/momo-ipn', json=ipn_payload)
    
    # Sẽ rollback, không tạo booking
    booking = test_session.query(Booking).filter_by(room_type_id=rt.id).first()
    assert booking is None
    
    # Phải có lệnh Refund
    refund = test_session.query(RefundLog).filter_by(trans_id='TRANS_LATE').first()
    assert refund is not None
    assert "chỉ còn" in refund.reason.lower() or "không đủ" in refund.reason.lower()
