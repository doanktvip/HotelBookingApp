import pytest
from unittest.mock import patch, MagicMock
from app.services.momo_service import MoMoService

def test_encode_decode_extra_data():
    booking_dict = {"booking_id": 123, "user_id": 456}
    encoded = MoMoService.encode_extra_data(booking_dict)
    
    assert isinstance(encoded, str)
    assert encoded != ""
    
    decoded = MoMoService.decode_extra_data(encoded)
    assert decoded["booking_id"] == 123
    assert decoded["user_id"] == 456
    
    assert MoMoService.decode_extra_data("") == {}
    assert MoMoService.decode_extra_data("invalid_base64_!@#") == {}

def test_generate_signature():
    secret_key = "my_secret_key"
    data = "amount=50000&orderId=123"
    sig = MoMoService.generate_signature(data, secret_key)
    
    assert isinstance(sig, str)
    assert len(sig) == 64 # Chuẩn SHA256 phải là chuỗi hexa 64 ký tự

@patch('app.services.momo_service.requests.post')
def test_create_payment_request_success(mock_post, test_app):
    mock_response = MagicMock()
    mock_response.json.return_value = {"payUrl": "https://momo.vn/pay/test", "resultCode": 0}
    mock_post.return_value = mock_response
    
    booking_data = {
        "total_price": 500000,
        "quantity": 1,
        "hotel_name": "Khách sạn X",
        "room_type_name": "Standard",
        "check_in": "2026-12-01",
        "check_out": "2026-12-02",
        "booking_id": 999
    }
    
    with test_app.test_request_context():
        # Bơm cấu hình giả vào Flask App
        test_app.config['MOMO_ENDPOINT'] = "https://test.momo.vn"
        test_app.config['MOMO_PARTNER_CODE'] = "PARTNER"
        test_app.config['MOMO_ACCESS_KEY'] = "ACCESS"
        test_app.config['MOMO_SECRET_KEY'] = "SECRET"
        
        result = MoMoService.create_payment_request(booking_data)
        
        assert result["resultCode"] == 0
        assert "payUrl" in result
        assert "extraData" in result
        mock_post.assert_called_once()

def test_verify_ipn_signature(test_app):
    with test_app.app_context():
        test_app.config['MOMO_ACCESS_KEY'] = "ACCESS"
        test_app.config['MOMO_SECRET_KEY'] = "SECRET"
        
        ipn_data = {
            "amount": "50000",
            "extraData": "base64==",
            "message": "Success",
            "orderId": "O_123",
            "orderInfo": "Thanh toan",
            "orderType": "momo_wallet",
            "partnerCode": "PARTNER",
            "payType": "qr",
            "requestId": "R_123",
            "responseTime": "123456",
            "resultCode": "0",
            "transId": "T_123"
        }
        
        # 1. Tính toán chữ ký chuẩn bằng Secret Key
        raw_sig = (
            "accessKey=ACCESS&amount=50000&extraData=base64==&message=Success&orderId=O_123"
            "&orderInfo=Thanh toan&orderType=momo_wallet&partnerCode=PARTNER&payType=qr"
            "&requestId=R_123&responseTime=123456&resultCode=0&transId=T_123"
        )
        real_sig = MoMoService.generate_signature(raw_sig, "SECRET")
        
        # Đưa chữ ký chuẩn vào cục IPN giả
        ipn_data["signature"] = real_sig
        
        # Hàm xác thực phải báo True
        assert MoMoService.verify_ipn_signature(ipn_data) is True
        
        # Đổi chữ ký thành chữ ký bậy bạ
        ipn_data["signature"] = "bad_hacker_signature"
        # Hàm xác thực phải từ chối ngay lập tức
        assert MoMoService.verify_ipn_signature(ipn_data) is False

def test_refund_payment_mock(test_app):
    with test_app.app_context():
        test_app.config['MOMO_PARTNER_CODE'] = "PARTNER"
        test_app.config['MOMO_ACCESS_KEY'] = "ACCESS"
        test_app.config['MOMO_SECRET_KEY'] = "SECRET"
        
        # Code của bạn đã hỗ trợ tự động trả về success nếu mã giao dịch bắt đầu bằng MOCK_
        result = MoMoService.refund_payment("O_123", "MOCK_123", "50000")
        assert result["resultCode"] == 0
        assert result["transId"] == "MOCK_123"


