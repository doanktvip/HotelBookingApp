from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, g, jsonify
from flask_login import login_required, current_user
from app.extensions import db, socketio
from app.services import RoomTypeService, BookingService
from app.services.momo_service import MoMoService
from app.models import PaymentMethod

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/booking/room-type/<int:room_type_id>', methods=['GET', 'POST'])
@login_required
def book_room_type(room_type_id):
    room_type_service = RoomTypeService(db.session)
    room_type = room_type_service.get_room_type_by_id(room_type_id)
    
    if not room_type:
        flash('Loại phòng không tồn tại.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        check_in_str = request.form.get('check_in')
        check_out_str = request.form.get('check_out')
        quantity_str = request.form.get('quantity', 1)
        payment_method = request.form.get('payment_method', 'MOMO')
        
        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
            quantity = int(quantity_str)
            
            booking_service = BookingService(db.session)
            pending_booking = booking_service.prepare_booking_data(
                room_type, check_in, check_out, quantity, current_user.id
            )
            
            if payment_method == 'MOMO':
                response = MoMoService.create_payment_request(pending_booking)
                if response.get('resultCode') == 0:
                    return render_template('payment.html', 
                                           pay_url=response.get('payUrl'),
                                           qr_code_url=response.get('qrCodeUrl'),
                                           amount=response.get('amount'),
                                           order_id=response.get('orderId'),
                                           order_info=response.get('orderInfo'),
                                           extra_data=response.get('extraData'))
                else:
                    flash(f"Lỗi từ cổng thanh toán MoMo: {response.get('message')}", 'danger')
                    return redirect(url_for('booking.book_room_type', room_type_id=room_type.id))
            else:
                flash(f"Phương thức thanh toán {payment_method} chưa được hỗ trợ.", 'info')
                return redirect(url_for('booking.book_room_type', room_type_id=room_type.id))
            
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f"Đã xảy ra lỗi hệ thống: {str(e)}", 'danger')
            
    # Xử lý GET request (Khởi tạo form)
    booking_service = BookingService(db.session)
    check_in_date, check_out_date = booking_service.parse_and_validate_dates(
        request.args.get('check_in'), request.args.get('check_out')
    )
        
    available_rooms = booking_service.get_available_rooms(
        room_type.id, 
        check_in_date, 
        check_out_date, 
        quantity=999
    )
    
    available_count = len(available_rooms)
    max_allowed_quantity = min(g.max_rooms_per_booking, available_count)
    
    # Đảm bảo max_allowed_quantity tối thiểu là 1 để vòng lặp UI không bị lỗi (dù thực tế đã hết phòng, nút đặt phòng bên hotel-detail đã chặn)
    if max_allowed_quantity < 1:
        max_allowed_quantity = 1

    return render_template('booking.html', 
                           room_type=room_type, 
                           PaymentMethod=PaymentMethod,
                           max_allowed_quantity=max_allowed_quantity,
                           check_in_date=check_in_date,
                           check_out_date=check_out_date)


@booking_bp.route('/booking/momo-return', methods=['GET'])
def momo_return():
    result_code = request.args.get('resultCode')
    order_id = request.args.get('orderId')
    
    if result_code == '0':
        if order_id:
            flash(f'Thanh toán thành công! Đơn đặt phòng ({order_id}) của bạn đã được ghi nhận.', 'success')
        else:
            flash('Thanh toán thành công! Đơn đặt phòng của bạn đã được ghi nhận.', 'success')
    else:
        flash('Giao dịch thất bại hoặc đã bị hủy.', 'danger')
    return redirect(url_for('profile.my_bookings'))


@booking_bp.route('/booking/momo-ipn', methods=['POST'])
@booking_bp.route('/api/payment/momo-ipn', methods=['POST'])
def momo_ipn():
    ipn_data = request.json
    if not ipn_data:
        return {"message": "Invalid request"}, 400
        
    # Xác thực chữ ký
    if not MoMoService.verify_ipn_signature(ipn_data):
        return {"message": "Invalid signature"}, 401
        
    result_code = ipn_data.get('resultCode')
    if result_code == 0:
        extra_data_b64 = ipn_data.get('extraData')
        booking_data = MoMoService.decode_extra_data(extra_data_b64)
        
        if booking_data:
            booking_service = BookingService(db.session)
            try:
                payment_data = {
                    'amount': ipn_data.get('amount'),
                    'transaction_id': ipn_data.get('transId'),
                    'payment_method': 'MOMO'
                }
                booking_service.process_successful_payment(booking_data, payment_data)
                
                # Bắn tín hiệu SocketIO về trình duyệt đang hiển thị QR code
                socketio.emit('payment_success', {'order_id': ipn_data.get('orderId')}, room=ipn_data.get('orderId'))
                
                # Bắn tín hiệu Broadcast toàn hệ thống báo hiệu phòng vừa bị đặt
                if booking_data.get('hotel_id'):
                    socketio.emit('booking_updated', {'hotel_id': booking_data.get('hotel_id')})
                
            except Exception as e:
                # Gặp lỗi hết phòng do Race Condition. Tiền đã trừ. Cần Refund.
                print(f"[MoMo IPN] Lỗi tạo booking: {e}")
                db.session.rollback()
                
                # Chuyển xử lý hoàn tiền sang Service
                refund_reason = f"Lỗi tạo booking: {str(e)[:100]}"
                booking_service.process_refund(ipn_data, refund_reason)
                
                # Bắn tín hiệu SocketIO về trình duyệt báo hoàn tiền
                order_id = ipn_data.get('orderId')
                socketio.emit('payment_refunded', {'order_id': order_id, 'reason': refund_reason}, room=order_id)
                
    return '', 204 # HTTP 204 No Content là chuẩn response cho Webhook
@booking_bp.route('/api/booking/calculate-price', methods=['POST'])
def api_calculate_price():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400
        
    check_in_str = data.get('check_in')
    check_out_str = data.get('check_out')
    quantity = int(data.get('quantity', 1))
    room_type_id = int(data.get('room_type_id'))
    
    if not all([check_in_str, check_out_str, room_type_id]):
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        
        room_type_service = RoomTypeService(db.session)
        room_type = room_type_service.get_room_type_by_id(room_type_id)
        if not room_type:
            return jsonify({'error': 'Room type not found'}), 404
            
        booking_service = BookingService(db.session)
        total_price, avg_daily = booking_service.calculate_dynamic_total_price(
            room_type.hotel_id, room_type.base_price, check_in, check_out, quantity
        )
        
        return jsonify({
            'total_price': float(total_price),
            'average_daily_price': float(avg_daily),
            'base_price': float(room_type.base_price),
            'quantity': quantity,
            'days': (check_out - check_in).days
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
