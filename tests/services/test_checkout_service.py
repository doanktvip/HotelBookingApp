from datetime import date, timedelta

import pytest
from werkzeug.exceptions import Forbidden, NotFound

from app.models import BookingStatus, RoomStatus, PaymentStatus
from app.services.checkout_service import CheckoutService


@pytest.fixture
def checkout_service(test_session):
    return CheckoutService(db_session=test_session)


# Test booking CONFIRMED quá hạn được auto checkout thành COMPLETED
def test_auto_checkout_confirmed(test_app, checkout_service, sample_hotel, sample_booking, sample_booking_details):
    sample_booking.check_out = date.today() - timedelta(days=1)
    sample_booking.status = BookingStatus.CONFIRMED

    for detail in sample_booking_details:
        detail.room.status = RoomStatus.OCCUPIED

    checkout_service.commit_or_rollback()

    with test_app.test_request_context():
        checkout_service.process_auto_checkout(sample_hotel.id)

    assert sample_booking.status == BookingStatus.COMPLETED
    assert all(detail.room.status == RoomStatus.AVAILABLE for detail in sample_booking_details)


# Test booking CANCELLED quá hạn không bị đổi sai thành COMPLETED
def test_auto_checkout_cancelled(test_app, checkout_service, sample_hotel, sample_booking, sample_booking_details):
    sample_booking.check_out = date.today() - timedelta(days=1)
    sample_booking.status = BookingStatus.CANCELLED

    for detail in sample_booking_details:
        detail.room.status = RoomStatus.OCCUPIED

    checkout_service.commit_or_rollback()

    with test_app.test_request_context():
        checkout_service.process_auto_checkout(sample_hotel.id)

    assert sample_booking.status == BookingStatus.CANCELLED


# Test check-in thành công khi booking hợp lệ, đúng ngày và đã thanh toán
def test_checkin_success(test_app, checkout_service, sample_hotel, sample_booking, sample_booking_details, sample_payment):
    sample_booking.check_in = date.today()
    sample_booking.check_out = date.today() + timedelta(days=2)
    sample_booking.status = BookingStatus.CONFIRMED
    checkout_service.commit_or_rollback()

    with test_app.test_request_context():
        checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, "checkin")

    assert all(detail.room.status == RoomStatus.OCCUPIED for detail in sample_booking_details)


# Test booking đã CANCELLED không được check-in
def test_checkin_cancelled(test_app, checkout_service, sample_hotel, sample_booking, sample_payment):
    sample_booking.status = BookingStatus.CANCELLED
    sample_booking.check_in = date.today()
    sample_booking.check_out = date.today() + timedelta(days=2)
    checkout_service.commit_or_rollback()

    with test_app.test_request_context():
        with pytest.raises(ValueError):
            checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, "checkin")


# Test không được check-in trước ngày nhận phòng
def test_checkin_too_early(test_app, checkout_service, sample_hotel, sample_booking, sample_payment):
    sample_booking.check_in = date.today() + timedelta(days=1)
    sample_booking.check_out = date.today() + timedelta(days=3)
    checkout_service.commit_or_rollback()

    with test_app.test_request_context():
        with pytest.raises(ValueError):
            checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, "checkin")


# Test không được check-in khi booking đã tới hoặc quá ngày checkout
def test_checkin_expired(test_app, checkout_service, sample_hotel, sample_booking, sample_payment):
    sample_booking.check_in = date.today() - timedelta(days=2)
    sample_booking.check_out = date.today()
    checkout_service.commit_or_rollback()

    with test_app.test_request_context():
        with pytest.raises(ValueError):
            checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, "checkin")


# Test booking không có thông tin thanh toán không được check-in
def test_checkin_without_payment(test_app, checkout_service, sample_hotel, sample_booking):
    sample_booking.check_in = date.today()
    sample_booking.check_out = date.today() + timedelta(days=2)
    checkout_service.commit_or_rollback()

    with test_app.test_request_context():
        with pytest.raises(ValueError):
            checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, "checkin")

# Test payment chưa SUCCESS không được check-in
def test_checkin_payment_failed(test_app, checkout_service, sample_hotel, sample_booking, sample_payment):
    sample_booking.check_in = date.today()
    sample_booking.check_out = date.today() + timedelta(days=2)
    sample_payment.status = PaymentStatus.FAILED
    checkout_service.commit_or_rollback()

    with test_app.test_request_context():
        with pytest.raises(ValueError):
            checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, "checkin")


# Test không cho check-in khi phòng đang bảo trì
def test_checkin_maintenance_room(
    test_app, checkout_service, sample_hotel, sample_booking, sample_booking_details, sample_payment
):
    sample_booking.check_in = date.today()
    sample_booking.check_out = date.today() + timedelta(days=2)
    sample_booking_details[0].room.status = RoomStatus.MAINTENANCE
    checkout_service.commit_or_rollback()

    with test_app.test_request_context():
        with pytest.raises(ValueError):
            checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, "checkin")


# Test không cho check-in khi phòng đang có khách sử dụng
def test_checkin_occupied_room(
    test_app, checkout_service, sample_hotel, sample_booking, sample_booking_details, sample_payment
):
    sample_booking.check_in = date.today()
    sample_booking.check_out = date.today() + timedelta(days=2)
    sample_booking_details[0].room.status = RoomStatus.OCCUPIED
    checkout_service.commit_or_rollback()

    with test_app.test_request_context():
        with pytest.raises(ValueError):
            checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, "checkin")


# Test checkout thành công khi booking đã check-in
def test_checkout_success(test_app, checkout_service, sample_hotel, sample_booking, sample_booking_details):
    sample_booking.status = BookingStatus.CONFIRMED

    for detail in sample_booking_details:
        detail.room.status = RoomStatus.OCCUPIED

    checkout_service.commit_or_rollback()

    with test_app.test_request_context():
        checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, "checkout")

    assert sample_booking.status == BookingStatus.COMPLETED
    assert all(detail.room.status == RoomStatus.AVAILABLE for detail in sample_booking_details)


# Test booking chưa check-in thì không được checkout
def test_checkout_not_checked_in(test_app, checkout_service, sample_hotel, sample_booking):
    with test_app.test_request_context():
        with pytest.raises(ValueError):
            checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, "checkout")


# Test booking đã CANCELLED không được checkout
def test_checkout_cancelled(test_app, checkout_service, sample_hotel, sample_booking, sample_booking_details):
    sample_booking.status = BookingStatus.CANCELLED

    checkout_service.commit_or_rollback()

    with test_app.test_request_context():
        with pytest.raises(ValueError):
            checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, "checkout")


# Test lễ tân khách sạn khác không được thao tác booking
def test_forbidden(test_app, checkout_service, sample_booking):
    with test_app.test_request_context():
        with pytest.raises(Forbidden):
            checkout_service.update_status_at_counter(sample_booking.id, 999, "checkin")


# Test booking không tồn tại phải trả về lỗi 404
def test_not_found(test_app, checkout_service, sample_hotel):
    with test_app.test_request_context():
        with pytest.raises(NotFound):
            checkout_service.update_status_at_counter(9999, sample_hotel.id, "checkin")


# Test action không phải checkin/checkout phải bị từ chối
def test_invalid_action(test_app, checkout_service, sample_hotel, sample_booking):
    with test_app.test_request_context():
        with pytest.raises(ValueError):
            checkout_service.update_status_at_counter(sample_booking.id, sample_hotel.id, "invalid")