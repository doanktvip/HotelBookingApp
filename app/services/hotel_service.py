from app.services import BaseService
from app.models import Hotel


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

        # Truyền danh sách điều kiện (*filters) vào hàm cha siêu tái sử dụng
        return self.get_all_paginated(Hotel, *filters, per_page=per_page)
