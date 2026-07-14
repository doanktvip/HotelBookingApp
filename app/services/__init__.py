from flask import request


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
        per_page = request.args.get('per_page', default_per_page, type=int)
        return query.paginate(page=page, per_page=per_page, error_out=False)

    def get_all_paginated(self, model_class, *filters, per_page=None):
        query = self.db.query(model_class)
        if filters:
            query = query.filter(*filters)
        if per_page:
            return self.get_paginated(query, default_per_page=per_page)
        return self.get_paginated(query)

    def get_by_id(self, model_class, record_id):
        return self.db.get(model_class, record_id)


from .room_type_service import RoomTypeService
from .user_service import UserService
from .hotel_service import HotelService

__all__ = ['BaseService', 'RoomTypeService', 'UserService', 'HotelService']
