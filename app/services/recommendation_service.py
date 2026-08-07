from sqlalchemy import func, case, Float
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import exists
from app.models import Hotel, RoomType, SearchHistory, hotel_tags, Booking, BookingStatus
from app.services import BaseService
from app.services.ai_service import AIService

class RecommendationService(BaseService):
    
    def _get_recent_searches(self, user_id=None, limit=50):
        query = SearchHistory.query.filter(SearchHistory.is_useful == True)
        if user_id:
            query = query.filter(SearchHistory.user_id == user_id)
        return query.order_by(SearchHistory.searched_at.desc()).limit(limit).all()

    def _get_recent_bookings(self, user_id, limit=5):
        bookings = self.db.query(Booking).options(
            joinedload(Booking.hotel).selectinload(Hotel.tags),
            joinedload(Booking.room_type)
        ).filter(
            Booking.user_id == user_id,
            Booking.status == BookingStatus.COMPLETED
        ).order_by(Booking.check_in.desc()).limit(limit).all()
        return bookings

    def _get_valid_searches(self, user=None):
        if user:
            valid_recent_searches = self._get_recent_searches(user_id=user.id, limit=20)
            
            if not valid_recent_searches:
                valid_recent_searches = self._get_recent_searches(limit=50)
        else:
            valid_recent_searches = self._get_recent_searches(limit=50)
            
        return valid_recent_searches

    def get_sql_candidates(self, valid_recent_searches, recent_bookings, limit=20):
        has_active_room = exists().where(RoomType.hotel_id == Hotel.id).where(RoomType.is_active == True)
        query = self.db.query(Hotel).options(
            selectinload(Hotel.tags),
            selectinload(Hotel.room_types)
        ).filter(has_active_room)
        
        score_expr = func.coalesce(Hotel.rating, 0.0)
        
        preferred_locations = []
        preferred_tag_ids = []
        
        for search in valid_recent_searches:
            data = search.parsed_data
            
            loc = data.get('location')
            if loc:
                preferred_locations.append(loc.lower())
                
            tags = data.get('tag_ids')
            if isinstance(tags, list):
                preferred_tag_ids.extend(tags)

        # Trích xuất sở thích từ Lịch sử đặt phòng (Booking History)
        for booking in recent_bookings:
            hotel = booking.hotel
            if hotel:
                if hotel.location:
                    preferred_locations.append(hotel.location.lower())
                for t in hotel.tags:
                    preferred_tag_ids.append(t.id)

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
        
        candidates = self.get_limit(query, limit=limit)
        return candidates

    def get_recommended_hotels(self, user=None, limit=4):
        valid_recent_searches = self._get_valid_searches(user)
        recent_bookings = self._get_recent_bookings(user.id) if user else []
        
        candidates = self.get_sql_candidates(valid_recent_searches, recent_bookings, limit=20)
        
        ai_service = AIService(self.db)
        final_hotels = ai_service.get_ai_recommendations(user, candidates, valid_recent_searches, recent_bookings, limit)
        
        return final_hotels
