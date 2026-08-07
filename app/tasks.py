from app.extensions import db, scheduler
from app.models import SystemConfig
from app.services.prediction_service import PredictionService

def daily_price_prediction_job():
    with scheduler.app.app_context():
        try:
            print("[Scheduler] Bắt đầu chạy dự báo giá động hàng ngày...")
            interval=SystemConfig.get_value('AI_PREDICTION_INTERVAL', 7, type_func=int)
            prediction_service = PredictionService(db.session)
            upsert_count = prediction_service.run_daily_prediction_job(interval)
            
            print(f"[Scheduler] Đã hoàn tất dự báo cho {upsert_count} ngày/khách sạn.")
        except Exception as e:
            print(f"[Scheduler] Lỗi khi chạy dự báo: {e}")
