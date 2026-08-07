from app.models import SearchHistory
from app.services import BaseService
from app.services.ai_service import AIService, SearchQuerySchema
from app.services.hotel_service import HotelService

class SearchService(BaseService):
    
    def semantic_search(self, keyword, user=None, per_page=8):
        ai_service = AIService(self.db)
        hotel_service = HotelService(self.db)
        
        parsed_filters = ai_service.parse_search_query(keyword)
        
        if parsed_filters is None:
            raise Exception("Hệ thống AI đang gặp sự cố. Vui lòng thử lại sau.")
            
        has_useful_data = SearchQuerySchema(**parsed_filters).has_useful_data()
        
        self.save_search_history(keyword, parsed_filters, has_useful_data, user.id if user else None)
        
        if has_useful_data:
            return hotel_service.get_hotels(
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
        
        return None

    def save_search_history(self, keyword, parsed_data, is_useful, user_id=None):
        # Kiểm tra xem lịch sử tìm kiếm này đã tồn tại chưa để tránh lưu trùng lặp
        existing_history = self.db.query(SearchHistory).filter(
            SearchHistory.search_query.ilike(keyword)
        ).first()
        
        if existing_history:
            return  # Nếu có rồi thì bỏ qua, không tạo thêm dòng mới
            
        history = SearchHistory(
            user_id=user_id,
            search_query=keyword,
            parsed_data=parsed_data,
            is_useful=is_useful
        )
        self.db.add(history)
        self.commit_or_rollback()