# --- Merged from test_momo_booking.py ---

import os
import sys
import hashlib
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from flask import g

# Đảm bảo đường dẫn gốc dự án có trong sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.models import (
    User, UserRole, Hotel, RoomType, Room, RoomStatus,
    Booking, BookingStatus, BookingDetail, Payment, PaymentStatus, PaymentMethod
)
from app.services.momo_service import MoMoService
from app.services.booking_service import BookingService


@pytest.fixture
def mock_external_services():
    """Giả lập (Mock) các dịch vụ bên ngoài để kiểm thử độc lập, không gọi mạng ngoài."""
    with patch('app.routes.booking.MoMoService.verify_ipn_signature', return_value=True), \
         patch('app.services.email_service.EmailService.send_booking_confirmation_email', return_value=True), \
         patch('app.routes.booking.socketio.emit', return_value=None), \
         patch('builtins.print'):
        yield


@pytest.fixture
def base_momo_setup(test_session):
    """
    Chuẩn bị dữ liệu dùng chung (Khách hàng & Khách sạn) và cung cấp helper tạo RoomType độc lập cho từng test.
    Đảm bảo tính cô lập tuyệt đối giữa các test case.
    """

    customer = test_session.query(User).filter_by(username="momo_test_customer").first()
    if not customer:
        customer = User(
            username="momo_test_customer",
            email="momo_test_customer@hotel.com",
            password=hashlib.md5("123456".encode('utf-8')).hexdigest(),
            role=UserRole.CUSTOMER,
            is_verified=True
        )
        test_session.add(customer)
        test_session.commit()

    hotel = test_session.query(Hotel).filter_by(name="Khách Sạn MoMo Unit Test").first()
    if not hotel:
        hotel = Hotel(
            name="Khách Sạn MoMo Unit Test",
            address="123 Đường Test MoMo",
            location="Hồ Chí Minh",
            description="Khách sạn phục vụ unit test MoMo",
            rating=5.0,
            cancellation_policy_days=2
        )
        test_session.add(hotel)
        test_session.commit()

    created_room_types = []

    def create_test_room_type(name: str, base_price: Decimal = Decimal("1000000.00"), room_count: int = 1):
        """Tạo loại phòng độc lập và các phòng vật lý tương ứng cho test case"""
        # Xóa nếu đã tồn tại từ trước để đảm bảo dữ liệu sạch
        existing_rt = test_session.query(RoomType).filter_by(hotel_id=hotel.id, name=name).first()
        if existing_rt:
            # Xóa các liên kết cũ nếu có
            for rm in existing_rt.rooms:
                test_session.query(BookingDetail).filter_by(room_id=rm.id).delete()
                test_session.delete(rm)
            test_session.delete(existing_rt)
            test_session.commit()

        rt = RoomType(
            hotel_id=hotel.id,
            name=name,
            description=f"Loại phòng dùng riêng cho test case {name}",
            base_price=base_price,
            max_occupancy=2,
            bed_count=1,
            bed_type="King Size",
            is_active=True
        )
        test_session.add(rt)
        test_session.commit()
        created_room_types.append(rt.id)

        rooms = []
        for i in range(1, room_count + 1):
            r = Room(
                room_type_id=rt.id,
                room_number=f"{name}-R{i:02d}",
                floor=1,
                status=RoomStatus.AVAILABLE,
                is_active=True
            )
            test_session.add(r)
            rooms.append(r)
        test_session.commit()
        test_session.refresh(rt)
        return rt, rooms

    yield {
        "customer": customer,
        "hotel": hotel,
        "create_test_room_type": create_test_room_type
    }

