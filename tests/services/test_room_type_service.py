import pytest
from app.services.room_type_service import RoomTypeService
from app.models import RoomType

@pytest.fixture
def room_type_service(test_session):
    return RoomTypeService(db_session=test_session)

def test_get_room_type_by_id(room_type_service, sample_hotel, test_session):
    """Test lấy loại phòng theo ID"""
    rt = RoomType(hotel_id=sample_hotel.id, name="Deluxe Test", max_occupancy=2, bed_count=1, base_price=100000)
    test_session.add(rt)
    test_session.commit()
    
    result = room_type_service.get_room_type_by_id(rt.id)
    assert result is not None
    assert result.name == "Deluxe Test"
    
    result_none = room_type_service.get_room_type_by_id(99999)
    assert result_none is None

def test_get_room_types(test_app, room_type_service, sample_hotel, test_session):
    """Test lấy danh sách loại phòng có phân trang và lọc theo khách sạn"""
    rt1 = RoomType(hotel_id=sample_hotel.id, name="Deluxe 1", max_occupancy=2, bed_count=1, base_price=100000)
    rt2 = RoomType(hotel_id=sample_hotel.id, name="Deluxe 2", max_occupancy=2, bed_count=1, base_price=100000)
    rt3 = RoomType(hotel_id=999, name="Deluxe 3", max_occupancy=2, bed_count=1, base_price=100000) # Khách sạn lạ
    test_session.add_all([rt1, rt2, rt3])
    test_session.commit()
    
    with test_app.test_request_context():
        # Lấy các phòng thuộc sample_hotel
        paginated = room_type_service.get_room_types(hotel_id=sample_hotel.id, per_page=10)
        
        # Đảm bảo kết quả có chứa phòng 1, 2 nhưng không chứa phòng 3
        names = [rt.name for rt in paginated.items]
        assert "Deluxe 1" in names
        assert "Deluxe 2" in names
        assert "Deluxe 3" not in names
