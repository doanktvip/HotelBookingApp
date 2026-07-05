from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Khởi tạo các extensions rỗng (Application Factory Pattern)
db = SQLAlchemy()
login_manager = LoginManager()

# Cấu hình cơ bản cho login_manager
login_manager.login_view = 'auth.login'  # type: ignore
login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
login_manager.login_message_category = 'info'
