import pytest
from unittest.mock import patch
from app.services.recommendation_service import RecommendationService
from app.models import SearchHistory, BookingStatus

@pytest.fixture
def recommendation_service(test_session):
    return RecommendationService(db_session=test_session)

@patch('app.services.recommendation_service.AIService.get_ai_recommendations')
def test_get_recommended_hotels(mock_ai, test_app, recommendation_service, sample_customer, sample_hotel, sample_booking):
    # Mock AI vì không muốn gọi API thật
    mock_ai.return_value = [sample_hotel]
    
    # 1. Bơm lịch sử tìm kiếm vào DB
    history = SearchHistory(
        user_id=sample_customer.id,
        search_query="Khách sạn giá rẻ ở Đà Lạt",
        parsed_data={"location": "Đà Lạt", "max_price": 500000},
        is_useful=True
    )
    recommendation_service.db.add(history)
    
    # 2. Ép sample_booking thành COMPLETED để hệ thống tính nó vào Lịch sử đặt phòng
    sample_booking.status = BookingStatus.COMPLETED
    recommendation_service.commit_or_rollback()
    
    with test_app.test_request_context():
        # Gọi hàm gợi ý chính
        hotels = recommendation_service.get_recommended_hotels(user=sample_customer, limit=4)
        
        # Kết quả cuối cùng phải do AI quyết định (trả về 1 khách sạn theo mock)
        assert len(hotels) == 1
        assert hotels[0].id == sample_hotel.id
        mock_ai.assert_called_once()
        
        # Đảm bảo phần SQL chạy ngầm phải rút trích đúng dữ liệu lịch sử
        valid_searches = recommendation_service._get_valid_searches(sample_customer)
        assert len(valid_searches) == 1
        assert valid_searches[0].parsed_data["location"] == "Đà Lạt"
        
        recent_bookings = recommendation_service._get_recent_bookings(sample_customer.id)
        assert len(recent_bookings) == 1
        
        candidates = recommendation_service.get_sql_candidates(valid_searches, recent_bookings)
        assert len(candidates) >= 1
