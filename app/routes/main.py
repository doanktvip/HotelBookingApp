from flask import Blueprint, render_template
from flask_login import current_user

from app.routes.search import search_service
from app.services import RoomTypeService, HotelService
from app.extensions import db
from app.models import UserRole
from app.services.search_service import SearchService

# Định nghĩa Blueprint cho các tuyến đường chính
main_bp = Blueprint('main', __name__)
search_service = SearchService()

@main_bp.route('/')
def index():
    user = current_user if current_user.is_authenticated else None

    room_type_service = RoomTypeService(db.session)
    room_type_pagination = room_type_service.get_room_types()

    hotel_service = HotelService(db.session)
    # Lấy 4 khách sạn ngẫu nhiên hoặc trang đầu tiên
    hotels_pagination = hotel_service.get_hotels(per_page=4)

    recommended_hotels = search_service.get_recommended_hotels(
        user=current_user if current_user.is_authenticated else None
    )


    return render_template(
        'index.html',
        room_type_pagination=room_type_pagination,
        hotels=hotels_pagination.items,
        recommended_hotels=search_service.get_recommended_hotels(user=user),
        UserRole=UserRole
    )
