from sqlalchemy import func, exists,Float,case
from app.models import Hotel, RoomType, SearchHistory, hotel_tags
from app.services import BaseService
from app.services.ai_service import AIService
from app.services.hotel_service import HotelService

class SearchService(BaseService):
    
    def semantic_search(self, keyword, user=None, per_page=8):
        ai_service = AIService(self.db)
        hotel_service = HotelService(self.db)
        
        try:
            parsed_filters = ai_service.parse_search_query(keyword)
            if parsed_filters:
                # Chỉ lưu vào Database nếu AI trích xuất được ít nhất 1 dữ liệu có ích (khác null, rỗng, list rỗng)
                has_useful_data = any(v is not None and v != "" and v != [] for v in parsed_filters.values())
                if has_useful_data:
                    ai_service.save_search_history(keyword, parsed_filters, user.id if user else None)
                
                hotels_pagination = hotel_service.get_hotels(
                    location=parsed_filters.get('location'),
                    name=parsed_filters.get('name'),
                    min_rating=parsed_filters.get('min_rating'),
                    min_price=parsed_filters.get('min_price'),
                    max_price=parsed_filters.get('max_price'),
                    capacity=parsed_filters.get('capacity'),
                    bed_count=parsed_filters.get('bed_count'),
                    check_in=parsed_filters.get('check_in'),
                    check_out=parsed_filters.get('check_out'),
                    tag_ids=parsed_filters.get('tag_ids'),
                    sort_by=parsed_filters.get('sort_by', 'rating_desc'),
                    per_page=per_page
                )
                return hotels_pagination, True, None, ''
            else:
                return hotel_service.get_hotels(per_page=per_page), False, "AI không thể nhận diện được yêu cầu của bạn. Vui lòng thử lại bằng câu khác.", 'warning'
        except Exception as e:
            print("AI Error:", e)
            return hotel_service.get_hotels(per_page=per_page), False, "Hệ thống AI đang quá tải hoặc chưa được cấu hình. Vui lòng thử lại sau.", 'danger'

    def get_recommended_hotels(self, user=None, limit=4):
        has_active_room = exists().where(RoomType.hotel_id == Hotel.id).where(RoomType.is_active == True)
        query = self.db.query(Hotel).filter(has_active_room)
        
        score_expr = func.coalesce(Hotel.rating, 0.0)
        
        if user:
            recent_searches = (
                SearchHistory.query
                .filter(SearchHistory.user_id == user.id, SearchHistory.parsed_data != None)
                .order_by(SearchHistory.searched_at.desc())
                .limit(10).all()
            )
            # Nếu khách đăng nhập chưa từng tìm kiếm gì, lấy xu hướng chung của khách vãng lai
            if not recent_searches:
                recent_searches = (
                    SearchHistory.query
                    .filter(SearchHistory.parsed_data != None)
                    .order_by(SearchHistory.searched_at.desc())
                    .limit(30).all()
                )
        else:
            recent_searches = (
                SearchHistory.query
                .filter(SearchHistory.parsed_data != None)
                .order_by(SearchHistory.searched_at.desc())
                .limit(30).all()
            )
            
        preferred_locations = []
        preferred_tag_ids = []
        
        valid_recent_searches = []
        
        for search in recent_searches:
            data = search.parsed_data
            if not isinstance(data, dict):
                continue
                
            # Loại bỏ những tìm kiếm vô nghĩa (toàn null, chuỗi rỗng, hoặc danh sách rỗng)
            has_useful_data = any(v is not None and v != "" and v != [] for v in data.values())
            if not has_useful_data:
                continue
                
            valid_recent_searches.append(search)

                
            loc = data.get('location')
            if loc:
                preferred_locations.append(loc.lower())
                
            tags = data.get('tag_ids')
            if isinstance(tags, list):
                preferred_tag_ids.extend(tags)

        if preferred_locations:
            loc_case = case(
                (func.lower(Hotel.location).in_(preferred_locations), 5.0),
                else_=0.0
            )
            score_expr = score_expr + loc_case
            
        if preferred_tag_ids:
            tag_count_subq = (
                self.db.query(func.count(hotel_tags.c.tag_id))
                .filter(hotel_tags.c.hotel_id == Hotel.id)
                .filter(hotel_tags.c.tag_id.in_(preferred_tag_ids))
                .correlate(Hotel)
                .scalar_subquery()
            )
            score_expr = score_expr + func.cast(tag_count_subq, Float)
                
        query = query.order_by(score_expr.desc(), Hotel.rating.desc())
        
        # Giai đoạn 1: Lấy 20 Candidates bằng SQL
        candidates = self.get_limit(query, limit=20)
        
        # Giai đoạn 2: Lọc tinh bằng AI (truyền vào danh sách lịch sử đã được làm sạch)
        ai_service = AIService(self.db)
        final_hotels = ai_service.get_ai_recommendations(user, candidates, valid_recent_searches, limit)
        
        return final_hotels

