from datetime import time
from app.services import BaseService
from app.models import Booking, BookingStatus, RoomStatus, Room, BookingDetail
from app.utils import get_vn_time
from flask import abort
from sqlalchemy import or_, and_

class CheckoutService(BaseService):
    def process_auto_checkout(self, hotel_id):
        today=get_vn_time().date()
        current_time = get_vn_time().time()
        checkout_time_limit = time(12, 0)
        #Đơn quá hạn
        expired_bookings = self.db.query(Booking).filter(Booking.hotel_id == hotel_id,
           or_(
                Booking.check_out < today,
                and_(Booking.check_out == today, current_time >= checkout_time_limit)
            )
        ).all()
        updated = False
        for booking in expired_bookings:
            has_occupied_room = any(
                detail.room and detail.room.status.name == 'OCCUPIED'
                for detail in booking.booking_details
            )

            if has_occupied_room or booking.status.name != 'COMPLETED':
                booking.status = BookingStatus.COMPLETED
                for detail in booking.booking_details:
                    room = detail.room
                    if room and room.status.name == 'OCCUPIED':
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

        if action == 'checkin':
            for detail in booking.booking_details:
                room = detail.room
                if room:
                    room.status = RoomStatus.OCCUPIED
            self.commit_or_rollback()

        elif action == 'checkout':
            booking.status = BookingStatus.COMPLETED
            for detail in booking.booking_details:
                room = detail.room
                if room:
                    room.status = RoomStatus.AVAILABLE
            self.commit_or_rollback()