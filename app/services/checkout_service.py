from datetime import time
from app.services import BaseService
from app.models import Booking, BookingStatus, RoomStatus, Room, BookingDetail, PaymentStatus
from app.utils import get_vn_time
from flask import abort
from sqlalchemy import or_, and_

class CheckoutService(BaseService):
    def process_auto_checkout(self, hotel_id):
        today=get_vn_time().date()
        current_time = get_vn_time().time()
        checkout_time_limit = time(12, 0)
        #Đơn quá hạn
        expired_bookings = self.db.query(Booking).filter(
            Booking.hotel_id == hotel_id,
            Booking.status == BookingStatus.CONFIRMED,
           or_(
                Booking.check_out < today,
                and_(Booking.check_out == today, current_time >= checkout_time_limit)
            )
        ).all()
        updated = False
        for booking in expired_bookings:
            booking.status = BookingStatus.COMPLETED
            for detail in booking.booking_details:
                room = detail.room

                if room and room.status == RoomStatus.OCCUPIED:
                    room.status = RoomStatus.AVAILABLE

            updated = True

        if updated:
            self.commit_or_rollback()

    def update_status_at_counter(self, booking_id, hotel_id, action):
        booking = self.get_by_id(Booking, booking_id)
        if not booking:
            abort(404)

        if booking.hotel_id != hotel_id:
            abort(403)

        today = get_vn_time().date()
        if action == 'checkin':
            # 1. Chỉ booking CONFIRMED mới được check-in
            if booking.status != BookingStatus.CONFIRMED:
                raise ValueError("Chỉ đơn đặt phòng đã xác nhận mới được check-in.")

            # 2. Không cho check-in trước ngày đặt
            if today < booking.check_in:
                raise ValueError( "Chưa đến ngày nhận phòng.")

            # 3. Không cho check-in khi đã tới hoặc qua ngày checkout
            if today >= booking.check_out:
                raise ValueError("Đơn đặt phòng đã quá thời gian nhận phòng." )

            # 4. Booking phải thanh toán thành công
            if (not booking.payment or booking.payment.status != PaymentStatus.SUCCESS):
                raise ValueError("Đơn đặt phòng chưa được thanh toán thành công.")


            # 5. Validate TẤT CẢ phòng trước khi thay đổi dữ liệu
            for detail in booking.booking_details:
                room = detail.room

                if not room:
                    raise ValueError("Không tìm thấy phòng được phân bổ cho đơn.")

                if not room.is_active:
                    raise ValueError( f"Phòng {room.room_number} hiện không hoạt động.")

                if room.status == RoomStatus.MAINTENANCE:
                    raise ValueError(f"Phòng {room.room_number} đang bảo trì.")

                if room.status == RoomStatus.OCCUPIED:
                    raise ValueError( f"Phòng {room.room_number} đang có khách sử dụng." )

            # Sau khi tất cả validation đều pass
            # mới thực sự thay đổi trạng thái phòng
            for detail in booking.booking_details:
                detail.room.status = RoomStatus.OCCUPIED

            self.commit_or_rollback()

        elif action == 'checkout':
            if booking.status != BookingStatus.CONFIRMED:
                raise ValueError("Chỉ đơn đặt phòng đang hoạt động mới được checkout.")

            has_occupied_room = any(detail.room and detail.room.status == RoomStatus.OCCUPIED for detail in booking.booking_details)

            if not has_occupied_room:
                raise ValueError("Đơn đặt phòng chưa check-in nên không thể checkout.")

            booking.status = BookingStatus.COMPLETED

            for detail in booking.booking_details:
                room = detail.room

                if room and room.status == RoomStatus.OCCUPIED:
                    room.status = RoomStatus.AVAILABLE

            self.commit_or_rollback()
        else:
            raise ValueError("Hành động không hợp lệ.")
