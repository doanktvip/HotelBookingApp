import pytest
from datetime import date, timedelta
from decimal import Decimal
import hashlib
from app.models import (
    User, UserRole, Hotel, RoomType, Room, RoomStatus,
    Booking, BookingStatus, BookingDetail, Payment, PaymentMethod, PaymentStatus,
    Tag, SystemConfig, OTP, PricePrediction, SearchHistory, PriceHistory, RefundLog
)

import uuid
from app.utils import get_vn_time
PASSWORD='123456'
# ==============================================================================
# TẦNG CORE (LEVEL 1) - DỮ LIỆU ĐỘC LẬP
# ==============================================================================

@pytest.fixture(scope='function')
def sample_customer(test_session):
    """Tài khoản khách hàng"""
    user = User(
        username="customer",
        email="customer@gmail.com",
        password=str(hashlib.md5(PASSWORD.strip().encode('utf-8')).hexdigest()),
        role=UserRole.CUSTOMER,
        is_verified=True
    )
    test_session.add(user)
    test_session.commit()
    return user


@pytest.fixture(scope='function')
def sample_admin(test_session):
    """Tài khoản quản trị viên"""
    user = User(
        username="admin",
        email="admin@hotel.com",
        password=str(hashlib.md5(PASSWORD.strip().encode('utf-8')).hexdigest()),
        role=UserRole.ADMIN,
        is_verified=True
    )
    test_session.add(user)
    test_session.commit()
    return user


@pytest.fixture(scope='function')
def sample_receptionist(test_session):
    """Tài khoản lễ tân (Chưa gán khách sạn, sẽ gán ở Level 2)"""
    user = User(
        username="recept",
        email="recept@hotel.com",
        password=str(hashlib.md5(PASSWORD.strip().encode('utf-8')).hexdigest()),
        role=UserRole.RECEPTIONIST,
        is_verified=True
    )
    test_session.add(user)
    test_session.commit()
    return user


@pytest.fixture(scope='function')
def sample_tags(test_session):
    """Danh sách các tag tiện ích cơ bản"""
    tags = [
        Tag(name="Wifi Miễn phí", icon="bi-wifi"),
        Tag(name="Hồ bơi", icon="bi-water"),
        Tag(name="Bữa sáng", icon="bi-cup-hot")
    ]
    test_session.add_all(tags)
    test_session.commit()
    return tags


@pytest.fixture(scope='function')
def sample_system_config(test_session):
    """Cấu hình hệ thống mẫu"""
    config = SystemConfig(
        config_key="MAX_ROOMS_PER_BOOKING",
        config_value="5",
        description="Số lượng phòng tối đa được phép đặt trong 1 đơn"
    )
    test_session.add(config)
    test_session.commit()
    return config


# ==============================================================================
# TẦNG CƠ SỞ VẬT CHẤT (LEVEL 2) - PHỤ THUỘC LEVEL 1
# ==============================================================================

@pytest.fixture(scope='function')
def sample_hotel(test_session, sample_tags, sample_receptionist):
    """Khách sạn chuẩn với Tag và Lễ tân"""
    hotel = Hotel(
        name="Nha Trang Bay Hotel",
        address="01 Trần Phú",
        location="Khánh Hòa",
        description="Khách sạn view biển đẹp nhất",
        rating=4.5,
        cancellation_policy_days=3
    )
    # Gán tag cho khách sạn
    hotel.tags.extend(sample_tags)
    test_session.add(hotel)
    test_session.commit()

    # Gán lễ tân vào khách sạn này
    sample_receptionist.hotel_id = hotel.id
    test_session.commit()
    
    return hotel


@pytest.fixture(scope='function')
def sample_room_type(test_session, sample_hotel):
    """Loại phòng Deluxe Hướng biển"""
    room_type = RoomType(
        hotel=sample_hotel,
        name="Deluxe Ocean View",
        description="Phòng rộng 40m2, view biển trực diện",
        base_price=Decimal("1500000.00"),
        max_occupancy=2,
        bed_count=1,
        bed_type="Giường đôi cực lớn"
    )
    test_session.add(room_type)
    test_session.commit()
    return room_type


@pytest.fixture(scope='function')
def sample_rooms(test_session, sample_room_type):
    """Tạo 3 phòng vật lý thuộc loại Deluxe Ocean View"""
    rooms = [
        Room(room_type=sample_room_type, room_number="101", floor=1, status=RoomStatus.AVAILABLE),
        Room(room_type=sample_room_type, room_number="102", floor=2, status=RoomStatus.AVAILABLE),
        Room(room_type=sample_room_type, room_number="103", floor=3, status=RoomStatus.AVAILABLE)
    ]
    test_session.add_all(rooms)
    test_session.commit()
    return rooms


# ==============================================================================
# TẦNG GIAO DỊCH (LEVEL 3) - PHỤ THUỘC LEVEL 1 & 2
# ==============================================================================

