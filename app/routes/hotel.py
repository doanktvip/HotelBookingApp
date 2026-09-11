from flask import Blueprint, redirect, render_template, request, jsonify, url_for, flash, session
from app.services import HotelService, BookingService, SearchService, PricePrediction
from app.extensions import db
from app.utils import get_vn_time
from datetime import timedelta
from urllib.parse import urlparse
from flask_login import current_user

from app.models import Hotel

hotel_bp = Blueprint('hotel', __name__)

@hotel_bp.route('/rooms')
@hotel_bp.route('/search')
def rooms_search():
    hotel_id = request.args.get('hotel_id', type=int)
    if not hotel_id:
        hotel = db.session.query(Hotel).first()
        hotel_id = hotel.id if hotel else 1
    return hotel_detail(hotel_id)

@hotel_bp.route('/hotels')
def hotel():
    hotel_service = HotelService(db.session)
    search_service = SearchService(db.session)
    
    keyword = request.args.get('keyword', '').strip()
    location = request.args.get('location', '').strip()
    check_in = request.args.get('check_in', '').strip()
    check_out = request.args.get('check_out', '').strip()
    guest_count = request.args.get('guest_count', type=int) or request.args.get('capacity', type=int) or 1
    room_count = request.args.get('room_count', type=int) or 1
    page = request.args.get('page', 1, type=int)
    
    # Tự động ghi nhận lịch sử tìm kiếm
    if page == 1 and (keyword or location or check_in or check_out):
        import uuid
        if not current_user.is_authenticated and 'guest_id' not in session:
            session['guest_id'] = str(uuid.uuid4())
        session_id = session.get('guest_id') if not current_user.is_authenticated else None
        
        search_service.record_search(
            keyword=keyword,
            location=location,
            check_in_str=check_in,
            check_out_str=check_out,
            guest_count=guest_count,
            room_count=room_count,
            user=current_user,
            session_id=session_id,
            ip_address=request.remote_addr
        )

    async_keyword = None
    
    if keyword:
        async_keyword = keyword
        hotels_pagination = None

    else:
        hotels_pagination = hotel_service.get_hotels(
            location=location,
            check_in=check_in,
            check_out=check_out,
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
    hotel_service = HotelService(db.session)
    
    try:
        hotels_pagination = search_service.semantic_search(
            keyword, 
            user=current_user if current_user.is_authenticated else None,
            per_page=8
        )
        
        if hotels_pagination is None:
            flash("AI không thể nhận diện được yêu cầu tìm kiếm của bạn.", "warning")
            
    except Exception as e:
        flash(str(e), "danger")
        hotels_pagination = hotel_service.get_hotels(per_page=8)
    
    return render_template('partials/hotel_list.html', hotels_pagination=hotels_pagination)

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
    dynamic_prices = {}
    
    for room_type in hotel.room_types:
        available_rooms = booking_service.get_available_rooms(
            room_type.id, 
            check_in_date, 
            check_out_date, 
            quantity=999
        )
        available_counts[room_type.id] = len(available_rooms)
        
        # Gọi BookingService để tái sử dụng lõi tính giá AI
        days = (check_out_date - check_in_date).days
        if days > 0:
            total_price, avg_daily = booking_service.calculate_dynamic_total_price(
                hotel.id, room_type.base_price, check_in_date, check_out_date, 1
            )
            dynamic_prices[room_type.id] = float(avg_daily)
        else:
            dynamic_prices[room_type.id] = float(room_type.base_price)
        
    return render_template('hotel-detail.html', 
                           hotel=hotel,
                           check_in_date=check_in_date,
                           check_out_date=check_out_date,
                           today_str=today.strftime('%Y-%m-%d'),
                           available_counts=available_counts,
                           dynamic_prices=dynamic_prices)


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