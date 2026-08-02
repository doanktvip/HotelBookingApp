from app.services import BaseService
from app.models import RoomType


class RoomTypeService(BaseService):

    def get_room_type_by_id(self, room_type_id):
        return self.get_by_id(RoomType, room_type_id)

    def get_room_types(self, hotel_id=None, per_page=None):
        filters = []
        if hotel_id:
            filters.append(RoomType.hotel_id == hotel_id)
        return self.get_all_paginated(RoomType, *filters, per_page=per_page)
