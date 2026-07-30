import os
from flask import Flask
from config import config_by_name
from app.extensions import db, login_manager, socketio


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
    # Danh sách tên miền (Origins) được phép vượt tường lửa CORS
    socketio.init_app(app, cors_allowed_origins=app.config['CORS_ALLOWED_ORIGINS'])

    # Đăng ký Blueprints tự động
    from app.routes import all_blueprints

    for bp in all_blueprints:
        app.register_blueprint(bp)

    # Đăng ký SocketIO events
    from app import events

    # Thiết lập user_loader cho Flask-Login
    from app.services import UserService

    @login_manager.user_loader
    def load_user(user_id):
        user_service = UserService(db_session=db.session)
        return user_service.get_user_by_id(int(user_id))

    # Đăng ký các hàm chạy ngầm (hooks)
    from app.hooks import register_hooks
    register_hooks(app)

    return app
