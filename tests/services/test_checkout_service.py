import pytest
from datetime import date, timedelta
from werkzeug.exceptions import Forbidden, NotFound
from app.services.checkout_service import CheckoutService
from app.models import BookingStatus, RoomStatus,PaymentStatus
from app.utils import get_vn_time
@pytest.fixture
def checkout_service(test_session):
    return CheckoutService(db_session=test_session)

def test_process_auto_checkout(test_app, checkout_service, sample_hotel, sample_booking, sample_booking_details):
    sample_booking.check_out = date.today() - timedelta(days=1)
    
    # Giả sử khách đang ở trong phòng (RoomStatus = OCCUPIED)
    for detail in sample_booking_details:
        detail.room.status = RoomStatus.OCCUPIED
    
    checkout_service.commit_or_rollback()
    
    with test_app.test_request_context():
        # 2. Chạy hàm tự động checkout
        checkout_service.process_auto_checkout(sample_hotel.id)
        
        # 3. Kiểm tra booking đã bị chuyển sang trạng thái COMPLETED chưa
        assert sample_booking.status == BookingStatus.COMPLETED
        # Kiểm tra xem các phòng đã được giải phóng (AVAILABLE) chưa
        for detail in sample_booking_details:
            assert detail.room.status == RoomStatus.AVAILABLE

def test_update_status_at_counter_checkin(test_app, checkout_service, sample_hotel, sample_booking, sample_booking_details, sample_payment):
    sample_booking.check_in = get_vn_time().date()
    if sample_booking.payment:
        sample_booking.payment.status = PaymentStatus.SUCCESS
    checkout_service.commit_or_rollback()
    with test_app.test_request_context():
        checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, 'checkin')
        
        for detail in sample_booking_details:
            assert detail.room.status == RoomStatus.OCCUPIED

def test_update_status_at_counter_checkout(test_app, checkout_service, sample_hotel, sample_booking, sample_booking_details):
    for detail in sample_booking_details:
        detail.room.status = RoomStatus.OCCUPIED
    checkout_service.commit_or_rollback()
    with test_app.test_request_context():
        checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, 'checkout')
        
        assert sample_booking.status == BookingStatus.COMPLETED
        for detail in sample_booking_details:
            assert detail.room.status == RoomStatus.AVAILABLE

def test_update_status_at_counter_forbidden(test_app, checkout_service, sample_booking):
    with test_app.test_request_context():
        with pytest.raises(Forbidden):
            checkout_service.update_status_at_counter(sample_booking.id, 999, 'checkin')

def test_update_status_at_counter_not_found(test_app, checkout_service, sample_hotel):
    with test_app.test_request_context():
        with pytest.raises(NotFound):
            checkout_service.update_status_at_counter(9999, sample_hotel.id, 'checkin')
