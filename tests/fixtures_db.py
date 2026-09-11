import pytest
from datetime import date, timedelta
from decimal import Decimal
import hashlib
from app.models import (
    User, UserRole, Hotel, RoomType, Room, RoomStatus, Floor,
    Booking, BookingStatus, BookingDetail, Payment, PaymentMethod, PaymentStatus,
    Tag, SystemConfig, OTP, PricePrediction, SearchHistory, PriceHistory
)
import uuid
from app.utils import get_vn_time
PASSWORD='123456'

@pytest.fixture(scope='function')
def sample_customer(test_session):
    user = User(
        username="customer",
        email="customer@gmail.com",
        password=str(hashlib.md5(PASSWORD.strip().encode('utf-8')).hexdigest()),
        role=UserRole.CUSTOMER,
        is_verified=True
    )
    cust_a = User(username='Nguyễn Văn A', email='nguyenvana@hotel.com', phone='012345678', password=str(hashlib.md5(PASSWORD.encode('utf-8')).hexdigest()), role=UserRole.CUSTOMER, is_verified=True)
    cust_b = User(username='Trần Thị B', email='tranthib@hotel.com', phone='098765432', password=str(hashlib.md5(PASSWORD.encode('utf-8')).hexdigest()), role=UserRole.CUSTOMER, is_verified=True)
    cust_c = User(username='Lê Văn C', email='levanc@hotel.com', phone='0333444555', password=str(hashlib.md5(PASSWORD.encode('utf-8')).hexdigest()), role=UserRole.CUSTOMER, is_verified=True)
    cust_d = User(username='Phạm Văn D', email='phamvand@hotel.com', phone='0777888999', password=str(hashlib.md5(PASSWORD.encode('utf-8')).hexdigest()), role=UserRole.CUSTOMER, is_verified=True)
    cust2 = User(username='Trần Văn Bình', email='binh@gmail.com', phone='0987654321', password=str(hashlib.md5(PASSWORD.encode('utf-8')).hexdigest()), role=UserRole.CUSTOMER, is_verified=True)
    
    test_session.add_all([user, cust_a, cust_b, cust_c, cust_d, cust2])
    test_session.commit()
    return user


@pytest.fixture(scope='function')
def sample_admin(test_session, sample_hotel):
    user = User(
        username="admin",
        email="admin@hotel.com",
        password=str(hashlib.md5(PASSWORD.strip().encode('utf-8')).hexdigest()),
        role=UserRole.ADMIN,
        hotel_id=sample_hotel.id,
        is_verified=True
    )
    test_session.add(user)
    test_session.commit()
    return user


@pytest.fixture(scope='function')
def sample_receptionist(test_session):
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
    config = SystemConfig(
        config_key="MAX_ROOMS_PER_BOOKING",
        config_value="5",
        description="Số lượng phòng tối đa được phép đặt trong 1 đơn"
    )
    test_session.add(config)
    test_session.commit()
    return config


@pytest.fixture(scope='function')
def sample_hotel(test_session, sample_tags, sample_receptionist):
    hotel = Hotel(
        name="Nha Trang Bay Hotel",
        address="01 Trần Phú",
        location="Khánh Hòa",
        description="Khách sạn view biển đẹp nhất",
        rating=4.5,
        cancellation_policy_days=3
    )
    hotel.tags.extend(sample_tags)
    test_session.add(hotel)
    test_session.commit()
    
    sample_receptionist.hotel_id = hotel.id
    test_session.commit()
    
    return hotel


@pytest.fixture(scope='function')
def sample_room_type(test_session, sample_hotel):
    room_type = RoomType(
        hotel=sample_hotel,
        name="Deluxe Ocean View",
        description="Phòng rộng 40m2, view biển trực diện",
        base_price=Decimal("1500000.00"),
        max_occupancy=2,
        bed_count=1,
        bed_type="Giường đôi cực lớn"
    )
    rt_suite = RoomType(
        hotel=sample_hotel, name="Suite Gia Đình", description="Phòng Suite rộng rãi", 
        base_price=Decimal("2500000.00"), max_occupancy=4, bed_count=2, bed_type="2 Queen Beds", is_active=True
    )
    test_session.add_all([room_type, rt_suite])
    test_session.commit()
    return room_type


