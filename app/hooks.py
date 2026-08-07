from flask import g, request, render_template, abort
from werkzeug.exceptions import HTTPException
from app import utils
from app.models import SystemConfig, UserRole
from flask_login import current_user

def load_global_variables():
    g.max_rooms_per_booking = SystemConfig.get_value('MAX_ROOMS_PER_BOOKING', 5,type_func=int)
    g.cancelation_fee = SystemConfig.get_value('CANCELLATION_FEE_PERCENTAGE', 10,type_func=int)
    g.maintenance_mode = SystemConfig.get_value('MAINTENANCE_MODE', False,type_func=bool)
    g.min_len = SystemConfig.get_value('MINIMUM_PASSWORD_LENGTH', 6,type_func=int)
    g.max_len = SystemConfig.get_value('MAXIMUM_PASSWORD_LENGHT', 20,type_func=int)
    g.default_per_page = SystemConfig.get_value('DEFAULT_PER_PAGE', 12,type_func=int)
    g.check_in_time = SystemConfig.get_value('CHECK_IN_TIME', '14:00',type_func=utils.parse_time)
    g.check_out_time = SystemConfig.get_value('CHECK_OUT_TIME', '12:00',type_func=utils.parse_time)
    g.hotline_number = SystemConfig.get_value('HOTLINE_NUMBER', '19001508',type_func=str)
    g.otp_expiration_minutes = SystemConfig.get_value('OTP_EXPIRATION_MINUTES', 5, type_func=int)
    g.tax_fee = SystemConfig.get_value('TAX_FEE_PERCENTAGE', 0, type_func=int)
    g.ai_prediction_interval = SystemConfig.get_value('AI_PREDICTION_INTERVAL', 7, type_func=int)
    g.max_price_adjustment_percentage = SystemConfig.get_value('MAX_PRICE_ADJUSTMENT_PERCENTAGE', 20, type_func=int)

def check_maintenance_mode():
    """Kiểm tra và chặn truy cập nếu hệ thống đang bảo trì"""
    if getattr(g, 'maintenance_mode', False):
        allowed_paths = ('/static', '/admin', '/login')
        
        if request.path.startswith(allowed_paths):
            return None
            
        if current_user.is_authenticated and current_user.role == UserRole.ADMIN:
            return None
            
        abort(503)

def register_error_handlers(app):
    ERROR_MESSAGES = {
        400: "Yêu cầu sai cú pháp hoặc bị lỗi.",
        401: "Chưa đăng nhập hoặc sai thông tin xác thực.",
        403: "Không có quyền truy cập vào tài nguyên này.",
        404: "Trang web không tồn tại hoặc đã bị xóa.",
        405: "Phương thức gửi dữ liệu không được hỗ trợ.",
        408: "Thời gian gửi yêu cầu từ client quá lâu.",
        429: "Gửi quá nhiều yêu cầu trong thời gian ngắn.",
        500: "Lỗi chung chung của hệ thống máy chủ.",
        501: "Server không hỗ trợ tính năng được yêu cầu.",
        502: "Bad Gateway: Server trung gian nhận phản hồi lỗi từ server gốc.",
        503: "Server quá tải hoặc đang bảo trì.",
        504: "Gateway Timeout: Server trung gian không nhận được phản hồi kịp lúc."
    }

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        code = e.code if isinstance(e, HTTPException) else 500
        message = ERROR_MESSAGES.get(code, "Đã xảy ra lỗi không xác định.")
        return render_template("error.html", error_code=code, error_message=message), code

    @app.errorhandler(Exception)
    def handle_general_exception(e):
        return render_template("error.html", error_code=500, error_message=ERROR_MESSAGES.get(500)), 500

def register_hooks(app):
    app.before_request(load_global_variables)
    app.before_request(check_maintenance_mode)
    # register_error_handlers(app)