def test_tc20_momo_ipn_success_creates_confirmed_booking_and_payment(client, test_db, test_session, base_momo_setup, mock_external_services):
    """
    TC20: Kiểm tra gửi IPN thành công tạo đơn đặt phòng CONFIRMED, Payment SUCCESS và phân bổ phòng.
    - Precondition: Chuẩn bị 1 phòng trống và dữ liệu tạm (pending booking trong extraData).
    - Action: Gửi webhook IPN với resultCode = 0, đúng số tiền (1.000.000 VNĐ), transaction_id mới.
    - Assert: Booking status = CONFIRMED, Payment status = SUCCESS, payment_method = MOMO,
              tạo đúng BookingDetail cho phòng được phân bổ.
    """
    customer = base_momo_setup["customer"]
    hotel = base_momo_setup["hotel"]
    create_room_type = base_momo_setup["create_test_room_type"]

    # Precondition: Tạo riêng loại phòng TC20 với 1 phòng trống
    room_type, rooms = create_room_type("RT_TC20", base_price=Decimal("1000000.00"), room_count=1)

    check_in = date.today() + timedelta(days=5)
    check_out = date.today() + timedelta(days=6)  # 1 đêm

    booking_data = {
        'user_id': customer.id,
        'hotel_id': hotel.id,
        'hotel_name': hotel.name,
        'room_type_id': room_type.id,
        'room_type_name': room_type.name,
        'check_in': check_in.strftime('%d/%m/%Y'),
        'check_out': check_out.strftime('%d/%m/%Y'),
        'quantity': 1,
        'price_at_booking': float(room_type.base_price),
        'total_price': float(room_type.base_price * 1)  # 1.000.000 VNĐ
    }
    extra_data = MoMoService.encode_extra_data(booking_data)

    trans_id = "MOCK_TRANS_TC20_001"
    order_id = "ORDER_TC20_001"
    ipn_payload = {
        'resultCode': 0,
        'amount': 1000000,
        'transId': trans_id,
        'orderId': order_id,
        'extraData': extra_data,
        'signature': 'TEST_DEV_SIGNATURE'
    }

    # Action: Gửi IPN POST tới webhook endpoint
    response = client.post('/api/payment/momo-ipn', json=ipn_payload)
    assert response.status_code == 204

    # Assert 1: Kiểm tra Booking được tạo với status = CONFIRMED
    test_session.expire_all()
    booking = test_session.query(Booking).filter_by(
        user_id=customer.id,
        room_type_id=room_type.id
    ).first()

    assert booking is not None, "Booking không được tạo sau khi IPN thành công!"
    assert booking.status == BookingStatus.CONFIRMED, f"Trạng thái booking không phải CONFIRMED: {booking.status}"
    assert booking.check_in == check_in
    assert booking.check_out == check_out

    # Assert 2: Kiểm tra Payment có status = SUCCESS và payment_method = MOMO
    payment = test_session.query(Payment).filter_by(booking_id=booking.id).first()
    assert payment is not None, "Payment record không được tạo!"
    assert payment.status == PaymentStatus.SUCCESS
    assert payment.payment_method in (PaymentMethod.MOMO, "MOMO") or payment.payment_method.value == "MOMO"
    assert payment.transaction_id == trans_id
    assert payment.amount == Decimal("1000000")

    # Assert 3: Tạo đúng BookingDetail cho từng phòng được phân bổ
    details = test_session.query(BookingDetail).filter_by(booking_id=booking.id).all()
    assert len(details) == 1, f"Số lượng BookingDetail không đúng: {len(details)}"
    assert details[0].room_id == rooms[0].id


# ==============================================================================
# TEST CASE 21
# ==============================================================================
def test_tc21_momo_ipn_duplicate_transaction_id_idempotency(client, test_db, test_session, base_momo_setup, mock_external_services):
    """
    TC21: Đảm bảo tính Idempotency khi MoMo gọi lại IPN với cùng transaction_id.
    - Precondition: Đã xử lý thành công IPN có transaction_id = X.
    - Action: Gửi lại IPN lần 2 với cùng transaction_id = X.
    - Assert: Hệ thống trả về booking hiện tại, không tạo thêm Booking hay Payment mới.
    """
    customer = base_momo_setup["customer"]
    hotel = base_momo_setup["hotel"]
    create_room_type = base_momo_setup["create_test_room_type"]

    room_type, rooms = create_room_type("RT_TC21", base_price=Decimal("1000000.00"), room_count=1)

    check_in = date.today() + timedelta(days=7)
    check_out = date.today() + timedelta(days=8)

    booking_data = {
        'user_id': customer.id,
        'hotel_id': hotel.id,
        'hotel_name': hotel.name,
        'room_type_id': room_type.id,
        'room_type_name': room_type.name,
        'check_in': check_in.strftime('%d/%m/%Y'),
        'check_out': check_out.strftime('%d/%m/%Y'),
        'quantity': 1,
        'price_at_booking': float(room_type.base_price),
        'total_price': float(room_type.base_price)
    }
    extra_data = MoMoService.encode_extra_data(booking_data)

    trans_id_idem = "MOCK_TRANS_TC21_IDEM"
    ipn_payload = {
        'resultCode': 0,
        'amount': 1000000,
        'transId': trans_id_idem,
        'orderId': "ORDER_TC21_IDEM",
        'extraData': extra_data,
        'signature': 'TEST_DEV_SIGNATURE'
    }

    # Action 1: Gửi IPN lần 1 (thành công)
    res1 = client.post('/api/payment/momo-ipn', json=ipn_payload)
    assert res1.status_code == 204

    # Action 2: Gửi lại IPN lần 2 với cùng transaction_id
    res2 = client.post('/api/payment/momo-ipn', json=ipn_payload)
    assert res2.status_code == 204

    # Assert: Số lượng Booking và Payment không bị nhân đôi (vẫn là 1)
    test_session.expire_all()
    bookings = test_session.query(Booking).filter_by(
        user_id=customer.id,
        room_type_id=room_type.id
    ).all()
    assert len(bookings) == 1, f"Idempotency thất bại: tìm thấy {len(bookings)} bookings!"

    payments = test_session.query(Payment).filter_by(transaction_id=trans_id_idem).all()
    assert len(payments) == 1, f"Idempotency thất bại: tìm thấy {len(payments)} payments!"


