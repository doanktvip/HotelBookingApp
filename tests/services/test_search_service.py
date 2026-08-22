import pytest
from unittest.mock import patch
from app.services.search_service import SearchService
from app.models import SearchHistory

@pytest.fixture
def search_service(test_session):
    """Khởi tạo SearchService với DB thật"""
    return SearchService(db_session=test_session)

@patch('app.services.search_service.AIService.parse_search_query')
def test_semantic_search_success(mock_parse, test_app, search_service, sample_hotel, sample_customer):
    """Test chức năng tìm kiếm ngữ nghĩa thành công"""
    # Mock AI bóc tách câu văn thành filters
    mock_parse.return_value = {
        "name": sample_hotel.name,
        "location": sample_hotel.location,
        "min_price": None,
        "max_price": None,
        "min_rating": None,
        "capacity": None,
        "bed_count": None,
        "check_in": None,
        "check_out": None,
        "tag_ids": [],
        "sort_by": None
    }
    
    with test_app.test_request_context():
        # Gọi tìm kiếm
        keyword = "Tìm khách sạn Nha Trang"
        pagination = search_service.semantic_search(keyword=keyword, user=sample_customer)
        
        # Kiểm tra kết quả có chứa sample_hotel không
        assert pagination is not None
        assert pagination.total > 0
        assert pagination.items[0].id == sample_hotel.id
        
        # Kiểm tra xem hệ thống đã lưu Lịch sử tìm kiếm vào DB chưa
        history = search_service.db.query(SearchHistory).filter_by(search_query=keyword).first()
        assert history is not None
        assert history.user_id == sample_customer.id
        assert history.is_useful is True

@patch('app.services.search_service.AIService.parse_search_query')
def test_semantic_search_no_useful_data(mock_parse, test_app, search_service):
    """Test khi người dùng nhập câu vô nghĩa không chứa điều kiện lọc"""
    # Mock AI không tìm thấy dữ liệu lọc nào
    mock_parse.return_value = {
        "name": None, "location": None, "min_price": None, "max_price": None,
        "min_rating": None, "capacity": None, "bed_count": None, 
        "check_in": None, "check_out": None, "tag_ids": [], "sort_by": None
    }
    
    with test_app.test_request_context():
        keyword = "Xin chào bạn khoẻ không"
        result = search_service.semantic_search(keyword=keyword)
        
        # Nếu vô nghĩa thì phải trả về None thay vì tìm kiếm
        assert result is None
        
        # Kiểm tra lịch sử vẫn được lưu nhưng is_useful = False
        history = search_service.db.query(SearchHistory).filter_by(search_query=keyword).first()
        assert history is not None
        assert history.is_useful is False

def test_save_search_history_duplicate(search_service, sample_customer):
    """Test chức năng lưu lịch sử không bị lưu trùng"""
    keyword = "khách sạn giá rẻ"
    
    # Lưu lần 1
    search_service.save_search_history(keyword, {"price": 100}, True, sample_customer.id)
    count1 = search_service.db.query(SearchHistory).filter_by(search_query=keyword).count()
    assert count1 == 1
    
    # Lưu lần 2 y hệt
    search_service.save_search_history(keyword, {"price": 100}, True, sample_customer.id)
    count2 = search_service.db.query(SearchHistory).filter_by(search_query=keyword).count()
    
    # Số lượng record vẫn phải là 1 (không tạo thêm)
    assert count2 == 1

def test_search_booking_in_recept(test_app, search_service, sample_hotel, sample_customer, sample_booking, sample_booking_details):
    """Test chức năng tìm kiếm Booking tại quầy Lễ tân"""
    with test_app.test_request_context():
        # 1. Tìm theo Mã Đặt Phòng (VD: BK-1)
        search_id = f"BK-{sample_booking.id}"
        pagination1 = search_service.search_booking_in_recept(sample_hotel.id, search_id)
        assert pagination1.total == 1
        assert pagination1.items[0].id == sample_booking.id
        
        # 2. Tìm theo Tên Khách Hàng
        pagination2 = search_service.search_booking_in_recept(sample_hotel.id, sample_customer.username)
        assert pagination2.total >= 1
        
        # 3. Tìm theo SĐT Khách Hàng
        pagination3 = search_service.search_booking_in_recept(sample_hotel.id, sample_customer.phone)
        assert pagination3.total >= 1
        
        # 4. Tìm tào lao (sẽ ra 0)
        pagination4 = search_service.search_booking_in_recept(sample_hotel.id, "NOBODYHERE")
        assert pagination4.total == 0
