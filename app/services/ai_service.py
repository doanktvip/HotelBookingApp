import os
import json
import re
import google.generativeai as genai
from app.utils import get_vn_time
from app.services import BaseService
from app.extensions import cache
from app.models import SearchHistory

@cache.memoize(timeout=86400)
def call_gemini_api(prompt):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.5-flash')
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json"
        )
    )
    return response.text

def extract_json(text):
    """Trích xuất mảng JSON hoặc Object JSON bao trọn cả chuỗi kết quả (Bỏ qua mọi rác xung quanh)"""
    text = text.strip()
    
    # Làm sạch thẻ markdown trước (nếu có)
    if text.startswith("```"):
        text = re.sub(r'^```[a-zA-Z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        text = text.strip()

    # Thử parse trực tiếp trước
    try:
        json.loads(text)
        return text
    except:
        pass

    # Dùng regex để bóc tách block JSON (Object hoặc Array) lớn nhất
    # match.group(1) sẽ lấy từ dấu ngoặc mở đầu tiên đến dấu ngoặc đóng tương ứng
    match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if match:
        extracted = match.group(1)
        try:
            json.loads(extracted)
            return extracted
        except:
            pass

    return text

class AIService(BaseService):
    def __init__(self, db_session):
        super().__init__(db_session)

    def parse_search_query(self, keyword):
        # 1. Kiểm tra Database xem đã có ai từng tìm câu này chưa (Database Caching)
        existing_history = self.db.query(SearchHistory).filter(
            SearchHistory.search_query.ilike(keyword),
            SearchHistory.parsed_data != None
        ).first()
        
        if existing_history:
            print("Lấy kết quả từ Database SearchHistory, không gọi AI!")
            return existing_history.parsed_data

        # 2. Nếu chưa có, mới bắt đầu lấy Tags và gọi AI
        tags = self.get_all_tags()
        tag_info = "\n".join([f"- ID: {tag.id}, Name: '{tag.name}'" for tag in tags])

        current_date = get_vn_time().strftime('%Y-%m-%d')

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
            response_text = call_gemini_api(prompt)
            clean_text = extract_json(response_text)
            parsed_data = json.loads(clean_text)
            
            if not isinstance(parsed_data, dict):
                raise ValueError("JSON trả về không phải là Object/Dict")
                
            return parsed_data
        except Exception as e:
            print(f"Lỗi khi gọi Gemini API: {e}")
            # Xóa cache ngay lập tức nếu dữ liệu trả về bị lỗi (để lần sau gọi lại LLM)
            cache.delete_memoized(call_gemini_api, prompt)
            return None

    def save_search_history(self, keyword, parsed_data, user_id=None):
        history = SearchHistory(
            user_id=user_id,
            search_query=keyword,
            parsed_data=parsed_data
        )
        self.db.add(history)
        try:
            self.commit_or_rollback()
        except Exception as e:
            print(f"Lỗi khi lưu Search History: {e}")

    def get_ai_recommendations(self, user, candidates, recent_searches, limit=4):
        if not candidates:
            return []
            
        candidate_data = []
        for h in candidates:
            tags = [t.name for t in h.tags]
            candidate_data.append({
                "hotel_id": h.id,
                "name": h.name,
                "location": h.location,
                "rating": h.rating,
                "tags": tags,
                "min_price": float(h.min_price) if h.min_price else 0
            })
            
        history_data = []
        for s in recent_searches:
            if s.parsed_data:
                history_data.append(s.parsed_data)
                
        user_context = "KHÁCH CHƯA ĐĂNG NHẬP (GUEST)"
        if user:
            user_context = f"KHÁCH ĐÃ ĐĂNG NHẬP (Username: {user.username})"

        prompt = f"""
        Bạn là một chuyên gia Hệ thống Gợi ý Khách sạn (Recommendation System AI).
        Người dùng hiện tại: {user_context}.
        
        Đây là dữ liệu Lịch sử Tìm kiếm (Search History):
        {json.dumps(history_data, ensure_ascii=False)}
        
        (Lưu ý: Nếu KHÁCH CHƯA ĐĂNG NHẬP, lịch sử tìm kiếm trên là XU HƯỚNG ĐÁM ĐÔNG của tất cả mọi người. Nếu KHÁCH ĐÃ ĐĂNG NHẬP, đó là lịch sử CÁ NHÂN CỦA HỌ).
        
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
            response_text = call_gemini_api(prompt)
            clean_text = extract_json(response_text)
            recommended_items = json.loads(clean_text)
            
            final_hotels = []
            hotel_map = {h.id: h for h in candidates}
            
            for item in recommended_items:
                h_id = item.get("hotel_id")
                if h_id in hotel_map:
                    hotel = hotel_map[h_id]
                    hotel.match_score = item.get("match_score", 0)
                    final_hotels.append(hotel)
                    
            if len(final_hotels) == 0:
                raise ValueError("AI trả về danh sách rỗng hoặc sai format ID")
                
            return final_hotels[:limit]
            
        except Exception as e:
            print(f"Lỗi AI Ranking: {e}")
            # Xóa cache ngay lập tức nếu dữ liệu AI trả về bị rác
            cache.delete_memoized(call_gemini_api, prompt)
            
            for h in candidates[:limit]:
                h.match_score = 80
            return candidates[:limit]
