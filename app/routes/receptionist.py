from flask import Blueprint, render_template, request, abort, redirect, url_for, flash
from flask_login import login_required,current_user

from app.services.search_service import SearchService
from app.services.checkout_service import CheckoutService
from app.utils import get_vn_time
from app.models import Room, Booking, BookingStatus, RoomStatus, UserRole, RoomType, BookingDetail
from app.extensions import db

receptionist_bp = Blueprint('receptionist', __name__)

@receptionist_bp.route('/recept', methods=['GET'])
@receptionist_bp.route('/reception/bookings', methods=['GET'])
@receptionist_bp.route('/admin/bookings', methods=['GET'])
@login_required
def recept():
    if current_user.role not in (UserRole.RECEPTIONIST, UserRole.ADMIN):
        abort(403)
    hotel_id = current_user.hotel_id
    if not hotel_id:
        first_hotel = Hotel.query.first()
        hotel_id = first_hotel.id if first_hotel else None
    today = get_vn_time().date()

    checkout_service = CheckoutService(db.session)
    checkout_service.process_auto_checkout(hotel_id)

    #lấy ds phòng của ks
    rooms = Room.query.join(RoomType).filter(Room.is_active == True,RoomType.hotel_id == hotel_id).order_by(Room.floor, Room.room_number).all()
    #lấy booking của ngày htai
    bookings_today = db.session.query(BookingDetail.room_id).join(Booking).filter(
        Booking.hotel_id == hotel_id,
        Booking.status == BookingStatus.CONFIRMED,
        Booking.check_in <= today,
        Booking.check_out > today
    ).all()
    booked_room_ids = [b.room_id for b in bookings_today]

    rooms_by_floor = {}
    status_counts = {'AVAILABLE': 0, 'BOOKED': 0, 'OCCUPIED': 0, 'MAINTENANCE': 0}
    floors = set()
    for room in rooms:
        actual_status = room.status.name
        if actual_status == 'AVAILABLE':
            #phòng có lịch đặt hôm nay
            if room.id in booked_room_ids:
                actual_status = 'BOOKED'
        elif actual_status == 'BOOKED':
            if room.id not in booked_room_ids:
                actual_status = 'AVAILABLE'

        room.actual_status = actual_status
        if room.floor not in rooms_by_floor:
            rooms_by_floor[room.floor] = []
        rooms_by_floor[room.floor].append(room)
        floors.add(room.floor)
        status_counts[actual_status] += 1

    floors = sorted(list(floors))
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status = request.args.get('status', 'ALL')
    check_in_date = request.args.get('check_in_date', '')
    
    search_service = SearchService(db.session)
    bookings_pagination = search_service.search_booking_in_recept(
        hotel_id=hotel_id,
        search_keyword=search,
        status=status,
        check_in_date=check_in_date,
        page=page,
        per_page=10
    )
    return render_template('room_management.html',rooms_by_floor=rooms_by_floor,status_counts=status_counts,floors=floors,bookings=bookings_pagination,today=today,BookingStatus=BookingStatus,current_status=status,current_date=check_in_date)


@receptionist_bp.route('/api/checkout-details/<int:booking_id>', methods=['GET'])
@login_required
def get_checkout_details(booking_id):
    if current_user.role not in (UserRole.RECEPTIONIST, UserRole.ADMIN):
        abort(403)
        
    booking = db.get_or_404(Booking, booking_id)
    if current_user.hotel_id and booking.hotel_id != current_user.hotel_id:
        abort(403)
        
    room_price = float(booking.total_price)
    late_fee = 0.0
    
    today = get_vn_time().date()
    current_time = get_vn_time().time()
    from datetime import time
    from app.models import PaymentStatus
    checkout_time_limit = time(12, 0)
    
    if today > booking.check_out or (today == booking.check_out and current_time > checkout_time_limit):
        late_fee = room_price * 0.1
        
    total = room_price + late_fee
    
    paid = 0.0
    if booking.payment and booking.payment.status == PaymentStatus.SUCCESS:
        paid = float(booking.payment.amount)
        
    balance = max(0.0, total - paid)
    
    from flask import jsonify
    return jsonify({
        'room_price': room_price,
        'late_fee': late_fee,
        'total': total,
        'paid': paid,
        'balance': balance
    })


@receptionist_bp.route('/update_booking_status/<int:booking_id>', methods=['POST'])
@login_required
def update_booking_status(booking_id):
    if current_user.role not in (UserRole.RECEPTIONIST, UserRole.ADMIN):
        abort(403)

    action = request.form.get('action')
    checkout_service = CheckoutService(db.session)
    try:
        hotel_id = current_user.hotel_id
        if not hotel_id:
            booking = db.session.get(Booking, booking_id)
            hotel_id = booking.hotel_id if booking else None
        checkout_service.update_status_at_counter(booking_id, hotel_id, action)
        if action == "checkin":
            flash("Check-in thành công.", "success")
        elif action == "checkout":
            flash("Checkout thành công.", "success")

    except ValueError as e:
        flash(str(e), "danger")
    return redirect( url_for('receptionist.recept',tab='list'))