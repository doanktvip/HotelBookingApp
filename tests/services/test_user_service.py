import pytest
import hashlib
from unittest.mock import patch
from flask import g
from app.services.user_service import UserService

@pytest.fixture
def user_service(test_session):
    return UserService(db_session=test_session)

def test_get_user_by_id_and_filter(user_service, sample_customer):
    """Test lấy user theo id và filter"""
    user1 = user_service.get_user_by_id(sample_customer.id)
    assert user1 is not None
    assert user1.username == sample_customer.username

    user2 = user_service.get_first_user_by(email=sample_customer.email)
    assert user2 is not None
    assert user2.id == sample_customer.id

def test_auth_user_success(user_service, sample_customer):
    """Test đăng nhập thành công"""
    # sample_customer có password là 123456 nhưng trong fixture_db nó dùng generate_password_hash.
    # Trong khi đó UserService lại dùng hashlib.md5. 
    # Do đó, để test auth_user của UserService, ta sẽ tạo một user mới băm bằng MD5.
    
    password_123456_md5 = str(hashlib.md5("123456".strip().encode('utf-8')).hexdigest())
    sample_customer.password = password_123456_md5
    user_service.commit_or_rollback()

    user = user_service.auth_user(sample_customer.username, "123456")
    assert user is not None
    assert user.id == sample_customer.id

def test_auth_user_fail(user_service, sample_customer):
    """Test đăng nhập thất bại do sai mật khẩu"""
    password_123456_md5 = str(hashlib.md5("123456".strip().encode('utf-8')).hexdigest())
    sample_customer.password = password_123456_md5
    user_service.commit_or_rollback()

    with pytest.raises(ValueError, match="Tên đăng nhập hoặc mật khẩu không chính xác"):
        user_service.auth_user(sample_customer.username, "wrong_password")

def test_add_user_success(test_app, user_service):
    """Test thêm người dùng thành công"""
    with test_app.test_request_context():
        g.min_len = 6
        g.max_len = 20

        new_user = user_service.add_user(
            username="newuser123",
            email="newuser@gmail.com",
            password="password123",
            confirm_password="password123"
        )
        assert new_user.id is not None
        assert new_user.username == "newuser123"
        # Mật khẩu phải được băm MD5
        assert new_user.password == str(hashlib.md5("password123".encode('utf-8')).hexdigest())

def test_add_user_validation_fail(test_app, user_service):
    """Test thêm người dùng thất bại do validation"""
    with test_app.test_request_context():
        g.min_len = 6
        g.max_len = 20

        # Mật khẩu không khớp
        with pytest.raises(ValueError, match="Mật khẩu xác nhận không khớp."):
            user_service.add_user("testuser", "test@test.com", "pass123", "pass456")

        # Tên đăng nhập quá ngắn
        with pytest.raises(ValueError, match="Tên đăng nhập phải từ 6 đến 20 ký tự."):
            user_service.add_user("abc", "test@test.com", "pass123", "pass123")

        # Email sai định dạng
        with pytest.raises(ValueError, match="Định dạng email không hợp lệ"):
            user_service.add_user("testuser", "email-sai", "pass123", "pass123")

def test_update_phone_and_email_success(user_service, sample_customer):
    """Test cập nhật sđt và email thành công"""
    updated = user_service.update_phone_and_email(sample_customer, "0123456789", "new_email@gmail.com")
    
    assert updated is True
    assert sample_customer.phone == "0123456789"
    assert sample_customer.email == "new_email@gmail.com"
    assert sample_customer.is_verified is False # Cập nhật email sẽ đưa is_verified về False

def test_update_phone_and_email_duplicate_email(user_service, sample_customer, sample_admin):
    """Test lỗi khi email đã có người khác dùng"""
    with pytest.raises(ValueError, match="Email này đã được sử dụng bởi tài khoản khác!"):
        user_service.update_phone_and_email(sample_customer, None, sample_admin.email)

def test_change_password_success(test_app, user_service, sample_customer):
    """Test đổi mật khẩu thành công"""
    with test_app.test_request_context():
        g.min_len = 6
        g.max_len = 20
        
        # Đặt lại mật khẩu cũ về MD5
        password_123456_md5 = str(hashlib.md5("123456".strip().encode('utf-8')).hexdigest())
        sample_customer.password = password_123456_md5
        user_service.commit_or_rollback()

        result = user_service.change_password(sample_customer, "123456", "newpass123", "newpass123")
        assert result is True
        
        newpass_md5 = str(hashlib.md5("newpass123".encode('utf-8')).hexdigest())
        assert sample_customer.password == newpass_md5

@patch("app.services.user_service.cloudinary.uploader.upload")
def test_update_avatar_with_file_success(mock_upload, user_service, sample_customer):
    """Test đổi ảnh đại diện (sử dụng mock để không gửi file thật lên Cloudinary)"""
    # Giả lập kết quả trả về từ Cloudinary
    mock_upload.return_value = {"secure_url": "https://fake_cloudinary.com/avatar.jpg"}
    
    result = user_service.update_avatar_with_file(sample_customer, "fake_file_content")
    
    assert result is True
    assert sample_customer.avatar_url == "https://fake_cloudinary.com/avatar.jpg"
    mock_upload.assert_called_once_with("fake_file_content")
