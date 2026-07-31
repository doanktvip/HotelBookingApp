from flask import g, request
from app.models import SystemConfig, UserRole
from flask_login import current_user

def load_global_variables():
    g.max_rooms_per_booking = SystemConfig.get_value('MAX_ROOMS_PER_BOOKING', 5)
    g.cancelation_fee = SystemConfig.get_value('CANCELLATION_FEE_PERCENTAGE', 10)
    g.maintenance_mode = SystemConfig.get_value('MAINTENANCE_MODE', False)
    g.min_len = SystemConfig.get_value('MINIMUM_PASSWORD_LENGTH', 6)
    g.max_len = SystemConfig.get_value('MAXIMUM_PASSWORD_LENGHT', 20)
    g.default_per_page = SystemConfig.get_value('DEFAULT_PER_PAGE', 12)

def check_maintenance_mode():
    """Kiểm tra và chặn truy cập nếu hệ thống đang bảo trì"""
    if getattr(g, 'maintenance_mode', False):
        allowed_paths = ('/static', '/admin', '/login')
        
        if request.path.startswith(allowed_paths):
            return None
            
        if current_user.is_authenticated and current_user.role == UserRole.ADMIN:
            return None
            
        return "Hệ thống đang được nâng cấp bảo trì. Vui lòng quay lại sau ít phút!", 503

def register_hooks(app):
    app.before_request(load_global_variables)
    app.before_request(check_maintenance_mode)
