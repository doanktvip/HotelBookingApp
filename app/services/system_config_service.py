from app.models import SystemConfig
from . import BaseService
from app.extensions import cache

class SystemConfigService(BaseService):
    def update_config(self, key, new_value):
        """
        Cập nhật cấu hình hệ thống từ giao diện Admin.
        """
        config = self.db.query(SystemConfig).filter_by(config_key=key).first()
        if config:
            # Cập nhật giá trị mới (luôn chuyển về chuỗi để lưu vào DB)
            config.config_value = str(new_value)
            self.commit_or_rollback()
            
            # Xóa cache cũ bằng thư viện Flask-Caching
            cache.delete_memoized(SystemConfig.get_all_raw_configs)
            
            return True
        return False
