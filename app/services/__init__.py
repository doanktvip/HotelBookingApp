from flask import request
from app.models import Tag

class BaseService:
    def __init__(self, db_session):
        self.db = db_session

    def commit_or_rollback(self):
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise

    def get_paginated(self, query, default_per_page=12):
        page = request.args.get('page', 1, type=int)
        return query.paginate(page=page, per_page=default_per_page, error_out=False)

    def get_limit(self, query, limit=4):
        return query.limit(limit).all()

    def get_all_paginated(self, model_class, *filters, per_page=None):
        query = self.db.query(model_class)
        if filters:
            query = query.filter(*filters)
        if per_page:
            return self.get_paginated(query, default_per_page=per_page)
        return self.get_paginated(query)

    def get_by_id(self, model_class, record_id):
        return self.db.get(model_class, record_id)

    def get_all_tags(self):
        return self.db.query(Tag).order_by(Tag.name).all()


from .room_type_service import RoomTypeService
from .user_service import UserService
from .ai_service import AIService
from .hotel_service import HotelService
from .system_config_service import SystemConfigService
from .booking_service import BookingService

__all__ = ['BaseService', 'RoomTypeService', 'UserService', 'AIService', 'HotelService', 'SystemConfigService', 'BookingService']
