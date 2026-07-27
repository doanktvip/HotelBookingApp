from flask import Blueprint, render_template
from app.services import RoomTypeService, HotelService
from app.extensions import db
from app.models import UserRole

# Định nghĩa Blueprint cho các tuyến đường chính
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    room_type_service = RoomTypeService(db.session)
    room_type_pagination = room_type_service.get_room_types()

    hotel_service = HotelService(db.session)
    # Lấy 4 khách sạn ngẫu nhiên hoặc trang đầu tiên
    hotels_pagination = hotel_service.get_hotels(per_page=4)

    return render_template('index.html', room_type_pagination=room_type_pagination, hotels=hotels_pagination.items, UserRole=UserRole)
