from app.services import BaseService
from app.models import RoomType


class RoomTypeService(BaseService):
    def get_room_types_for_homepage(self, per_page=None):
        return self.get_all_paginated(RoomType, per_page=per_page)