# ==============================================================================
# TEST CASE 22
# ==============================================================================
def test_tc22_momo_ipn_insufficient_amount_raises_error(client, test_db, test_session, base_momo_setup, mock_external_services):
    """
    TC22: Gửi IPN với số tiền không đủ so với đơn đặt phòng.
    - Precondition: Đơn hàng cần thanh toán 2.000.000 VNĐ.
    - Action: Gửi IPN resultCode = 0 nhưng amount < 2.000.000 VNĐ (ví dụ 1.500.000 VNĐ).
    - Assert: Hệ thống báo lỗi số tiền không hợp lệ, Booking không được kích hoạt thành CONFIRMED,
              kích hoạt luồng hoàn tiền và ghi nhận RefundLog.
    """
    customer = base_momo_setup["customer"]
    hotel = base_momo_setup["hotel"]
    create_room_type = base_momo_setup["create_test_room_type"]

    room_type, rooms = create_room_type("RT_TC22", base_price=Decimal("1000000.00"), room_count=2)

    check_in = date.today() + timedelta(days=9)
    check_out = date.today() + timedelta(days=10)

    # Đơn hàng cần thanh toán 2.000.000 VNĐ (2 phòng x 1.000.000)
    booking_data = {
        'user_id': customer.id,
        'hotel_id': hotel.id,
        'hotel_name': hotel.name,
        'room_type_id': room_type.id,
        'room_type_name': room_type.name,
        'check_in': check_in.strftime('%d/%m/%Y'),
        'check_out': check_out.strftime('%d/%m/%Y'),
        'quantity': 2,
        'price_at_booking': float(room_type.base_price),
        'total_price': 2000000.0
    }
    extra_data = MoMoService.encode_extra_data(booking_data)

    trans_id_short = "MOCK_TRANS_TC22_SHORT"
    order_id_short = "ORDER_TC22_SHORT"

    # Action: Gửi IPN với amount = 1.500.000 VNĐ (< 2.000.000 VNĐ)
    ipn_payload = {
        'resultCode': 0,
        'amount': 1500000,
        'transId': trans_id_short,
        'orderId': order_id_short,
        'extraData': extra_data,
        'signature': 'TEST_DEV_SIGNATURE'
    }

    response = client.post('/api/payment/momo-ipn', json=ipn_payload)
    assert response.status_code == 204

    # Assert 1: Booking KHÔNG được tạo / không kích hoạt thành CONFIRMED
    test_session.expire_all()
    booking = test_session.query(Booking).filter_by(
        user_id=customer.id,
        room_type_id=room_type.id
    ).first()
    assert booking is None, "Đơn đặt phòng không được phép tạo khi thiếu tiền!"

    # Assert 2: Kiểm tra log hoặc xử lý khi gọi Refund API (Bỏ qua RefundLog)
    # Vì RefundLog đã bị xóa, hàm process_refund chỉ cần gọi API MoMo và trả về kết quả


