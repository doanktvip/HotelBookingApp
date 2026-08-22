import os
import json
from datetime import datetime
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, Field
from typing import Optional, List
from app.utils import get_vn_time
from app.services import BaseService
from app.extensions import cache
from app.models import SearchHistory, Room, RoomType, Booking, BookingDetail, BookingStatus, PricePrediction, SystemConfig

class SearchQuerySchema(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    capacity: Optional[int] = None
    bed_count: Optional[int] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    tag_ids: List[int] = Field(default_factory=list)
    sort_by: Optional[str] = None

    def has_useful_data(self) -> bool:
        return any(v is not None and v != "" and v != [] for v in self.model_dump().values())

class HotelRecommendation(BaseModel):
    hotel_id: int
    match_score: int

class PricePredictionItem(BaseModel):
    hotel_id: int
    target_date: str # YYYY-MM-DD
    adjustment_percentage: float
    reason: str

@cache.memoize(timeout=86400)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=6))
def call_gemini_api(prompt, schema_name=None):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")
    
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(response_mime_type="application/json")
    
    if schema_name == "SearchQuery":
        config.response_schema = SearchQuerySchema
    elif schema_name == "Recommendations":
        config.response_schema = list[HotelRecommendation]
    elif schema_name == "PricePredictions":
        config.response_schema = list[PricePredictionItem]

    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=prompt,
        config=config
    )
    return response.text


