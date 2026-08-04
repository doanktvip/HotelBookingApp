from flask import Blueprint, redirect, render_template, request, jsonify, session, url_for, flash
from app.services import HotelService, BookingService
from app.extensions import db
from app.utils import get_vn_time
from urllib.parse import urlparse

hotel_bp = Blueprint('hotel', __name__)


from flask_login import current_user
from app.services.hotel_service import HotelService
from app.services.search_service import SearchService

@hotel_bp.route('/hotels')
def hotel():
    hotel_service = HotelService(db.session)
    
    keyword = request.args.get('keyword', '').strip()
    async_keyword = None
    
    if keyword:
        # Thay vì chạy AI đồng bộ gây treo trang, ta đánh dấu biến cờ để giao diện tải trước rồi mới gọi API ngầm
        async_keyword = keyword
        hotels_pagination = None

    else:
        hotels_pagination = hotel_service.get_hotels(
            location=request.args.get('location', '').strip(),
            check_in=request.args.get('check_in', '').strip(),
            check_out=request.args.get('check_out', '').strip(),
            min_price=request.args.get('min_price', type=float),
            max_price=request.args.get('max_price', type=float),
            tag_ids=request.args.getlist('tags', type=int),
            sort_by=request.args.get('sort_by', 'rating_desc'),
            per_page=8
        )

    
    all_tags = hotel_service.get_all_tags()
    
    return render_template('hotel.html', hotels_pagination=hotels_pagination, all_tags=all_tags, async_keyword=async_keyword)

@hotel_bp.route('/api/search')
def api_search():
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify({"error": "Missing keyword"}), 400
        
    search_service = SearchService(db.session)
    hotels_pagination, success, error_msg, flash_type = search_service.semantic_search(
        keyword, 
        user=current_user if current_user.is_authenticated else None,
        per_page=8
    )
    
    # Trả về partial HTML (không render lại toàn trang)
    return render_template('partials/hotel_list.html', 
                           hotels_pagination=hotels_pagination, 
                           success=success, 
                           error_msg=error_msg, 
                           flash_type=flash_type)

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