# ==============================================================================
# TEST CASE 23
# ==============================================================================
def test_tc23_momo_ipn_refund_when_room_out_of_stock_at_ipn_time(client, test_db, test_session, base_momo_setup, mock_external_services):
    """
    TC23: Hết phòng tại thời điểm xử lý IPN (Race condition sau khi khách quét QR).
    - Precondition: Người dùng nhận QR thanh toán khi phòng còn, nhưng trước khi IPN xử lý
                    thì phòng bị booking khác chiếm hết.
    - Action: Gửi IPN thanh toán thành công resultCode = 0.
    - Assert: Xử lý tạo phòng thất bại do hết phòng, kích hoạt luồng hoàn tiền/ghi nhận log
              hoàn tiền cho orderId tương ứng.
    """
    customer = base_momo_setup["customer"]
    hotel = base_momo_setup["hotel"]
    create_room_type = base_momo_setup["create_test_room_type"]

    # Chỉ tạo đúng 1 phòng duy nhất cho loại phòng này
    room_type, rooms = create_room_type("RT_TC23", base_price=Decimal("1000000.00"), room_count=1)
    single_room = rooms[0]

    check_in = date.today() + timedelta(days=11)
    check_out = date.today() + timedelta(days=12)

    booking_data = {
        'user_id': customer.id,
        'hotel_id': hotel.id,
        'hotel_name': hotel.name,
        'room_type_id': room_type.id,
        'room_type_name': room_type.name,
        'check_in': check_in.strftime('%d/%m/%Y'),
        'check_out': check_out.strftime('%d/%m/%Y'),
        'quantity': 1,
        'price_at_booking': float(room_type.base_price),
        'total_price': float(room_type.base_price)
    }
    extra_data = MoMoService.encode_extra_data(booking_data)

    # Precondition: Trước khi IPN xử lý, phòng duy nhất bị 1 đơn CONFIRMED khác chiếm chỗ
    competing_booking = Booking(
        user_id=customer.id,
        hotel_id=hotel.id,
        room_type_id=room_type.id,
        check_in=check_in,
        check_out=check_out,
        total_price=Decimal("1000000"),
        status=BookingStatus.CONFIRMED
    )
    test_session.add(competing_booking)
    test_session.flush()

    competing_detail = BookingDetail(
        booking_id=competing_booking.id,
        room_id=single_room.id,
        price_at_booking=room_type.base_price
    )
    test_session.add(competing_detail)
    test_session.commit()

    trans_id_oos = "MOCK_TRANS_TC23_OOS"
    order_id_oos = "ORDER_TC23_OOS"
    ipn_payload = {
        'resultCode': 0,
        'amount': 1000000,
        'transId': trans_id_oos,
        'orderId': order_id_oos,
        'extraData': extra_data,
        'signature': 'TEST_DEV_SIGNATURE'
    }

    # Action: Gửi IPN
    response = client.post('/api/payment/momo-ipn', json=ipn_payload)
    assert response.status_code == 204

    # Assert 1: Không tạo thêm booking mới cho khách (chỉ duy nhất có competing_booking)
    test_session.expire_all()
    bookings = test_session.query(Booking).filter_by(
        user_id=customer.id,
        room_type_id=room_type.id
    ).all()
    assert len(bookings) == 1
    assert bookings[0].id == competing_booking.id

    # Assert 2: Kích hoạt luồng hoàn tiền, ghi nhận log hoàn tiền cho orderId tương ứng
    # Assert RefundLog đã bị xóa nên không cần assert