@pytest.fixture(scope='function')
def sample_rooms(test_session, sample_room_type):
    hotel = sample_room_type.hotel
    rt_suite = test_session.query(RoomType).filter_by(name="Suite Gia Đình").first()
    
    floor_3 = Floor(hotel_id=hotel.id, floor_number=3, name="Tầng 3")
    test_session.add(floor_3)
    test_session.commit()
    
    rooms = [
        Room(room_type_id=sample_room_type.id, room_number="101", floor=1, status=RoomStatus.OCCUPIED),
        Room(room_type_id=sample_room_type.id, room_number="102", floor=2, status=RoomStatus.AVAILABLE),
        Room(room_type_id=sample_room_type.id, room_number="103", floor=3, status=RoomStatus.OCCUPIED),
        Room(room_type_id=sample_room_type.id, room_number="P104", floor=1, status=RoomStatus.AVAILABLE),
        Room(room_type_id=rt_suite.id, room_number="P302", floor=3, floor_id=floor_3.id, status=RoomStatus.OCCUPIED)
    ]
    test_session.add_all(rooms)
    test_session.commit()
    return rooms

@pytest.fixture(scope='function')
def sample_booking(test_session, sample_customer, sample_room_type, sample_rooms):
    hotel = sample_room_type.hotel
    today = get_vn_time().date()
    
    check_in = date.today() + timedelta(days=1)
    check_out = check_in + timedelta(days=2)
    
    # Main Booking
    b_main = Booking(
        customer=sample_customer, hotel=hotel, room_type=sample_room_type,
        check_in=check_in, check_out=check_out, total_price=Decimal("6000000.00"), status=BookingStatus.CONFIRMED
    )
    test_session.add(b_main)
    test_session.commit()
    
    cust_a = test_session.query(User).filter_by(username="Nguyễn Văn A").first()
    cust_b = test_session.query(User).filter_by(username="Trần Thị B").first()
    cust_c = test_session.query(User).filter_by(username="Lê Văn C").first()
    cust_d = test_session.query(User).filter_by(username="Phạm Văn D").first()
    cust2 = test_session.query(User).filter_by(username="Trần Văn Bình").first()
    rt_suite = test_session.query(RoomType).filter_by(name="Suite Gia Đình").first()
    
    r101, r102, r103, r104, rp302 = sample_rooms[0], sample_rooms[1], sample_rooms[2], sample_rooms[3], sample_rooms[4]
    
    # Owner manage booking
    b_owner_1 = Booking(user_id=sample_customer.id, hotel_id=hotel.id, room_type_id=sample_room_type.id, check_in=date(2026, 9, 15), check_out=date(2026, 9, 18), total_price=Decimal("4500000.00"), status=BookingStatus.CONFIRMED)
    b_owner_2 = Booking(user_id=cust2.id, hotel_id=hotel.id, room_type_id=rt_suite.id, check_in=today - timedelta(days=1), check_out=today + timedelta(days=2), total_price=Decimal("7500000.00"), status=BookingStatus.CONFIRMED)
    
    # Check-in / Checkout
    bk_in_use = Booking(user_id=sample_customer.id, hotel_id=hotel.id, room_type_id=sample_room_type.id, check_in=today - timedelta(days=1), check_out=today + timedelta(days=1), total_price=Decimal("2000000.00"), status=BookingStatus.CONFIRMED)
    bk_confirmed = Booking(user_id=sample_customer.id, hotel_id=hotel.id, room_type_id=sample_room_type.id, check_in=today, check_out=today + timedelta(days=2), total_price=Decimal("2000000.00"), status=BookingStatus.CONFIRMED)
    bk_cancelled = Booking(user_id=sample_customer.id, hotel_id=hotel.id, room_type_id=sample_room_type.id, check_in=today, check_out=today + timedelta(days=2), total_price=Decimal("2000000.00"), status=BookingStatus.CANCELLED)
    bk_unpaid = Booking(user_id=sample_customer.id, hotel_id=hotel.id, room_type_id=sample_room_type.id, check_in=today - timedelta(days=2), check_out=today + timedelta(days=1), total_price=Decimal("3000000.00"), status=BookingStatus.CONFIRMED)
    
    # Reception search
    b_search_1 = Booking(user_id=cust_a.id, hotel_id=hotel.id, room_type_id=sample_room_type.id, check_in=today - timedelta(days=2), check_out=today + timedelta(days=2), total_price=Decimal("4000000.00"), status=BookingStatus.CONFIRMED)
    b_search_2 = Booking(user_id=cust_b.id, hotel_id=hotel.id, room_type_id=sample_room_type.id, check_in=today, check_out=today + timedelta(days=2), total_price=Decimal("2000000.00"), status=BookingStatus.CONFIRMED)
    b_search_3 = Booking(user_id=cust_c.id, hotel_id=hotel.id, room_type_id=sample_room_type.id, check_in=today - timedelta(days=1), check_out=today, total_price=Decimal("1000000.00"), status=BookingStatus.CONFIRMED)
    b_search_4 = Booking(user_id=cust_d.id, hotel_id=hotel.id, room_type_id=sample_room_type.id, check_in=today + timedelta(days=5), check_out=today + timedelta(days=7), total_price=Decimal("2000000.00"), status=BookingStatus.CONFIRMED)
    
    # Room availability states boundary
    b_boundary_1 = Booking(user_id=sample_customer.id, hotel_id=hotel.id, room_type_id=sample_room_type.id, check_in=date(2026, 10, 10), check_out=date(2026, 10, 12), total_price=Decimal("2400000.00"), status=BookingStatus.CONFIRMED)
    b_boundary_2 = Booking(user_id=sample_customer.id, hotel_id=hotel.id, room_type_id=sample_room_type.id, check_in=date(2026, 10, 12), check_out=date(2026, 10, 14), total_price=Decimal("3000000.00"), status=BookingStatus.CONFIRMED)
    b_bound_cancelled = Booking(user_id=sample_customer.id, hotel_id=hotel.id, room_type_id=sample_room_type.id, check_in=today + timedelta(days=5), check_out=today + timedelta(days=7), total_price=Decimal("3000000.00"), status=BookingStatus.CANCELLED)

    test_session.add_all([b_owner_1, b_owner_2, bk_in_use, bk_confirmed, bk_cancelled, bk_unpaid, b_search_1, b_search_2, b_search_3, b_search_4, b_boundary_1, b_boundary_2, b_bound_cancelled])
    test_session.commit()

    # Create BookingDetails and Payments
    details = [
        BookingDetail(booking_id=b_owner_1.id, room_id=r101.id, price_at_booking=sample_room_type.base_price),
        BookingDetail(booking_id=b_owner_2.id, room_id=rp302.id, price_at_booking=rt_suite.base_price),
        
        BookingDetail(booking_id=bk_in_use.id, room_id=r101.id, price_at_booking=Decimal('1000000.00')),
        BookingDetail(booking_id=bk_confirmed.id, room_id=r102.id, price_at_booking=Decimal('1000000.00')),
        BookingDetail(booking_id=bk_unpaid.id, room_id=r103.id, price_at_booking=Decimal('1000000.00')),
        
        BookingDetail(booking_id=b_search_1.id, room_id=r101.id, price_at_booking=sample_room_type.base_price),
        BookingDetail(booking_id=b_search_2.id, room_id=r102.id, price_at_booking=sample_room_type.base_price),
        BookingDetail(booking_id=b_search_3.id, room_id=r103.id, price_at_booking=sample_room_type.base_price),
        BookingDetail(booking_id=b_search_4.id, room_id=r104.id, price_at_booking=sample_room_type.base_price),
        
        BookingDetail(booking_id=b_boundary_1.id, room_id=r101.id, price_at_booking=sample_room_type.base_price),
        BookingDetail(booking_id=b_boundary_2.id, room_id=r102.id, price_at_booking=sample_room_type.base_price),
        BookingDetail(booking_id=b_bound_cancelled.id, room_id=r103.id, price_at_booking=sample_room_type.base_price)
    ]
    
    payments = [
        Payment(booking_id=bk_in_use.id, amount=Decimal('2000000.00'), payment_method=PaymentMethod.MOMO, status=PaymentStatus.SUCCESS, transaction_id=f'TRANS_USE_{bk_in_use.id}'),
        Payment(booking_id=bk_confirmed.id, amount=Decimal('2000000.00'), payment_method=PaymentMethod.MOMO, status=PaymentStatus.SUCCESS, transaction_id=f'TRANS_CONF_{bk_confirmed.id}'),
        Payment(booking_id=bk_unpaid.id, amount=Decimal('1000000.00'), payment_method=PaymentMethod.MOMO, status=PaymentStatus.PENDING, transaction_id=f'TRANS_UNP_{bk_unpaid.id}')
    ]
    
    test_session.add_all(details)
    test_session.add_all(payments)
    test_session.commit()

    return b_main


