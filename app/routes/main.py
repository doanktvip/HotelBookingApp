from flask import Blueprint, render_template
from app.services import RoomTypeService
from app.extensions import db

# Định nghĩa Blueprint cho các tuyến đường chính
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    room_type_service = RoomTypeService(db.session)

    pagination = room_type_service.get_room_types_for_homepage()

    return render_template('index.html', pagination=pagination)