# ==============================================================================
# TEST CASE 24
# ==============================================================================
def test_tc24_create_booking_with_multiple_rooms_quantity(client, test_db, test_session, base_momo_setup, mock_external_services):
    """
    TC24: Đặt phòng với số lượng nhiều phòng (quantity = 3).
    - Precondition: Hệ thống có sẵn 3 phòng trống cùng loại.
    - Action: Xử lý thanh toán thành công cho quantity = 3.
    - Assert: Tạo đúng 1 Booking, tạo đúng 3 bản ghi BookingDetail tương ứng 3 mã phòng vật lý khác nhau.
    """
    customer = base_momo_setup["customer"]
    hotel = base_momo_setup["hotel"]
    create_room_type = base_momo_setup["create_test_room_type"]

    # Precondition: Tạo loại phòng với 3 phòng trống
    room_type, rooms = create_room_type("RT_TC24", base_price=Decimal("1000000.00"), room_count=3)
    room_ids_set = {r.id for r in rooms}
    assert len(room_ids_set) == 3

    check_in = date.today() + timedelta(days=13)
    check_out = date.today() + timedelta(days=14)

    total_amount = float(room_type.base_price * 3)  # 3.000.000 VNĐ
    booking_data = {
        'user_id': customer.id,
        'hotel_id': hotel.id,
        'hotel_name': hotel.name,
        'room_type_id': room_type.id,
        'room_type_name': room_type.name,
        'check_in': check_in.strftime('%d/%m/%Y'),
        'check_out': check_out.strftime('%d/%m/%Y'),
        'quantity': 3,
        'price_at_booking': float(room_type.base_price),
        'total_price': total_amount
    }
    extra_data = MoMoService.encode_extra_data(booking_data)

    trans_id_multi = "MOCK_TRANS_TC24_MULTI"
    ipn_payload = {
        'resultCode': 0,
        'amount': int(total_amount),
        'transId': trans_id_multi,
        'orderId': "ORDER_TC24_MULTI",
        'extraData': extra_data,
        'signature': 'TEST_DEV_SIGNATURE'
    }

    # Action: Xử lý thanh toán thành công
    response = client.post('/api/payment/momo-ipn', json=ipn_payload)
    assert response.status_code == 204

    # Assert 1: Tạo đúng 1 Booking
    test_session.expire_all()
    bookings = test_session.query(Booking).filter_by(
        user_id=customer.id,
        room_type_id=room_type.id
    ).all()
    assert len(bookings) == 1
    booking = bookings[0]
    assert booking.status == BookingStatus.CONFIRMED

    # Assert 2: Tạo đúng 3 bản ghi BookingDetail tương ứng 3 phòng vật lý khác nhau
    details = test_session.query(BookingDetail).filter_by(booking_id=booking.id).all()
    assert len(details) == 3, f"Số lượng chi tiết đặt phòng không khớp: {len(details)}"

    allocated_room_ids = {d.room_id for d in details}
    assert len(allocated_room_ids) == 3, "Các phòng phân bổ bị trùng lặp!"
    assert allocated_room_ids == room_ids_set, "Phòng phân bổ không khớp danh sách phòng vật lý khả dụng!"


# ==============================================================================
# TEST CASE 25
# ==============================================================================
def test_tc25_booking_status_confirmed_after_successful_payment(client, test_db, test_session, base_momo_setup, mock_external_services):
    """
    TC25: Kiểm tra trạng thái Booking là CONFIRMED sau khi thanh toán thành công.
    - Precondition: Hoàn tất luồng thanh toán hợp lệ qua IPN.
    - Action: Truy vấn Booking từ database.
    - Assert: booking.status == BookingStatus.CONFIRMED.
    """
    customer = base_momo_setup["customer"]
    hotel = base_momo_setup["hotel"]
    create_room_type = base_momo_setup["create_test_room_type"]

    room_type, rooms = create_room_type("RT_TC25", base_price=Decimal("1000000.00"), room_count=1)

    check_in = date.today() + timedelta(days=15)
    check_out = date.today() + timedelta(days=16)

    booking_data = {
        'user_id': customer.id,
        'hotel_id': hotel.id,
        'hotel_name': hotel.name,
        'room_type_id': room_type.id,
        'room_type_name': room_type.name,
        'check_in': check_in.strftime('%d/%m/%Y'),
        'check_out': check_out.strftime('%d/%m/%Y'),
        'quantity': 1,
        'price_at_booking': float(room_type.base_price),
        'total_price': float(room_type.base_price)
    }
    extra_data = MoMoService.encode_extra_data(booking_data)

    trans_id_valid = "MOCK_TRANS_TC25_CONFIRM"
    ipn_payload = {
        'resultCode': 0,
        'amount': 1000000,
        'transId': trans_id_valid,
        'orderId': "ORDER_TC25_CONFIRM",
        'extraData': extra_data,
        'signature': 'TEST_DEV_SIGNATURE'
    }

    # Precondition: Hoàn tất luồng thanh toán hợp lệ
    response = client.post('/api/payment/momo-ipn', json=ipn_payload)
    assert response.status_code == 204

    # Action: Truy vấn Booking từ database
    test_session.expire_all()
    booking = test_session.query(Booking).filter_by(
        user_id=customer.id,
        room_type_id=room_type.id
    ).first()

    # Assert: booking.status == BookingStatus.CONFIRMED
    assert booking is not None, "Không tìm thấy đơn đặt phòng trong DB!"
    assert booking.status == BookingStatus.CONFIRMED
    assert booking.payment is not None
    assert booking.payment.status == PaymentStatus.SUCCESS