@pytest.fixture(scope='function')
def sample_booking_details(test_session, sample_booking, sample_rooms):
    assigned_rooms = sample_rooms[:2]
    
    details = []
    for room in assigned_rooms:
        bd = BookingDetail(
            booking=sample_booking,
            room=room,
            price_at_booking=sample_booking.room_type.base_price
        )
        details.append(bd)
        room.status = RoomStatus.BOOKED

    test_session.add_all(details)
    test_session.commit()
    return details


@pytest.fixture(scope='function')
def sample_payment(test_session, sample_booking):
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


@pytest.fixture(scope='function')
def sample_otp(test_session, sample_customer):
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
    history = PriceHistory(
        room_type_id=sample_room_type.id,
        old_price=Decimal("1200000.00"),
        new_price=Decimal("1500000.00")
    )
    test_session.add(history)
    test_session.commit()
    return history




@pytest.fixture(scope='function')
def setup_recept_data(test_db, sample_customer, sample_room_type, sample_rooms):
    pw_hash = str(hashlib.md5("123456".encode('utf-8')).hexdigest())
    recept = User(username="receptionist_manage", email="recept@manage.com", password=pw_hash, role=UserRole.RECEPTIONIST, phone="0999999999", hotel_id=sample_room_type.hotel_id)
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
        payment = Payment(booking_id=b.id, amount=b.total_price, transaction_id=str(uuid.uuid4())[:8], payment_method='MOMO', status=PaymentStatus.SUCCESS)
        test_db.session.add(detail)
        test_db.session.add(payment)
        test_db.session.commit()
        return b.id
    return recept, owner, _create

@pytest.fixture(scope='function')
def specific_room_setup(test_session, sample_hotel):
    rt_a = RoomType(hotel=sample_hotel, name="Room Type A", base_price=Decimal("1000000"), max_occupancy=2, bed_count=1)
    rt_b = RoomType(hotel=sample_hotel, name="Room Type B", base_price=Decimal("2000000"), max_occupancy=2, bed_count=1)
    rt_c = RoomType(hotel=sample_hotel, name="Room Type C", base_price=Decimal("3000000"), max_occupancy=2, bed_count=1)
    test_session.add_all([rt_a, rt_b, rt_c])
    test_session.commit()
    
    rooms = [
        Room(room_type=rt_a, room_number="A1", status=RoomStatus.AVAILABLE),
        Room(room_type=rt_a, room_number="A2", status=RoomStatus.AVAILABLE),
        Room(room_type=rt_a, room_number="A3", status=RoomStatus.AVAILABLE),
        Room(room_type=rt_b, room_number="B1", status=RoomStatus.OCCUPIED),
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