class AIService(BaseService):
    def __init__(self, db_session):
        super().__init__(db_session)

    def parse_search_query(self, keyword):
        existing_history = self.db.query(SearchHistory).filter(
            SearchHistory.search_query.ilike(keyword),
            SearchHistory.parsed_data != None
        ).first()
        
        if existing_history:
            return existing_history.parsed_data

        tags = self.get_all_tags()
        tag_info = "\n".join([f"- ID: {tag.id}, Name: '{tag.name}'" for tag in tags])

        current_date = get_vn_time().strftime('%d-%m-%Y')

        prompt = f"""
                    Bạn là một chuyên gia phân tích dữ liệu hệ thống đặt phòng khách sạn. (Lệnh bỏ qua cache bộ nhớ)
                    Hôm nay là ngày: {current_date}.

                    Nhiệm vụ của bạn là phân tích câu nói của người dùng và trích xuất ra các biến điều kiện tìm kiếm.
                    Hãy trả về DUY NHẤT một cục JSON hợp lệ (không chứa markdown, không có thẻ ```json, KHÔNG chứa chú thích comment).

                    MÔ TẢ CÁC TRƯỜNG DỮ LIỆU:
                    - name: (string hoặc null) Tên riêng của khách sạn (VD: "Mường Thanh", "Vinpearl").
                    - location: (string hoặc null) Địa điểm, thành phố.
                    - min_price: (number hoặc null) Giá thấp nhất (VNĐ).
                    - max_price: (number hoặc null) Giá cao nhất (VNĐ). Lưu ý: "giá dưới X" thì X là max_price.
                    - min_rating: (number hoặc null) Số sao hoặc điểm thấp nhất (VD: 5.0).
                    - capacity: (number hoặc null) Số người.
                    - bed_count: (number hoặc null) Số giường.
                    - check_in: (string hoặc null) Ngày check-in YYYY-MM-DD.
                    - check_out: (string hoặc null) Ngày check-out YYYY-MM-DD.
                    - tag_ids: (danh sách số nguyên hoặc mảng rỗng []) ID của tiện ích (chỉ được chọn từ danh sách bên dưới).
                    - sort_by: (string hoặc null) "price_asc", "price_desc", hoặc "rating_desc". ("rẻ nhất" -> "price_asc").

                    VÍ DỤ CẤU TRÚC JSON CẦN TRẢ VỀ (CHỈ ĐƯỢC PHÉP TRẢ VỀ DẠNG NÀY):
                    {{
                        "name": null,
                        "location": "Vũng Tàu",
                        "min_price": null,
                        "max_price": 2000000,
                        "min_rating": 4.0,
                        "capacity": 4,
                        "bed_count": 2,
                        "check_in": "2026-08-10",
                        "check_out": "2026-08-12",
                        "tag_ids": [1, 3],
                        "sort_by": "price_asc"
                    }}

                    DANH SÁCH TIỆN ÍCH (TAGS) CHO PHÉP (Chỉ được chọn ID từ đây):
                    {tag_info}

                    Câu nói của người dùng: "{keyword}"
                    """

        try:
            response_text = call_gemini_api(prompt, "SearchQuery")
            parsed_data = json.loads(response_text)
            validated_data = SearchQuerySchema(**parsed_data).model_dump()
            return validated_data
        except Exception as e:
            print(f"Lỗi khi gọi Gemini API: {e}")
            cache.delete_memoized(call_gemini_api, prompt, "SearchQuery")
            return None


    def get_recommendation_data_for_ai(self, candidates, recent_searches, recent_bookings):
        candidate_data = []
        for h in candidates:
            tags_with_id = [{"id": t.id, "name": t.name} for t in h.tags]
            
            # Tính toán các thông số cao nhất từ các loại phòng đang hoạt động
            active_rooms = [rt for rt in h.room_types if rt.is_active]
            max_capacity = max((rt.max_occupancy for rt in active_rooms), default=0)
            max_bed_count = max((rt.bed_count for rt in active_rooms), default=0)
            max_price = max((float(rt.base_price) for rt in active_rooms), default=0)
            
            candidate_data.append({
                "hotel_id": h.id,
                "name": h.name,
                "location": h.location,
                "rating": h.rating,
                "tags": tags_with_id,
                "min_price": float(h.min_price) if h.min_price else 0,
                "max_price": max_price,
                "max_capacity": max_capacity,
                "max_bed_count": max_bed_count,
                "description": h.description
            })
            
        history_data = []
        for s in recent_searches:
            if s.parsed_data:
                history_data.append(s.parsed_data)
                
        booking_data = []
        for b in recent_bookings:
            if b.hotel and b.room_type:
                booking_data.append({
                    "hotel_name": b.hotel.name,
                    "location": b.hotel.location,
                    "room_type": b.room_type.name,
                    "price_paid": float(b.total_price),
                    "tags": [{"id": t.id, "name": t.name} for t in b.hotel.tags]
                })
        return candidate_data, history_data, booking_data

    def get_ai_recommendations(self, user, candidates, recent_searches, recent_bookings, limit=4):
        if not candidates:
            return []
            
        candidate_data, history_data, booking_data = self.get_recommendation_data_for_ai(candidates, recent_searches, recent_bookings)
                
        user_context = "KHÁCH CHƯA ĐĂNG NHẬP (GUEST)"
        if user:
            user_context = f"KHÁCH ĐÃ ĐĂNG NHẬP (Username: {user.username})"

        prompt = f"""
        Bạn là một chuyên gia Hệ thống Gợi ý Khách sạn (Recommendation System AI).
        Người dùng hiện tại: {user_context}.
        
        Đây là dữ liệu Lịch sử Tìm kiếm (Search History):
        {json.dumps(history_data, ensure_ascii=False)}
        
        Đây là dữ liệu Lịch sử Đặt phòng thành công (Booking History):
        {json.dumps(booking_data, ensure_ascii=False)}
        
        (Lưu ý: Nếu KHÁCH CHƯA ĐĂNG NHẬP, lịch sử tìm kiếm trên là XU HƯỚNG ĐÁM ĐÔNG. Nếu KHÁCH ĐÃ ĐĂNG NHẬP, đó là lịch sử CÁ NHÂN. Lịch sử Đặt phòng là ưu tiên cao nhất để hiểu gu của khách hàng).
        
        Dưới đây là danh sách {len(candidates)} khách sạn ứng viên (Candidates) đã qua vòng sơ loại bằng SQL:
        {json.dumps(candidate_data, ensure_ascii=False)}
        
        NHIỆM VỤ CỦA BẠN:
        1. Phân tích lịch sử tìm kiếm để hiểu sở thích (nếu là cá nhân) hoặc xu hướng (nếu là đám đông).
        2. Chọn ra đúng {limit} khách sạn phù hợp nhất từ danh sách Candidates.
        3. Tự tính toán điểm phần trăm phù hợp (match_score, từ 60 đến 100) cho từng khách sạn được chọn dựa trên mức độ đáp ứng nhu cầu.
        
        YÊU CẦU ĐẦU RA:
        Trả về DUY NHẤT một mảng JSON (Array) chứa danh sách các khách sạn được chọn.
        - KHÔNG bọc trong thẻ markdown ```json.
        - KHÔNG chứa chú thích (comment) hay bất kỳ văn bản nào khác.
        
        VÍ DỤ CẤU TRÚC JSON TRẢ VỀ (Chỉ lấy hotel_id thực tế từ danh sách Candidates):
        [
            {{"hotel_id": 123, "match_score": 95}},
            {{"hotel_id": 456, "match_score": 88}}
        ]
        """
        
        try:
            response_text = call_gemini_api(prompt, "Recommendations")
            parsed_data = json.loads(response_text)
            validated_items = [HotelRecommendation(**item).model_dump() for item in parsed_data]
            
            final_hotels = []
            hotel_map = {h.id: h for h in candidates}
            
            for item in validated_items:
                h_id = item["hotel_id"]
                if h_id in hotel_map:
                    hotel = hotel_map[h_id]
                    hotel.match_score = item["match_score"]
                    final_hotels.append(hotel)
                    
            if len(final_hotels) == 0:
                raise ValueError("AI trả về danh sách rỗng hoặc sai format ID")
                
            return final_hotels[:limit]
            
        except Exception as e:
            cache.delete_memoized(call_gemini_api, prompt, "Recommendations")
            return None

    def get_occupancy_data_for_ai(self, hotels, target_dates):
        hotel_data_for_ai = []
        for hotel in hotels:
            total_rooms = self.db.query(Room).join(Room.room_type).filter(
                RoomType.hotel_id == hotel.id,
                Room.is_active == True
            ).count()
            
            if total_rooms == 0:
                continue
                
            occupancy_data = []
            for target_date in target_dates:
                booked_rooms = self.db.query(BookingDetail.room_id).join(Booking).filter(
                    Booking.hotel_id == hotel.id,
                    Booking.status == BookingStatus.CONFIRMED,
                    Booking.check_in <= target_date,
                    Booking.check_out > target_date
                ).count()
                
                occupancy_rate = (booked_rooms / total_rooms) if total_rooms > 0 else 0
                
                occupancy_data.append({
                    "date": target_date.strftime('%Y-%m-%d'),
                    "total_rooms": total_rooms,
                    "booked_rooms": booked_rooms,
                    "occupancy_rate": f"{occupancy_rate:.0%}"
                })
                
            hotel_data_for_ai.append({
                "hotel_id": hotel.id,
                "hotel_name": hotel.name,
                "location": hotel.location,
                "occupancy_forecast": occupancy_data
            })
            
        return hotel_data_for_ai

    def generate_price_predictions(self, hotels, target_dates):
        hotel_data_for_ai = self.get_occupancy_data_for_ai(hotels, target_dates)
            
        if not hotel_data_for_ai:
            return 0
            
        max_adj = SystemConfig.get_value('MAX_PRICE_ADJUSTMENT_PERCENTAGE', 20, type_func=int)
        min_adj = -max_adj
        
        prompt = f"""
        Bạn là một Giám đốc Doanh thu (Revenue Manager) chuyên nghiệp cho chuỗi khách sạn.
        Dưới đây là dữ liệu dự báo công suất phòng (Occupancy Rate) trong thời gian tới của các khách sạn:
        
        {json.dumps(hotel_data_for_ai, ensure_ascii=False)}
        
        NHIỆM VỤ CỦA BẠN:
        Phân tích công suất phòng, thời điểm (mùa, lễ, cuối tuần) và vị trí của từng khách sạn để đưa ra quyết định ĐIỀU CHỈNH GIÁ.
        
        LƯU Ý CỰC KỲ QUAN TRỌNG (HẠN MỨC ĐỀ XUẤT):
        - BẠN CHỈ ĐƯỢC PHÉP CHỌN RA TỐI ĐA 20 TRƯỜNG HỢP CẦN THIẾT NHẤT ĐỂ ĐIỀU CHỈNH GIÁ.
        - Hãy ưu tiên những ngày/khách sạn có công suất cực cao (cần tăng giá) hoặc cực thấp (cần giảm giá) để tối ưu doanh thu nhất.
        - BỎ QUA hoàn toàn những trường hợp công suất ở mức trung bình ổn định (không cần điều chỉnh).
        
        QUY TẮC ĐIỀU CHỈNH (CHO NHỮNG TRƯỜNG HỢP ĐƯỢC CHỌN):
        - Nếu công suất phòng rất cao (>80%) hoặc rơi vào cuối tuần/ngày lễ tại khu du lịch: Hãy tăng giá (từ 0.1 đến {max_adj/100} tương đương 10% đến {max_adj}%).
        - Nếu công suất phòng thấp (<30%) hoặc ngày giữa tuần ế ẩm: Hãy giảm giá (từ -0.05 đến {min_adj/100} tương đương giảm 5% đến {max_adj}%).
        
        Trả về kết quả dưới dạng mảng JSON (TỐI ĐA 20 PHẦN TỬ) gồm các Object với các trường:
        - hotel_id: ID của khách sạn
        - target_date: Ngày áp dụng (YYYY-MM-DD)
        - adjustment_percentage: Tỉ lệ điều chỉnh (ví dụ 0.15 là tăng 15%, -0.1 là giảm 10%)
        - reason: Lý do ngắn gọn giải thích quyết định của bạn.
        """
        
        try:
            response_text = call_gemini_api(prompt, "PricePredictions")
            parsed_data = json.loads(response_text)
            
            validated_items = [PricePredictionItem(**item).model_dump() for item in parsed_data]
            
            return validated_items
            
        except Exception as e:
            cache.delete_memoized(call_gemini_api, prompt, "PricePredictions")
            return []
