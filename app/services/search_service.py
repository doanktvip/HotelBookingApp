from sqlalchemy import func, exists,Float,case,or_
from app.models import Hotel, RoomType, SearchHistory, hotel_tags,Booking, User
from app.models import SearchHistory
from app.services import BaseService
from app.services.ai_service import AIService, SearchQuerySchema
from app.services.hotel_service import HotelService
from app.extensions import db
from datetime import datetime
from app.utils import get_vn_time

class SearchService(BaseService):
    
    def semantic_search(self, keyword, user=None, per_page=8):
        hotel_service = HotelService(self.db)
        
        # 1. Kiểm tra xem truy vấn này đã được AI phân tích trước đó chưa (Cache Database)
        existing_history = self.db.query(SearchHistory).filter(
            SearchHistory.search_query.ilike(keyword)
        ).order_by(SearchHistory.id.desc()).first()

        if existing_history and existing_history.parsed_data is not None:
            parsed_filters = existing_history.parsed_data
        else:
            # 2. Nếu chưa có thì mới gọi Gemini API
            ai_service = AIService(self.db)
            parsed_filters = ai_service.parse_search_query(keyword)
            
            if parsed_filters is None:
                raise Exception("Hệ thống AI đang gặp sự cố. Vui lòng thử lại sau.")
                
            has_useful_data = SearchQuerySchema(**parsed_filters).has_useful_data()
            self.save_search_history(keyword, parsed_filters, has_useful_data, user.id if user else None)
            
        has_useful_data = SearchQuerySchema(**parsed_filters).has_useful_data()
        
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

    def save_search_history(self, keyword, parsed_data, is_useful, user_id=None, session_id=None, ip_address=None):
        # Kiểm tra xem lịch sử tìm kiếm này đã tồn tại chưa để tránh lưu trùng lặp
        existing_history = self.db.query(SearchHistory).filter(
            SearchHistory.search_query.ilike(keyword)
        ).order_by(SearchHistory.id.desc()).first()
        
        if existing_history:
            # Nếu có rồi nhưng chưa có parsed_data thì cập nhật lại
            if existing_history.parsed_data is None:
                existing_history.parsed_data = parsed_data
                existing_history.is_useful = is_useful
                
                location = parsed_data.get('location') if parsed_data else None
                if location and not existing_history.location:
                    existing_history.location = location
                    
                self.commit_or_rollback()
            return  # Bỏ qua không tạo thêm dòng mới

        location = parsed_data.get('location') if parsed_data else None
        ci = parsed_data.get('check_in') if parsed_data else None
        co = parsed_data.get('check_out') if parsed_data else None
        capacity = parsed_data.get('capacity') if parsed_data else 1

        history = SearchHistory(
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            keyword=keyword,
            location=location,
            check_in_date=ci,
            check_out_date=co,
            guest_count=capacity or 1,
            room_count=1,
            search_query=keyword,
            parsed_data=parsed_data,
            is_useful=is_useful
        )
        self.db.add(history)
        self.commit_or_rollback()

    def record_search(
        self, keyword=None, location=None, check_in_str=None, check_out_str=None,
        guest_count=1, room_count=1, user=None, session_id=None, ip_address=None
    ):
        keyword = (keyword or '').strip() or None
        location = (location or '').strip() or None
        if not keyword and not location and not check_in_str and not check_out_str:
            return None

        ci_date, co_date = None, None
        if check_in_str:
            try:
                ci_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            except Exception:
                pass
        if check_out_str:
            try:
                co_date = datetime.strptime(check_out_str, '%Y-%m-%d').date()
            except Exception:
                pass

        user_id = user.id if user and getattr(user, 'is_authenticated', False) else None

        # Tránh ghi nhận trùng lặp nếu người dùng refresh liên tục trong 30 giây
        from datetime import timedelta
        recent_threshold = get_vn_time() - timedelta(seconds=30)
        query = self.db.query(SearchHistory).filter(
            SearchHistory.created_at >= recent_threshold,
            SearchHistory.keyword == keyword,
            SearchHistory.location == location
        )
        if user_id:
            query = query.filter(SearchHistory.user_id == user_id)
        else:
            query = query.filter(
                (SearchHistory.session_id == session_id) | (SearchHistory.ip_address == ip_address)
            )

        if query.first():
            return None

        history = SearchHistory(
            user_id=user_id,
            session_id=session_id if not user_id else None,
            ip_address=ip_address if not user_id else None,
            keyword=keyword,
            location=location,
            check_in_date=ci_date,
            check_out_date=co_date,
            guest_count=guest_count or 1,
            room_count=room_count or 1,
            search_query=keyword or location,
            is_useful=True
        )
        self.db.add(history)
        self.commit_or_rollback()
        return history


    def search_booking_in_recept(self, hotel_id, search_keyword='', status='ALL', check_in_date='', page=1, per_page=10):
        booking_query = self.db.query(Booking).join(User, Booking.user_id == User.id).filter(Booking.hotel_id == hotel_id)
        search_keyword = (search_keyword or '').strip()
        if search_keyword:
            clean_id_str = search_keyword.upper().replace('BK-', '').replace('BK', '').strip()
            if clean_id_str.isdigit():
                # Tìm theo ID HOẶC Tên HOẶC SĐT
                booking_query = booking_query.filter(
                    or_(
                        Booking.id == int(clean_id_str),
                        User.username.ilike(f'%{search_keyword}%'),
                        User.phone.ilike(f'%{search_keyword}%')
                    )
                )
            else:
                # Chỉ tìm theo Tên HOẶC SĐT
                booking_query = booking_query.filter(
                    or_(
                        User.username.ilike(f'%{search_keyword}%'),
                        User.phone.ilike(f'%{search_keyword}%')
                    )
                )

        if status and status != 'ALL':
            from app.models import BookingStatus, RoomStatus, BookingDetail, Room
            if status in ('CHECKED_IN', 'OCCUPIED'):
                # Đang sử dụng: những đơn có phòng mang trạng thái OCCUPIED
                booking_query = booking_query.join(Booking.booking_details).join(BookingDetail.room).filter(
                    Room.status == RoomStatus.OCCUPIED
                )
            elif status == 'CONFIRMED':
                occupied_subquery = self.db.query(BookingDetail.booking_id).join(Room).filter(
                    Room.status == RoomStatus.OCCUPIED
                )
                booking_query = booking_query.filter(
                    Booking.status == BookingStatus.CONFIRMED,
                    Booking.id.notin_(occupied_subquery)
                )
            else:
                try:
                    enum_status = BookingStatus[status]
                    booking_query = booking_query.filter(Booking.status == enum_status)
                except KeyError:
                    pass

        if check_in_date:
            if check_in_date.lower() == 'today':
                date_obj = get_vn_time().date()
            else:
                date_obj = datetime.strptime(check_in_date, '%Y-%m-%d').date()
            booking_query = booking_query.filter(Booking.check_in == date_obj)

        # Sắp xếp ưu tiên cho các đơn có check-in hoặc check-out là HÔM NAY
        today = get_vn_time().date()
        is_today_priority = case(
            (or_(Booking.check_in == today, Booking.check_out == today), 0),
            else_=1
        )
        booking_query = booking_query.order_by(is_today_priority.asc(), Booking.id.asc())
        bookings_pagination = booking_query.paginate(page=page, per_page=per_page, error_out=False)

        # Tính toán trạng thái "Đang ở"
        for booking in bookings_pagination.items:
            booking.is_currently_staying = any(
                detail.room and detail.room.status.name == 'OCCUPIED'
                for detail in booking.booking_details
            )

        return bookings_pagination
