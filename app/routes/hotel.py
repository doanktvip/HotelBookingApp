from flask import Blueprint, render_template
from app.services import HotelService, RoomTypeService
from app.extensions import db

hotel_bp = Blueprint('hotel', __name__)


@hotel_bp.route('/hotel')
def hotel():
    hotel_service = HotelService(db.session)
    hotels_pagination = hotel_service.get_hotels()
    return render_template('hotel.html', hotels_pagination=hotels_pagination)


@hotel_bp.route('/hotel/<int:hotel_id>')
def hotel_detail(hotel_id):
    hotel_service = HotelService(db.session)
    hotel = hotel_service.get_hotel_by_id(hotel_id)
    return render_template('hotel-detail.html', hotel=hotel)