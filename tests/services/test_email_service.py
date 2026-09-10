import pytest
from unittest.mock import patch
from app.services.email_service import EmailService

@patch('app.services.email_service.mail.send')
@patch('app.services.email_service.render_template')
def test_send_verification_email_success(mock_render_template, mock_mail_send, test_app):
    mock_render_template.return_value = "<html>Mã OTP của bạn là 123456</html>"
    
    with test_app.test_request_context():
        # Gọi hàm cần test
        result = EmailService.send_verification_email("test@gmail.com", "123456")
        
        # Kiểm tra kết quả phải là True
        assert result is True
        
        # Đảm bảo hàm render_template được gọi với đúng tên file và biến otp_code
        mock_render_template.assert_called_once_with('email/verify_email.html', otp_code="123456")
        
        # Đảm bảo hàm mail.send đã được kích hoạt
        mock_mail_send.assert_called_once()
        
        # Lấy đối tượng Message được truyền vào hàm mail.send
        msg = mock_mail_send.call_args[0][0]
        assert msg.subject == 'Mã xác thực tài khoản StayNow'
        assert msg.recipients == ["test@gmail.com"]
        assert msg.html == "<html>Mã OTP của bạn là 123456</html>"

@patch('app.services.email_service.mail.send')
@patch('app.services.email_service.render_template')
def test_send_verification_email_fail(mock_render_template, mock_mail_send, test_app):
    mock_render_template.return_value = "<html>Mã OTP của bạn là 123456</html>"
    mock_mail_send.side_effect = Exception("SMTP Connection Error")
    
    with test_app.test_request_context():
        # Gọi hàm
        result = EmailService.send_verification_email("test@gmail.com", "123456")
        
        # Hàm phải bắt được Exception (try...except) và trả về False một cách an toàn, không được crash hệ thống
        assert result is False
