from app.services import BaseService
from app.models import RoomType, Room, Booking, BookingDetail, BookingStatus, Tag, Hotel, PricePrediction
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta

class HotelService(BaseService):
    def get_hotel_by_id(self, hotel_id):
        return self.get_by_id(Hotel, hotel_id)

    def get_all_hotels(self):
        return self.db.query(Hotel).options(
            selectinload(Hotel.tags), 
            selectinload(Hotel.room_types)
        ).all()

    def get_hotels(
        self, location=None, name=None, min_rating=None, per_page=None, capacity=None, bed_count=None,
        min_price=None, max_price=None, check_in=None, check_out=None, tag_ids=None, sort_by=None
    ):  
        query = self.db.query(Hotel).options(
            selectinload(Hotel.tags),
            selectinload(Hotel.room_types)
        )
        
        # 1. Lọc cơ bản
        query = self._apply_basic_filters(query, location, name, min_rating, tag_ids)
        
        room_type_query = self.db.query(RoomType).filter(
            RoomType.hotel_id == Hotel.id, 
            RoomType.is_active == True
        )
        
        # 2. Lọc thông tin phòng
        room_type_query, need_room_filter = self._apply_room_filters(
            room_type_query, min_price, max_price, capacity, bed_count
        )
        
        # 3. Lọc tình trạng phòng trống
        ci, co, days = self._parse_dates(check_in, check_out)
        room_type_query, need_room_filter = self._apply_availability_filter(
            room_type_query, ci, co, need_room_filter
        )
        
        if need_room_filter:
            query = query.filter(room_type_query.exists())

        # 4. Sắp xếp (Có tính toán Giá AI)
        query = self._apply_sorting(query, room_type_query, sort_by, ci, co, days)

        # Phân trang
        pagination = self.get_paginated(query, default_per_page=per_page) if per_page else self.get_paginated(query)
        
        # 5. Cập nhật Giá AI lên UI
        self._decorate_display_prices(pagination, ci, co, days)
                
        return pagination

    # ================= CÁC HÀM HỖ TRỢ (PRIVATE METHODS) =================

    def _apply_basic_filters(self, query, location, name, min_rating, tag_ids):
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
        return query

    def _apply_room_filters(self, room_type_query, min_price, max_price, capacity, bed_count):
        need_filter = False
        if min_price is not None:
            room_type_query = room_type_query.filter(RoomType.base_price >= min_price)
            need_filter = True
        if max_price is not None:
            room_type_query = room_type_query.filter(RoomType.base_price <= max_price)
            need_filter = True
        if capacity is not None:
            room_type_query = room_type_query.filter(RoomType.max_occupancy >= capacity)
            need_filter = True
        if bed_count is not None:
            room_type_query = room_type_query.filter(RoomType.bed_count >= bed_count)
            need_filter = True
        return room_type_query, need_filter

    def _parse_dates(self, check_in, check_out):
        if check_in and check_out:
            try:
                ci = datetime.strptime(check_in, '%Y-%m-%d').date()
                co = datetime.strptime(check_out, '%Y-%m-%d').date()
                if co > ci:
                    return ci, co, (co - ci).days
            except ValueError:
                pass
        return None, None, 0

    def _apply_availability_filter(self, room_type_query, ci, co, need_filter):
        if ci and co:
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
            return room_type_query, True
        return room_type_query, need_filter

    def _apply_sorting(self, query, room_type_query, sort_by, ci, co, days):
        if sort_by == 'rating_desc':
            return query.order_by(Hotel.rating.desc())
            
        min_price_subq = room_type_query.with_entities(func.min(RoomType.base_price)).correlate(Hotel).scalar_subquery()
        
        if days > 0:
            avg_adj_subq = self.db.query(
                PricePrediction.hotel_id, 
                (func.sum(PricePrediction.adjustment_percentage) / days).label('avg_adj')
            ).filter(
                PricePrediction.is_applied == True,
                PricePrediction.target_date >= ci,
                PricePrediction.target_date < co
            ).group_by(PricePrediction.hotel_id).subquery()
            
            query = query.outerjoin(avg_adj_subq, Hotel.id == avg_adj_subq.c.hotel_id)
            adj_factor = 1 + func.coalesce(avg_adj_subq.c.avg_adj, 0)
            sort_price = min_price_subq * adj_factor
        else:
            sort_price = min_price_subq

        if sort_by == 'price_asc':
            return query.order_by(sort_price.is_(None), sort_price.asc())
        return query.order_by(sort_price.is_(None), sort_price.desc())

    def _decorate_display_prices(self, pagination, ci, co, days):
        if days > 0 and pagination.items:
            try:
                hotel_ids = [h.id for h in pagination.items]
                preds = self.db.query(PricePrediction).filter(
                    PricePrediction.hotel_id.in_(hotel_ids),
                    PricePrediction.is_applied == True,
                    PricePrediction.target_date >= ci,
                    PricePrediction.target_date < co
                ).all()
                
                pred_dict = {}
                for p in preds:
                    if p.hotel_id not in pred_dict:
                        pred_dict[p.hotel_id] = {}
                    pred_dict[p.hotel_id][p.target_date] = p.adjustment_percentage
                
                for hotel in pagination.items:
                    h_preds = pred_dict.get(hotel.id, {})
                    total_adj = sum([h_preds.get(ci + timedelta(days=i), 0.0) for i in range(days)])
                    avg_adj = total_adj / days
                    
                    hotel.display_min_price = float(hotel.min_price) * (1 + avg_adj)
                    hotel.display_max_price = float(hotel.max_price) * (1 + avg_adj)
            except Exception as e:
                print(f"Lỗi khi tính display_price: {e}")    
        return pagination