@pytest.fixture(scope='function')
def sample_booking(test_session, sample_customer, sample_room_type):
    """Đơn đặt phòng (chưa có phòng chi tiết)"""
    hotel = sample_room_type.hotel
    
    # Giả định khách đặt 2 ngày, bắt đầu từ ngày mai
    check_in = date.today() + timedelta(days=1)
    check_out = check_in + timedelta(days=2)
    
    # Khách đặt 2 phòng x 2 đêm = 4 x 1,500,000 = 6,000,000
    booking = Booking(
        customer=sample_customer,
        hotel=hotel,
        room_type=sample_room_type,
        check_in=check_in,
        check_out=check_out,
        total_price=Decimal("6000000.00"),
        status=BookingStatus.CONFIRMED
    )
    test_session.add(booking)
    test_session.commit()
    return booking


@pytest.fixture(scope='function')
def sample_booking_details(test_session, sample_booking, sample_rooms):
    """Chi tiết đơn đặt phòng: Khách lấy phòng 101 và 102"""
    # Lấy 2 phòng đầu tiên (101, 102)
    assigned_rooms = sample_rooms[:2]
    
    details = []
    for room in assigned_rooms:
        bd = BookingDetail(
            booking=sample_booking,
            room=room,
            price_at_booking=sample_booking.room_type.base_price
        )
        details.append(bd)
        # Đổi trạng thái phòng thành đã đặt
        room.status = RoomStatus.BOOKED

    test_session.add_all(details)
    test_session.commit()
    return details


@pytest.fixture(scope='function')
def sample_payment(test_session, sample_booking):
    """Giao dịch thanh toán đã thành công"""
    payment = Payment(
        booking=sample_booking,
        payment_method=PaymentMethod.MOMO,
        amount=sample_booking.total_price,
        transaction_id="MOMO123456789",
        status=PaymentStatus.SUCCESS
    )
    test_session.add(payment)
    test_session.commit()
    return payment


# ==============================================================================
# TẦNG NÂNG CAO (LEVEL 4) - CÁC TÍNH NĂNG MỞ RỘNG
# ==============================================================================

@pytest.fixture(scope='function')
def sample_otp(test_session, sample_customer):
    """Mã OTP cho người dùng"""
    otp = OTP(
        user_id=sample_customer.id,
        otp_code="123456",
        expires_at=date.today() + timedelta(days=1),
        is_used=False
    )
    test_session.add(otp)
    test_session.commit()
    return otp


@pytest.fixture(scope='function')
def sample_price_prediction(test_session, sample_hotel):
    """Gợi ý tăng giá phòng của AI (Vd: Tăng 10% dịp Lễ)"""
    prediction = PricePrediction(
        hotel_id=sample_hotel.id,
        target_date=date.today() + timedelta(days=30),
        adjustment_percentage=Decimal("0.1000"),
        reason="Lễ 30/4",
        is_applied=False
    )
    test_session.add(prediction)
    test_session.commit()
    return prediction


@pytest.fixture(scope='function')
def sample_search_history(test_session, sample_customer):
    """Lịch sử tìm kiếm của khách hàng"""
    search_history = SearchHistory(
        user_id=sample_customer.id,
        search_query="Tìm phòng cho 2 người ở Nha Trang có hồ bơi",
        parsed_data={"location": "Nha Trang", "occupancy": 2, "amenities": ["Hồ bơi"]},
        is_useful=True
    )
    test_session.add(search_history)
    test_session.commit()
    return search_history


@pytest.fixture(scope='function')
def sample_price_history(test_session, sample_room_type):
    """Lịch sử lưu vết đổi giá của loại phòng"""
    history = PriceHistory(
        room_type_id=sample_room_type.id,
        old_price=Decimal("1200000.00"),
        new_price=Decimal("1500000.00")
    )
    test_session.add(history)
    test_session.commit()
    return history


@pytest.fixture(scope='function')
def sample_refund_log(test_session):
    """Lịch sử hoàn tiền độc lập"""
    refund = RefundLog(
        order_id="BOOKING_9999",
        trans_id="MOMO_REFUND_9999",
        amount=Decimal("1000000.00"),
        reason="Khách hủy phòng trước 7 ngày"
    )
    test_session.add(refund)
    test_session.commit()
    return refund

