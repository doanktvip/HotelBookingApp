import pytest
from flask import g
from app.services.otp_service import OTPService

@pytest.fixture
def otp_service(test_session):
    return OTPService(db_session=test_session)

def test_create_otp_code(otp_service):
    code = otp_service.create_otp_code()
    assert len(code) == 6
    assert code.isdigit()

def test_save_otp(test_app, otp_service, sample_customer):
    with test_app.test_request_context():
        g.otp_expiration_minutes = 5
        
        otp = otp_service.save_otp(sample_customer.id, "123456")
        
        assert otp.user_id == sample_customer.id
        assert otp.otp_code == "123456"
        assert otp.is_used is False

def test_verify_otp_success(test_app, otp_service, sample_customer):
    with test_app.test_request_context():
        g.otp_expiration_minutes = 5
        otp_service.save_otp(sample_customer.id, "123456")
        
        sample_customer.is_verified = False
        
        result = otp_service.verify_otp(sample_customer, "123456")
        assert result is True
        assert sample_customer.is_verified is True

def test_verify_otp_invalid(test_app, otp_service, sample_customer):
    with test_app.test_request_context():
        g.otp_expiration_minutes = 5
        otp_service.save_otp(sample_customer.id, "123456")
        
        with pytest.raises(ValueError, match="Mã xác thực không hợp lệ hoặc đã được sử dụng."):
            otp_service.verify_otp(sample_customer, "000000")

def test_verify_otp_expired(test_app, otp_service, sample_customer):
    with test_app.test_request_context():
        g.otp_expiration_minutes = -5 
        otp_service.save_otp(sample_customer.id, "123456")
        
        with pytest.raises(ValueError, match="Mã xác thực đã hết hạn."):
            otp_service.verify_otp(sample_customer, "123456")

def test_has_active_otp(test_app, otp_service, sample_customer):
    with test_app.test_request_context():
        assert otp_service.has_active_otp(sample_customer.id) is False
        
        g.otp_expiration_minutes = 5
        otp_service.save_otp(sample_customer.id, "123456")
        
        assert otp_service.has_active_otp(sample_customer.id) is True
