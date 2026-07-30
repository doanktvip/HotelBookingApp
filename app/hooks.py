from flask import g
from app.models import SystemConfig

def load_global_variables():
    """Hàm chạy ngầm trước mỗi request để lấy cấu hình từ Database"""
    g.min_len = SystemConfig.get_value('MINIMUM_PASSWORD_LENGTH', 6, int)
    g.max_len = SystemConfig.get_value('MAXIMUM_PASSWORD_LENGHT', 20, int)

def register_hooks(app):
    """Đăng ký các hàm chạy ngầm (hooks) vào app"""
    app.before_request(load_global_variables)
