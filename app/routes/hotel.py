from flask import Blueprint, redirect, render_template, request, jsonify, session, url_for
from app.services import HotelService, BookingService
from app.extensions import db
from app.utils import get_vn_time
from urllib.parse import urlparse

hotel_bp = Blueprint('hotel', __name__)


@hotel_bp.route('/hotels')
def hotel():
    hotel_service = HotelService(db.session)
    hotels_pagination = hotel_service.get_hotels(per_page=8)
    return render_template('hotel.html', hotels_pagination=hotels_pagination)

@hotel_bp.route('/hotels/<int:hotel_id>')
def hotel_detail(hotel_id):
    hotel_service = HotelService(db.session)
    hotel = hotel_service.get_hotel_by_id(hotel_id)
    booking_service = BookingService(db.session)
    check_in_date, check_out_date = booking_service.parse_and_validate_dates(
        request.args.get('check_in'), request.args.get('check_out')
    )
    today = get_vn_time().date()
    
    available_counts = {}
    
    for room_type in hotel.room_types:
        available_rooms = booking_service.get_available_rooms(
            room_type.id, 
            check_in_date, 
            check_out_date, 
            quantity=999
        )
        available_counts[room_type.id] = len(available_rooms)
        
    return render_template('hotel-detail.html', 
                           hotel=hotel,
                           check_in_date=check_in_date,
                           check_out_date=check_out_date,
                           today_str=today.strftime('%Y-%m-%d'),
                           available_counts=available_counts)


@hotel_bp.route('/set-search-dates', methods=['POST'])
def set_search_dates():
    check_in = request.form.get('check_in')
    check_out = request.form.get('check_out')
    keyword = request.form.get('keyword')
    
    booking_service = BookingService(db.session)
    booking_service.parse_and_validate_dates(check_in, check_out)
    
    if request.referrer:
        parsed_url = urlparse(request.referrer)
        if parsed_url.path == url_for('hotel.hotel'):
            if keyword:
                return redirect(url_for('hotel.hotel', keyword=keyword))
            return redirect(url_for('hotel.hotel'))
        return redirect(request.referrer)
    return redirect(url_for('main.index'))


@hotel_bp.route('/api/hotel/<int:hotel_id>/availability')
def api_hotel_availability(hotel_id):
    hotel_service = HotelService(db.session)
    hotel = hotel_service.get_hotel_by_id(hotel_id)
    if not hotel:
        return jsonify({"error": "Hotel not found"}), 404
        
    booking_service = BookingService(db.session)
    check_in_date, check_out_date = booking_service.parse_and_validate_dates(
        request.args.get('check_in'), request.args.get('check_out')
    )
    
    available_counts = {}
    for room_type in hotel.room_types:
        available_rooms = booking_service.get_available_rooms(
            room_type.id, 
            check_in_date, 
            check_out_date, 
            quantity=999
        )
        available_counts[room_type.id] = {
            "available_count": len(available_rooms),
            "max_rooms": len(room_type.rooms)
        }
        
    return jsonify(available_counts)