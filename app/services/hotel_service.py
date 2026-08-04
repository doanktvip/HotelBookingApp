from app.services import BaseService
from app.models import RoomType, Room, Booking, BookingDetail, BookingStatus, Tag, Hotel
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from datetime import datetime

class HotelService(BaseService):
    def get_hotel_by_id(self, hotel_id):
        return self.get_by_id(Hotel, hotel_id)

    def get_hotels(
        self, location=None, name=None, min_rating=None, per_page=None, capacity=None, bed_count=None,
        min_price=None, max_price=None, check_in=None, check_out=None, tag_ids=None, sort_by=None
    ):  
        query = self.db.query(Hotel).options(
            selectinload(Hotel.tags),
            selectinload(Hotel.room_types)
        )
        
        if location:
            query = query.filter(or_(
                Hotel.location.ilike(f'%{location}%'),
                Hotel.address.ilike(f'%{location}%')
            ))
            
        if name:
            query = query.filter(Hotel.name.ilike(f'%{name}%'))
            
        if min_rating is not None:
            query = query.filter(Hotel.rating >= min_rating)
            
        if tag_ids:
            for tag_id in tag_ids:
                query = query.filter(Hotel.tags.any(Tag.id == tag_id))

        room_type_query = self.db.query(RoomType).filter(
            RoomType.hotel_id == Hotel.id, 
            RoomType.is_active == True
        )
        
        need_room_filter = False
        
        if min_price is not None:
            room_type_query = room_type_query.filter(RoomType.base_price >= min_price)
            need_room_filter = True
            
        if max_price is not None:
            room_type_query = room_type_query.filter(RoomType.base_price <= max_price)
            need_room_filter = True
            
        if capacity is not None:
            room_type_query = room_type_query.filter(RoomType.max_occupancy >= capacity)
            need_room_filter = True
            
        if bed_count is not None:
            room_type_query = room_type_query.filter(RoomType.bed_count >= bed_count)
            need_room_filter = True
            
        if check_in and check_out:
            try:
                ci = datetime.strptime(check_in, '%Y-%m-%d').date()
                co = datetime.strptime(check_out, '%Y-%m-%d').date()
                if co > ci:
                    overlapping_room_ids = (
                        self.db.query(BookingDetail.room_id)
                        .join(Booking, Booking.id == BookingDetail.booking_id)
                        .filter(
                            Booking.status.in_([BookingStatus.CONFIRMED]),
                            Booking.check_in < co,
                            Booking.check_out > ci,
                        )
                    )
                    room_available = self.db.query(Room).filter(
                        Room.room_type_id == RoomType.id,
                        Room.is_active == True,
                        Room.id.notin_(overlapping_room_ids),
                    ).exists()
                    room_type_query = room_type_query.filter(room_available)
                    need_room_filter = True
            except ValueError:
                pass
        
        if need_room_filter:
            query = query.filter(room_type_query.exists())

        if sort_by == 'rating_desc':
            query = query.order_by(Hotel.rating.desc())
        else:
            min_price_subq = room_type_query.with_entities(func.min(RoomType.base_price)).correlate(Hotel).scalar_subquery()

            if sort_by == 'price_asc':
                query = query.order_by(min_price_subq.is_(None), min_price_subq.asc())
            else:
                query = query.order_by(min_price_subq.is_(None), min_price_subq.desc())

        if per_page:
            return self.get_paginated(query, default_per_page=per_page)
        return self.get_paginated(query)
