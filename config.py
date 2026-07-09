import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    _db_user = os.environ.get('DB_USER')
    _db_password = os.environ.get('DB_PASSWORD')
    _db_host = os.environ.get('DB_HOST')
    _db_port = os.environ.get('DB_PORT')
    _db_name = os.environ.get('DB_NAME')

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Chỉ truyền cookie qua HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Chống XSS (JS không đọc được cookie)
    SESSION_COOKIE_SAMESITE = 'Lax'  # Chống CSRF
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Ép đăng nhập lại sau 7 ngày
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Tối đa 16MB mỗi file (chống hacker up file lớn)


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
