from app.services import BaseService
from app.models import Hotel
from sqlalchemy.orm import selectinload


class HotelService(BaseService):
    def get_hotel_by_id(self, hotel_id):
        return self.get_by_id(Hotel, hotel_id)

    def get_hotels(
        self, name=None, address=None, location=None, description=None, min_rating=None, amenities=None, per_page=None
    ):
        filters = []

        # Dùng ilike để tìm kiếm gần đúng (không phân biệt hoa/thường)
        if name:
            filters.append(Hotel.name.ilike(f'%{name}%'))
        if address:
            filters.append(Hotel.address.ilike(f'%{address}%'))
        if location:
            filters.append(Hotel.location.ilike(f'%{location}%'))
        if description:
            filters.append(Hotel.description.ilike(f'%{description}%'))

        # Lọc điểm đánh giá lớn hơn hoặc bằng
        if min_rating is not None:
            filters.append(Hotel.rating >= min_rating)

        # Tìm các tiện nghi có chứa từ khóa (Ví dụ: 'Wifi')
        if amenities:
            filters.append(Hotel.amenities.ilike(f'%{amenities}%'))

        # Tối ưu hoá truy vấn (Eager Loading) để giải quyết lỗi N+1 Queries gây lag
        query = self.db.query(Hotel).options(
            selectinload(Hotel.tags),
            selectinload(Hotel.room_types)
        )
        if filters:
            query = query.filter(*filters)
            
        if per_page:
            return self.get_paginated(query, default_per_page=per_page)
        return self.get_paginated(query)
