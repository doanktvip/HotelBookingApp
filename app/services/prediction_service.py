from app.services import BaseService
from app.models import PricePrediction, SystemConfig
from app.services.ai_service import AIService
from app.services.hotel_service import HotelService
from app.utils import get_vn_time
from datetime import datetime, timedelta

class PredictionService(BaseService):
    def save_price_predictions(self, validated_items):
        if not validated_items:
            return 0
            
        upsert_count = 0
        
        hotel_ids = list(set(item['hotel_id'] for item in validated_items))
        target_dates = list(set(datetime.strptime(item['target_date'], '%Y-%m-%d').date() for item in validated_items))
        
        existing_preds = self.db.query(PricePrediction).filter(
            PricePrediction.hotel_id.in_(hotel_ids),
            PricePrediction.target_date.in_(target_dates)
        ).all()
        
        pred_dict = {(p.hotel_id, p.target_date): p for p in existing_preds}
        
        for item in validated_items:
            target_date_obj = datetime.strptime(item['target_date'], '%Y-%m-%d').date()
            hotel_id = item['hotel_id']
            
            existing_pred = pred_dict.get((hotel_id, target_date_obj))
            
            if not existing_pred:
                new_pred = PricePrediction(
                    hotel_id=hotel_id,
                    target_date=target_date_obj,
                    adjustment_percentage=item['adjustment_percentage'],
                    reason=item['reason'],
                    is_applied=False
                )
                self.db.add(new_pred)
                upsert_count += 1
            elif not existing_pred.is_applied:
                existing_pred.adjustment_percentage = item['adjustment_percentage']
                existing_pred.reason = item['reason']
                upsert_count += 1
            
        self.commit_or_rollback()
        return upsert_count

    def run_daily_prediction_job(self, interval):
        hotel_service = HotelService(self.db)
        hotels = hotel_service.get_all_hotels()
        
        today = get_vn_time().date()
        target_dates = [today + timedelta(days=i) for i in range(1, interval + 1)]
        
        ai_service = AIService(self.db)
        predictions = ai_service.generate_price_predictions(hotels, target_dates)
        
        return self.save_price_predictions(predictions)
