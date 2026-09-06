import pytest
from unittest.mock import patch
from datetime import date, timedelta
from app.services.prediction_service import PredictionService
from app.models import PricePrediction

@pytest.fixture
def prediction_service(test_session):
    return PredictionService(db_session=test_session)

def test_save_price_predictions(prediction_service, sample_hotel):
    target_date = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    validated_items = [
        {
            "hotel_id": sample_hotel.id,
            "target_date": target_date,
            "adjustment_percentage": 0.15,
            "reason": "Tăng giá cuối tuần"
        }
    ]
    
    # 1. Tạo mới dự đoán
    upsert_count = prediction_service.save_price_predictions(validated_items)
    assert upsert_count == 1
    
    pred = prediction_service.db.query(PricePrediction).first()
    assert float(pred.adjustment_percentage) == 0.15
    assert pred.is_applied is False
    
    # 2. Cập nhật dự đoán (khi chưa is_applied)
    validated_items[0]["adjustment_percentage"] = 0.20
    upsert_count2 = prediction_service.save_price_predictions(validated_items)
    assert upsert_count2 == 1
    
    prediction_service.db.refresh(pred)
    assert float(pred.adjustment_percentage) == 0.20
    
    # 3. Không cho phép cập nhật khi dự đoán đã được áp dụng vào giá phòng thực tế
    pred.is_applied = True
    prediction_service.commit_or_rollback()
    
    validated_items[0]["adjustment_percentage"] = 0.25
    upsert_count3 = prediction_service.save_price_predictions(validated_items)
    assert upsert_count3 == 0 # Sẽ bỏ qua, không update
    
    prediction_service.db.refresh(pred)
    assert float(pred.adjustment_percentage) == 0.20 # Giá trị vẫn giữ nguyên

@patch('app.services.prediction_service.AIService.generate_price_predictions')
def test_run_daily_prediction_job(mock_generate, test_app, prediction_service, sample_hotel):
    target_date = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Giả lập AI trả về 1 dự đoán
    mock_generate.return_value = [
        {
            "hotel_id": sample_hotel.id,
            "target_date": target_date,
            "adjustment_percentage": -0.10,
            "reason": "Giảm giá ngày ế ẩm"
        }
    ]
    
    with test_app.test_request_context():
        # Gọi hàm Cron Job chạy cho 1 ngày tới
        count = prediction_service.run_daily_prediction_job(interval=1)
        
        assert count == 1
        mock_generate.assert_called_once()
        
        # Kiểm tra DB xem đã được lưu thật chưa
        pred = prediction_service.db.query(PricePrediction).first()
        assert pred is not None
        assert float(pred.adjustment_percentage) == -0.10
