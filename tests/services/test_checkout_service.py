import pytest
from datetime import date, timedelta
from werkzeug.exceptions import Forbidden, NotFound
from app.services.checkout_service import CheckoutService
from app.models import BookingStatus, RoomStatus

@pytest.fixture
def checkout_service(test_session):
    return CheckoutService(db_session=test_session)

def test_process_auto_checkout(test_app, checkout_service, sample_hotel, sample_booking, sample_booking_details):
    """Test tính năng tự động trả phòng khi quá giờ quy định"""
    # 1. Cập nhật booking để ngày check_out lùi về hôm qua (đã quá hạn)
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

def test_update_status_at_counter_checkin(test_app, checkout_service, sample_hotel, sample_booking, sample_booking_details):
    """Test chức năng lễ tân bấm Check-in"""
    with test_app.test_request_context():
        # Lễ tân thực hiện nhận phòng
        checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, 'checkin')
        
        # Phòng phải được đổi thành trạng thái OCCUPIED
        for detail in sample_booking_details:
            assert detail.room.status == RoomStatus.OCCUPIED

def test_update_status_at_counter_checkout(test_app, checkout_service, sample_hotel, sample_booking, sample_booking_details):
    """Test chức năng lễ tân bấm Check-out"""
    with test_app.test_request_context():
        # Lễ tân thực hiện trả phòng
        checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, 'checkout')
        
        # Đơn đặt phòng phải hoàn tất
        assert sample_booking.status == BookingStatus.COMPLETED
        # Phòng phải được giải phóng
        for detail in sample_booking_details:
            assert detail.room.status == RoomStatus.AVAILABLE

def test_update_status_at_counter_forbidden(test_app, checkout_service, sample_booking):
    """Test bảo mật: Lễ tân khách sạn này không được thao tác booking của khách sạn khác"""
    with test_app.test_request_context():
        # Khách sạn ID = 999 là sai, không sở hữu booking này
        with pytest.raises(Forbidden):
            checkout_service.update_status_at_counter(sample_booking.id, 999, 'checkin')

def test_update_status_at_counter_not_found(test_app, checkout_service, sample_hotel):
    """Test xử lý lỗi khi mã booking ảo"""
    with test_app.test_request_context():
        with pytest.raises(NotFound):
            checkout_service.update_status_at_counter(9999, sample_hotel.id, 'checkin')
