import os
from flask import Flask
from config import config_by_name
from app.extensions import db, login_manager


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

    # Đăng ký Blueprints tự động
    from app.routes import all_blueprints

    for bp in all_blueprints:
        app.register_blueprint(bp)

    # Thiết lập user_loader cho Flask-Login
    from app.services import UserService

    @login_manager.user_loader
    def load_user(user_id):
        user_service = UserService(db_session=db.session)
        return user_service.get_user_by_id(int(user_id))

    return app
