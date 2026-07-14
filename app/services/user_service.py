from app.models import User
from app.services import BaseService


class UserService(BaseService):

    def get_user_by_id(self, user_id):
        return self.get_by_id(User, user_id)