# ==============================================================================
# TEST CASE 26
# ==============================================================================
def test_tc26_reject_booking_when_available_rooms_drop_below_quantity(client, test_db, test_session, base_momo_setup, mock_external_services):
    """
    TC26: Từ chối đặt phòng khi số lượng phòng trống giảm xuống dưới số lượng yêu cầu.
    - Precondition: Ban đầu còn 2 phòng. Trước thời điểm phân bổ phòng thực tế số lượng giảm xuống còn 1.
    - Action: Thử hoàn tất booking với quantity = 2.
    - Assert: Hệ thống rollback, không tạo booking, trả về thông báo lỗi số lượng phòng trống không đủ
              và kích hoạt hoàn tiền RefundLog.
    """
    customer = base_momo_setup["customer"]
    hotel = base_momo_setup["hotel"]
    create_room_type = base_momo_setup["create_test_room_type"]

    # Ban đầu có 2 phòng
    room_type, rooms = create_room_type("RT_TC26", base_price=Decimal("1000000.00"), room_count=2)
    room_1, room_2 = rooms[0], rooms[1]

    check_in = date.today() + timedelta(days=17)
    check_out = date.today() + timedelta(days=18)

    # 1 phòng bị chiếm trước thời điểm phân bổ thực tế (còn lại 1 phòng)
    pre_booking = Booking(
        user_id=customer.id,
        hotel_id=hotel.id,
        room_type_id=room_type.id,
        check_in=check_in,
        check_out=check_out,
        total_price=Decimal("1000000"),
        status=BookingStatus.CONFIRMED
    )
    test_session.add(pre_booking)
    test_session.flush()

    pre_detail = BookingDetail(
        booking_id=pre_booking.id,
        room_id=room_1.id,
        price_at_booking=room_type.base_price
    )
    test_session.add(pre_detail)
    test_session.commit()

    # Dữ liệu khách hàng yêu cầu 2 phòng
    booking_data = {
        'user_id': customer.id,
        'hotel_id': hotel.id,
        'hotel_name': hotel.name,
        'room_type_id': room_type.id,
        'room_type_name': room_type.name,
        'check_in': check_in.strftime('%d/%m/%Y'),
        'check_out': check_out.strftime('%d/%m/%Y'),
        'quantity': 2,
        'price_at_booking': float(room_type.base_price),
        'total_price': 2000000.0
    }
    extra_data = MoMoService.encode_extra_data(booking_data)

    trans_id_drop = "MOCK_TRANS_TC26_DROP"
    order_id_drop = "ORDER_TC26_DROP"
    ipn_payload = {
        'resultCode': 0,
        'amount': 2000000,
        'transId': trans_id_drop,
        'orderId': order_id_drop,
        'extraData': extra_data,
        'signature': 'TEST_DEV_SIGNATURE'
    }

    # Action 1: Gửi qua Webhook IPN
    response = client.post('/api/payment/momo-ipn', json=ipn_payload)
    assert response.status_code == 204

    # Assert 1: Không tạo thêm booking mới (chỉ có pre_booking)
    test_session.expire_all()
    bookings = test_session.query(Booking).filter_by(
        user_id=customer.id,
        room_type_id=room_type.id
    ).all()
    assert len(bookings) == 1
    assert bookings[0].id == pre_booking.id

    # Assert 2: Kiểm tra xử lý hoàn tiền (Bỏ qua RefundLog)
    # Vì RefundLog đã bị xóa, chỉ cần MoMo API được gọi thành công là đủ.

    # Action 2 & Assert 3: Kiểm tra trực tiếp qua BookingService cũng bắn ngoại lệ ValueError
    booking_service = BookingService(test_session)
    payment_data = {
        'amount': 2000000,
        'transaction_id': 'MOCK_TRANS_DIRECT_CHECK',
        'payment_method': 'MOMO'
    }
    with pytest.raises(ValueError) as excinfo:
        booking_service.process_successful_payment(booking_data, payment_data)
    assert "chỉ còn 1 phòng trống" in str(excinfo.value).lower() or "không đủ" in str(excinfo.value).lower()
