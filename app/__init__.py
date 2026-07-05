import os
import time
from flask import Flask
from config import config_by_name
from app.extensions import db, login_manager

# Cấu hình múi giờ Việt Nam (GMT+7)
if os.name != 'nt':
    os.environ['TZ'] = 'Asia/Ho_Chi_Minh'
    if hasattr(time, 'tzset'):
        time.tzset()


def create_app(config_name=None):
    """Hàm khởi tạo ứng dụng Flask (Application Factory)."""
    if not config_name:
        # Lấy cấu hình từ biến môi trường FLASK_ENV, mặc định là development
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)

    # Nạp cấu hình từ config.py
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Gắn kết các extensions với ứng dụng
    db.init_app(app)
    login_manager.init_app(app)

    # Đăng ký Blueprints
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)

    # Thiết lập user_loader cho Flask-Login
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
