from flask import Blueprint, render_template
from app.services import RoomTypeService, HotelService
from app.extensions import db
from app.models import UserRole

# Định nghĩa Blueprint cho các tuyến đường chính
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():

    hotel_service = HotelService(db.session)
    hotels_pagination = hotel_service.get_hotels(per_page=4)

    return render_template('index.html', hotels_pagination=hotels_pagination, UserRole=UserRole)
