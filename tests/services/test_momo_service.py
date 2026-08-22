import pytest
from unittest.mock import patch, MagicMock
from app.services.momo_service import MoMoService

def test_encode_decode_extra_data():
    """Test chức năng đóng gói và mở gói dữ liệu bằng Base64"""
    booking_dict = {"booking_id": 123, "user_id": 456}
    encoded = MoMoService.encode_extra_data(booking_dict)
    
    # Phải là chuỗi string base64
    assert isinstance(encoded, str)
    assert encoded != ""
    
    decoded = MoMoService.decode_extra_data(encoded)
    assert decoded["booking_id"] == 123
    assert decoded["user_id"] == 456
    
    # Test ngoại lệ (dữ liệu rỗng hoặc sai chuẩn)
    assert MoMoService.decode_extra_data("") == {}
    assert MoMoService.decode_extra_data("invalid_base64_!@#") == {}

def test_generate_signature():
    """Test sinh chữ ký điện tử HMAC-SHA256"""
    secret_key = "my_secret_key"
    data = "amount=50000&orderId=123"
    sig = MoMoService.generate_signature(data, secret_key)
    
    assert isinstance(sig, str)
    assert len(sig) == 64 # Chuẩn SHA256 phải là chuỗi hexa 64 ký tự

@patch('app.services.momo_service.requests.post')
def test_create_payment_request_success(mock_post, test_app):
    """Test giả lập gửi yêu cầu thanh toán tới MoMo"""
    # 1. Giả lập MoMo trả về link thanh toán
    mock_response = MagicMock()
    mock_response.json.return_value = {"payUrl": "https://momo.vn/pay/test", "resultCode": 0}
    mock_post.return_value = mock_response
    
    booking_data = {
        "total_price": 500000,
        "quantity": 1,
        "hotel_name": "Khách sạn X",
        "room_type_name": "Standard",
        "check_in": "2026-12-01",
        "check_out": "2026-12-02",
        "booking_id": 999
    }
    
    with test_app.test_request_context():
        # Bơm cấu hình giả vào Flask App
        test_app.config['MOMO_ENDPOINT'] = "https://test.momo.vn"
        test_app.config['MOMO_PARTNER_CODE'] = "PARTNER"
        test_app.config['MOMO_ACCESS_KEY'] = "ACCESS"
        test_app.config['MOMO_SECRET_KEY'] = "SECRET"
        
        result = MoMoService.create_payment_request(booking_data)
        
        assert result["resultCode"] == 0
        assert "payUrl" in result
        assert "extraData" in result
        mock_post.assert_called_once()

def test_verify_ipn_signature(test_app):
    """Test xác thực chữ ký dữ liệu trả về từ MoMo (IPN)"""
    with test_app.app_context():
        test_app.config['MOMO_ACCESS_KEY'] = "ACCESS"
        test_app.config['MOMO_SECRET_KEY'] = "SECRET"
        
        ipn_data = {
            "amount": "50000",
            "extraData": "base64==",
            "message": "Success",
            "orderId": "O_123",
            "orderInfo": "Thanh toan",
            "orderType": "momo_wallet",
            "partnerCode": "PARTNER",
            "payType": "qr",
            "requestId": "R_123",
            "responseTime": "123456",
            "resultCode": "0",
            "transId": "T_123"
        }
        
        # 1. Tính toán chữ ký chuẩn bằng Secret Key
        raw_sig = (
            "accessKey=ACCESS&amount=50000&extraData=base64==&message=Success&orderId=O_123"
            "&orderInfo=Thanh toan&orderType=momo_wallet&partnerCode=PARTNER&payType=qr"
            "&requestId=R_123&responseTime=123456&resultCode=0&transId=T_123"
        )
        real_sig = MoMoService.generate_signature(raw_sig, "SECRET")
        
        # Đưa chữ ký chuẩn vào cục IPN giả
        ipn_data["signature"] = real_sig
        
        # Hàm xác thực phải báo True
        assert MoMoService.verify_ipn_signature(ipn_data) is True
        
        # Đổi chữ ký thành chữ ký bậy bạ
        ipn_data["signature"] = "bad_hacker_signature"
        # Hàm xác thực phải từ chối ngay lập tức
        assert MoMoService.verify_ipn_signature(ipn_data) is False

def test_refund_payment_mock(test_app):
    """Test cơ chế tự động xử lý khi hoàn tiền ảo (MOCK)"""
    with test_app.app_context():
        test_app.config['MOMO_PARTNER_CODE'] = "PARTNER"
        test_app.config['MOMO_ACCESS_KEY'] = "ACCESS"
        test_app.config['MOMO_SECRET_KEY'] = "SECRET"
        
        # Code của bạn đã hỗ trợ tự động trả về success nếu mã giao dịch bắt đầu bằng MOCK_
        result = MoMoService.refund_payment("O_123", "MOCK_123", "50000")
        assert result["resultCode"] == 0
        assert result["transId"] == "MOCK_123"
