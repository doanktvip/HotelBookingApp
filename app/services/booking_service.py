from decimal import Decimal
from flask import g, session
from app.models import Room, Booking, BookingDetail, BookingStatus, RoomStatus, Payment, PaymentStatus, RefundLog
from app.services import BaseService
from datetime import datetime, timedelta
from app.utils import get_vn_time
from sqlalchemy.orm import joinedload
from app.services.momo_service import MoMoService

class BookingService(BaseService):
    def parse_and_validate_dates(self, check_in_str, check_out_str):
        today = get_vn_time().date()
        
        # Nếu không có query param, thử lấy từ session
        if not check_in_str:
            check_in_str = session.get('search_check_in')
        if not check_out_str:
            check_out_str = session.get('search_check_out')
        
        if check_in_str and check_out_str:
            try:
                check_in_date = datetime.strptime(check_in_str, '%Y-%m-%d').date()
                check_out_date = datetime.strptime(check_out_str, '%Y-%m-%d').date()
            except ValueError:
                check_in_date = today
                check_out_date = today + timedelta(days=1)
        else:
            check_in_date = today
            check_out_date = today + timedelta(days=1)
            
        # Kiểm tra logic ngày hợp lệ
        if check_in_date < today:
            check_in_date = today
            
        if check_out_date <= check_in_date:
            check_out_date = check_in_date + timedelta(days=1)
            
        # Lưu lại vào session để dùng cho lần sau
        session['search_check_in'] = check_in_date.strftime('%Y-%m-%d')
        session['search_check_out'] = check_out_date.strftime('%Y-%m-%d')
            
        return check_in_date, check_out_date

    def get_available_rooms(self, room_type_id, check_in_date, check_out_date, quantity):
        overlapping_bookings = self.db.query(BookingDetail.room_id).join(Booking).filter(
            Booking.status == BookingStatus.CONFIRMED,
            Booking.check_in < check_out_date,
            Booking.check_out > check_in_date
        ).subquery()
        
        query = self.db.query(Room).filter(
            Room.room_type_id == room_type_id,
            Room.is_active == True,
            Room.id.notin_(overlapping_bookings)
        )
        
        if check_in_date <= get_vn_time().date():
            query = query.filter(Room.status == RoomStatus.AVAILABLE)
        else:
            query = query.filter(Room.status != RoomStatus.MAINTENANCE)
            
        available_rooms = query.limit(quantity).all()
        
        return available_rooms

    def get_user_bookings(self, user_id, status=None, per_page=None):
        query = self.db.query(Booking).options(
            joinedload(Booking.hotel),
            joinedload(Booking.room_type)
        ).filter(Booking.user_id == user_id)
        if status and status != 'ALL':
            query = query.filter(Booking.status == status)
        query = query.order_by(Booking.booking_date.desc())
        if per_page:
            return self.get_paginated(query, default_per_page=per_page)
        return self.get_paginated(query)

    def prepare_booking_data(self, room_type, check_in, check_out, quantity, user_id):
        if check_out <= check_in:
            raise ValueError("Ngày trả phòng phải sau ngày nhận phòng.")
            
        if quantity <= 0 or quantity > g.max_rooms_per_booking:
            raise ValueError("Số lượng phòng không hợp lệ.")
            
        available_rooms = self.get_available_rooms(room_type.id, check_in, check_out, quantity)
        
        if len(available_rooms) < quantity:
            raise ValueError(f"Chỉ còn {len(available_rooms)} phòng trống trong khoảng thời gian này.")
            
        nights = (check_out - check_in).days
        total_price = float(room_type.base_price * quantity * nights * (Decimal(100 + g.tax_fee) / Decimal(100)))
        
        return {
            'user_id': user_id,
            'hotel_id': room_type.hotel_id,
            'hotel_name': room_type.hotel.name,
            'room_type_id': room_type.id,
            'room_type_name': room_type.name,
            'check_in': check_in.strftime('%d/%m/%Y'),
            'check_out': check_out.strftime('%d/%m/%Y'),
            'quantity': quantity,
            'price_at_booking': float(room_type.base_price),
            'total_price': total_price
        }

    def create_booking(self, user_id, hotel_id, room_type_id, check_in, check_out, quantity, price_at_booking, commit=True):
        if check_out <= check_in:
            raise ValueError("Ngày trả phòng phải sau ngày nhận phòng.")

        if quantity <= 0 or quantity > g.max_rooms_per_booking:
            raise ValueError(f"Số lượng phòng không hợp lệ.")
            
        # 1. Tìm các phòng trống
        available_rooms = self.get_available_rooms(room_type_id, check_in, check_out, quantity)
        
        if len(available_rooms) < quantity:
            raise ValueError(f"Chỉ còn {len(available_rooms)} phòng trống trong khoảng thời gian này.")
            
        # 2. Tính số đêm
        nights = (check_out - check_in).days
        if nights <= 0:
            raise ValueError("Ngày trả phòng phải sau ngày nhận phòng.")
            
        total_price = price_at_booking * quantity * nights * (Decimal(100 + g.tax_fee) / Decimal(100))
        
        # 3. Tạo Booking
        new_booking = Booking(
            user_id=user_id,
            hotel_id=hotel_id,
            room_type_id=room_type_id,
            check_in=check_in,
            check_out=check_out,
            total_price=total_price,
            status=BookingStatus.CONFIRMED
        )
        self.db.add(new_booking)
        self.db.flush() # Để lấy ID đơn đặt phòng mới
        
        # 4. Phân bổ BookingDetail
        for room in available_rooms:
            detail = BookingDetail(
                booking_id=new_booking.id,
                room_id=room.id,
                price_at_booking=price_at_booking
            )
            self.db.add(detail)
            
        if commit:
            self.commit_or_rollback()
        return new_booking

    def process_successful_payment(self, booking_data, payment_data):
        # Kiểm tra xem giao dịch này đã được xử lý chưa (chống IPN gọi nhiều lần)
        transaction_id = payment_data.get('transaction_id')
        if transaction_id:
            existing_payment = self.db.query(Payment).filter_by(transaction_id=transaction_id).first()
            if existing_payment:
                return existing_payment.booking
                
        # Kiểm tra số tiền thanh toán có khớp không
        expected_amount = Decimal(str(booking_data['total_price']))
        actual_amount = Decimal(str(payment_data.get('amount', 0)))
        if actual_amount < expected_amount:
            raise ValueError(f"Số tiền thanh toán không đủ. Yêu cầu: {expected_amount}, Thực nhận: {actual_amount}")

        check_in = datetime.strptime(booking_data['check_in'], '%d/%m/%Y').date()
        check_out = datetime.strptime(booking_data['check_out'], '%d/%m/%Y').date()
        
        # Tạo đơn đặt phòng
        new_booking = self.create_booking(
            user_id=booking_data['user_id'],
            hotel_id=booking_data['hotel_id'],
            room_type_id=booking_data['room_type_id'],
            check_in=check_in,
            check_out=check_out,
            quantity=booking_data['quantity'],
            price_at_booking=Decimal(str(booking_data['price_at_booking'])),
            commit=False
        )
        
        # Tạo record thanh toán
        payment = Payment(
            booking_id=new_booking.id,
            amount=Decimal(str(payment_data.get('amount'))),
            transaction_id=payment_data.get('transaction_id'),
            payment_method=payment_data.get('payment_method', 'MOMO'),
            status=PaymentStatus.SUCCESS
        )
        self.db.add(payment)
        self.commit_or_rollback()
        
        return new_booking

    def process_refund(self, ipn_data, refund_reason):
        order_id = ipn_data.get('orderId')
        trans_id = ipn_data.get('transId')
        amount = ipn_data.get('amount')
        
        # 1. Gọi API Hoàn tiền của MoMo
        refund_res = MoMoService.refund_payment(
            original_order_id=order_id,
            trans_id=trans_id,
            amount=str(amount),
            description=refund_reason
        )
        
        # 2. Lưu vào DB để đối soát
        refund_log = RefundLog(
            order_id=str(order_id),
            trans_id=str(trans_id),
            amount=amount,
            reason=refund_reason
        )
        self.db.add(refund_log)
        self.commit_or_rollback()
        
        print(f"[MoMo IPN] Đã gọi Refund API cho order {order_id}. Kết quả: {refund_res}")
        return refund_res

    def cancel_user_booking(self, booking_id, user_id):
        booking = self.db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.user_id == user_id
        ).first()

        if not booking:
            raise ValueError("Không tìm thấy đơn đặt phòng.")
            
        if booking.status != BookingStatus.CONFIRMED:
            raise ValueError("Chỉ có thể hủy đơn đặt phòng đang ở trạng thái đã xác nhận.")
            
        if not booking.can_cancel:
            raise ValueError("Đã quá thời hạn hủy phòng theo chính sách của khách sạn.")

        payment = booking.payment
        if payment and payment.status == PaymentStatus.SUCCESS and payment.transaction_id:
            refund_reason = f"Khách hàng hủy đặt phòng #{booking.id}"
            
            ipn_mock_data = {
                'orderId': str(booking.id),
                'transId': payment.transaction_id,
                'amount': int(payment.amount)
            }
            
            refund_res = self.process_refund(ipn_mock_data, refund_reason)
            
            if refund_res.get('resultCode') != 0:
                message = refund_res.get('message', 'Lỗi không xác định từ cổng thanh toán')
                raise ValueError(f"Không thể hoàn tiền: {message}")

        booking.status = BookingStatus.CANCELLED
            
        self.commit_or_rollback()
        return booking
