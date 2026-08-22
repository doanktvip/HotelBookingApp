import pytest
import json
from datetime import date, timedelta
from unittest.mock import patch
from app.services.ai_service import AIService

@pytest.fixture
def ai_service(test_session):
    """Khởi tạo AIService với session từ Database thật"""
    return AIService(db_session=test_session)

@patch('app.services.ai_service.call_gemini_api')
def test_parse_search_query_success(mock_call_gemini_api, test_app, ai_service, sample_tags):
    """Test AI phân tích câu tìm kiếm của người dùng"""
    # 1. Giả lập dữ liệu trả về từ Gemini API (để không cần gọi lên server thật tốn tiền/chờ lâu)
    mock_response = {
        "name": "Nha Trang Bay",
        "location": "Khánh Hòa",
        "min_price": None,
        "max_price": 2000000,
        "min_rating": 4.0,
        "capacity": 2,
        "bed_count": 1,
        "check_in": "2026-08-25",
        "check_out": "2026-08-27",
        "tag_ids": [sample_tags[0].id],
        "sort_by": "price_asc"
    }
    # Biến dict thành chuỗi JSON vì hàm call_gemini_api trả về string
    mock_call_gemini_api.return_value = json.dumps(mock_response)
    
    with test_app.test_request_context():
        # 2. Thực thi hàm
        result = ai_service.parse_search_query("Tìm khách sạn Nha Trang Bay ở Khánh Hòa giá dưới 2 triệu có wifi")
        
        # 3. Kiểm tra kết quả
        assert result is not None
        assert result["name"] == "Nha Trang Bay"
        assert result["location"] == "Khánh Hòa"
        assert result["max_price"] == 2000000
        # Đảm bảo hàm gọi API ảo đã được kích hoạt đúng 1 lần
        mock_call_gemini_api.assert_called_once()

@patch('app.services.ai_service.call_gemini_api')
def test_get_ai_recommendations_success(mock_call_gemini_api, test_app, ai_service, sample_customer, sample_hotel, sample_search_history, sample_booking):
    """Test AI gợi ý khách sạn cá nhân hóa"""
    # Giả lập AI chấm điểm và chọn khách sạn số 1
    mock_response = [
        {"hotel_id": sample_hotel.id, "match_score": 95}
    ]
    mock_call_gemini_api.return_value = json.dumps(mock_response)
    
    with test_app.test_request_context():
        # Dữ liệu mồi đầu vào
        candidates = [sample_hotel]
        recent_searches = [sample_search_history]
        recent_bookings = [sample_booking]
        
        recommendations = ai_service.get_ai_recommendations(
            user=sample_customer,
            candidates=candidates,
            recent_searches=recent_searches,
            recent_bookings=recent_bookings,
            limit=2
        )
        
        assert recommendations is not None
        assert len(recommendations) == 1
        assert recommendations[0].id == sample_hotel.id
        assert recommendations[0].match_score == 95
        mock_call_gemini_api.assert_called_once()

@patch('app.services.ai_service.call_gemini_api')
def test_generate_price_predictions_success(mock_call_gemini_api, test_app, ai_service, sample_hotel, sample_room_type, sample_rooms):
    """Test AI dự đoán điều chỉnh giá (Tăng/Giảm giá)"""
    target_date = date.today() + timedelta(days=1)
    
    # Giả lập AI bảo tăng giá 15% vào ngày mai vì đông khách
    mock_response = [
        {
            "hotel_id": sample_hotel.id,
            "target_date": target_date.strftime('%Y-%m-%d'),
            "adjustment_percentage": 0.15,
            "reason": "Dự báo cuối tuần đông khách"
        }
    ]
    mock_call_gemini_api.return_value = json.dumps(mock_response)
    
    with test_app.test_request_context():
        hotels = [sample_hotel]
        target_dates = [target_date]
        
        predictions = ai_service.generate_price_predictions(hotels, target_dates)
        
        assert predictions is not None
        assert len(predictions) == 1
        assert predictions[0]["hotel_id"] == sample_hotel.id
        assert predictions[0]["adjustment_percentage"] == 0.15
        assert predictions[0]["reason"] == "Dự báo cuối tuần đông khách"
        mock_call_gemini_api.assert_called_once()

def test_get_occupancy_data_for_ai(test_app, ai_service, sample_hotel, sample_rooms, sample_booking_details):
    """Test hàm tính toán Công suất phòng (Không đụng tới AI)"""
    with test_app.test_request_context():
        # Khách đặt phòng bắt đầu từ ngày mai (trong fixture sample_booking)
        target_date = date.today() + timedelta(days=1)
        
        # Tính toán công suất cho ngày mai
        data = ai_service.get_occupancy_data_for_ai([sample_hotel], [target_date])
        
        assert len(data) == 1
        assert data[0]["hotel_id"] == sample_hotel.id
        
        occupancy_forecast = data[0]["occupancy_forecast"]
        assert len(occupancy_forecast) == 1
        assert occupancy_forecast[0]["date"] == target_date.strftime('%Y-%m-%d')
        
        # Khách sạn sample có 3 phòng (sample_rooms)
        assert occupancy_forecast[0]["total_rooms"] == 3
        # Nhưng đã có 2 phòng bị khách đặt trong sample_booking_details
        assert occupancy_forecast[0]["booked_rooms"] == 2
        # Tỉ lệ 2/3 = 67%
        assert occupancy_forecast[0]["occupancy_rate"] == "67%"
