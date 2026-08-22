import pytest
from unittest.mock import patch
from app.services.system_config_service import SystemConfigService
from app.models import SystemConfig

@pytest.fixture
def system_config_service(test_session):
    return SystemConfigService(db_session=test_session)

@patch('app.services.system_config_service.cache.delete_memoized')
def test_update_config_success(mock_delete, system_config_service, test_session, test_app):
    """Test chức năng cập nhật cấu hình hệ thống thành công"""
    # Tạo một config mẫu trong DB
    config = SystemConfig(config_key="TEST_KEY", config_value="old_value", description="Test Config")
    test_session.add(config)
    test_session.commit()
    
    with test_app.test_request_context():
        # Thực hiện cập nhật
        result = system_config_service.update_config("TEST_KEY", 999)
        
        assert result is True
        # Phải được chuyển thành string khi lưu
        assert config.config_value == "999"
        # Đảm bảo cache đã bị xóa để hệ thống load lại
        mock_delete.assert_called_once()

@patch('app.services.system_config_service.cache.delete_memoized')
def test_update_config_fail(mock_delete, system_config_service, test_app):
    """Test cập nhật config không tồn tại"""
    with test_app.test_request_context():
        result = system_config_service.update_config("NON_EXISTENT_KEY", "new_value")
        
        assert result is False
        mock_delete.assert_not_called()
