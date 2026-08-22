import pytest
from datetime import date, timedelta
from app.services.hotel_service import HotelService
from app.models import Hotel

@pytest.fixture
def hotel_service(test_session):
    """Khởi tạo HotelService với session từ Database thật"""
    return HotelService(db_session=test_session)

def test_get_hotel_by_id_success(hotel_service, sample_hotel):
    """Test lấy khách sạn theo ID hợp lệ"""
    hotel = hotel_service.get_hotel_by_id(sample_hotel.id)
    assert hotel is not None
    assert hotel.name == sample_hotel.name
    assert hotel.location == sample_hotel.location

def test_get_hotel_by_id_not_found(hotel_service):
    """Test lấy khách sạn với ID không tồn tại"""
    hotel = hotel_service.get_hotel_by_id(9999)
    assert hotel is None

def test_get_all_hotels(hotel_service, sample_hotel):
    """Test lấy danh sách tất cả khách sạn"""
    hotels = hotel_service.get_all_hotels()
    assert len(hotels) > 0
    # Đảm bảo sample_hotel có trong kết quả trả về
    assert any(h.id == sample_hotel.id for h in hotels)

def test_get_hotels_basic_filters(test_app, hotel_service, sample_hotel):
    """Test tìm kiếm khách sạn theo tên và địa điểm"""
    with test_app.test_request_context():
        # Tìm theo Location (sample_hotel có location='Khánh Hòa')
        pagination = hotel_service.get_hotels(location="Khánh Hòa")
        assert pagination.total > 0
        assert pagination.items[0].id == sample_hotel.id
        
        # Tìm theo Name (sample_hotel có name='Nha Trang Bay Hotel')
        pagination = hotel_service.get_hotels(name="Nha Trang")
        assert pagination.total > 0
        assert pagination.items[0].id == sample_hotel.id
        
        # Tìm không ra kết quả
        pagination = hotel_service.get_hotels(name="Hà Nội", location="Hà Nội")
        assert pagination.total == 0

def test_get_hotels_room_filters(test_app, hotel_service, sample_hotel, sample_room_type):
    """Test tìm kiếm khách sạn theo sức chứa và giá (capacity & price)"""
    with test_app.test_request_context():
        # sample_room_type có max_occupancy = 2, base_price = 1,500,000
        
        # Tìm sức chứa = 2
        pagination = hotel_service.get_hotels(capacity=2)
        assert pagination.total > 0
        
        # Tìm sức chứa = 10 (Sẽ không ra)
        pagination = hotel_service.get_hotels(capacity=10)
        assert pagination.total == 0
        
        # Tìm giá trong khoảng 1 triệu - 2 triệu
        pagination = hotel_service.get_hotels(min_price=1000000, max_price=2000000)
        assert pagination.total > 0

def test_get_hotels_with_availability(test_app, hotel_service, sample_hotel, sample_room_type, sample_rooms):
    """Test tìm kiếm khách sạn kèm theo check_in và check_out (còn phòng trống)"""
    with test_app.test_request_context():
        check_in = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        check_out = (date.today() + timedelta(days=3)).strftime('%Y-%m-%d')
        
        # Lúc này chưa có ai đặt nên sẽ tìm thấy khách sạn
        pagination = hotel_service.get_hotels(check_in=check_in, check_out=check_out)
        assert pagination.total > 0