# === MIGRATED UI FIXTURES ===
@pytest.fixture(scope='function')
def setup_recept_data(test_db, sample_customer, sample_room_type, sample_rooms):
    
    # Create Receptionist
    pw_hash = str(hashlib.md5("123456".encode('utf-8')).hexdigest())
    recept = User(username="receptionist_manage", email="recept@manage.com", password=pw_hash, role=UserRole.RECEPTIONIST, phone="0999999999", hotel_id=sample_room_type.hotel_id)
    
    # Create Owner (for TC4)
    owner = User(username="owner_manage", email="owner@manage.com", password=pw_hash, role=UserRole.ADMIN, phone="0888888888", hotel_id=sample_room_type.hotel_id)
    test_db.session.add_all([recept, owner])
    test_db.session.commit()
    
    def _create(scenario):
        hotel = sample_room_type.hotel
        today = get_vn_time().date()
        
        status = BookingStatus.CONFIRMED
        check_in = today
        room_status = RoomStatus.AVAILABLE
        
        if scenario == 'confirmed_today':
            pass
        elif scenario == 'occupied':
            status = BookingStatus.CONFIRMED
            room_status = RoomStatus.OCCUPIED
        elif scenario == 'cancelled':
            status = BookingStatus.CANCELLED
        elif scenario == 'completed':
            status = BookingStatus.COMPLETED
            
        b = Booking(
            customer=sample_customer,
            hotel=hotel,
            room_type=sample_room_type,
            check_in=check_in,
            check_out=check_in + timedelta(days=2),
            total_price=3000000,
            status=status
        )
        test_db.session.add(b)
        test_db.session.commit()
        
        room = sample_rooms[0]
        room.status = room_status
        
        detail = BookingDetail(booking_id=b.id, room_id=room.id, price_at_booking=1500000)
        payment = Payment(booking_id=b.id, amount=b.total_price, transaction_id=str(uuid.uuid4())[:8], payment_method='MOMO')
        test_db.session.add(detail)
        test_db.session.add(payment)
        test_db.session.commit()
        
        return b.id
        
    return recept, owner, _create


@pytest.fixture(scope='function')
def specific_room_setup(test_session, sample_hotel):
    """Setup các loại phòng với tình trạng trống khác nhau"""
    
    # Loại phòng A: Còn trống 3 phòng
    rt_a = RoomType(hotel=sample_hotel, name="Room Type A", base_price=Decimal("1000000"), max_occupancy=2, bed_count=1)
    
    # Loại phòng B: Không còn phòng nào
    rt_b = RoomType(hotel=sample_hotel, name="Room Type B", base_price=Decimal("2000000"), max_occupancy=2, bed_count=1)
    
    # Loại phòng C: Có phòng bảo trì
    rt_c = RoomType(hotel=sample_hotel, name="Room Type C", base_price=Decimal("3000000"), max_occupancy=2, bed_count=1)
    
    test_session.add_all([rt_a, rt_b, rt_c])
    test_session.commit()
    
    rooms = [
        Room(room_type=rt_a, room_number="A1", status=RoomStatus.AVAILABLE),
        Room(room_type=rt_a, room_number="A2", status=RoomStatus.AVAILABLE),
        Room(room_type=rt_a, room_number="A3", status=RoomStatus.AVAILABLE),
        
        # rt_b có 1 phòng nhưng bị chiếm (OCCUPIED)
        Room(room_type=rt_b, room_number="B1", status=RoomStatus.OCCUPIED),
        
        # rt_c có 1 phòng bảo trì
        Room(room_type=rt_c, room_number="C1", status=RoomStatus.MAINTENANCE)
    ]
    test_session.add_all(rooms)
    test_session.commit()
    return rt_a, rt_b, rt_c


@pytest.fixture(scope='function')
def create_booking(test_db, sample_customer, sample_room_type, sample_rooms):
    def _create(scenario):
        hotel = sample_room_type.hotel
        today = get_vn_time().date()
        policy_days = hotel.cancellation_policy_days
        
        status = BookingStatus.CONFIRMED
        check_in = today + timedelta(days=10)
        
        if scenario == 'valid_far':
            check_in = today + timedelta(days=policy_days + 3)
        elif scenario == 'valid_edge':
            check_in = today + timedelta(days=policy_days)
        elif scenario == 'invalid_close':
            check_in = today + timedelta(days=policy_days - 1)
        elif scenario == 'checked_in':
            check_in = today - timedelta(days=1)
            status = BookingStatus.COMPLETED
        elif scenario == 'checked_out':
            check_in = today - timedelta(days=3)
            status = BookingStatus.COMPLETED
        elif scenario == 'cancelled':
            status = BookingStatus.CANCELLED
            
        b = Booking(
            customer=sample_customer,
            hotel=hotel,
            room_type=sample_room_type,
            check_in=check_in,
            check_out=check_in + timedelta(days=2),
            total_price=3000000,
            status=status
        )
        test_db.session.add(b)
        test_db.session.commit()
        
        detail = BookingDetail(booking_id=b.id, room_id=sample_rooms[0].id, price_at_booking=1500000)
        payment = Payment(booking_id=b.id, amount=b.total_price, transaction_id=str(uuid.uuid4())[:8], payment_method='MOMO')
        test_db.session.add(detail)
        test_db.session.add(payment)
        test_db.session.commit()
        
        return b.id
    return _create


