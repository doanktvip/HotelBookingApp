import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SCHEDULER_API_ENABLED = True
    CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '*')
    if CORS_ALLOWED_ORIGINS != '*':
        # Ví dụ: ['https://domain1.com', 'https://domain2.com']
        CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS.split(',')]

    _db_user = os.environ.get('DB_USER')
    _db_password = os.environ.get('DB_PASSWORD')
    _db_host = os.environ.get('DB_HOST')
    _db_port = os.environ.get('DB_PORT')
    _db_name = os.environ.get('DB_NAME')

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"

    # Flask-Mail Config
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') == 'True'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

    # MoMo API Configs
    MOMO_PARTNER_CODE = os.environ.get('MOMO_PARTNER_CODE')
    MOMO_ACCESS_KEY = os.environ.get('MOMO_ACCESS_KEY')
    MOMO_SECRET_KEY = os.environ.get('MOMO_SECRET_KEY')
    MOMO_ENDPOINT = os.environ.get('MOMO_ENDPOINT')
    MOMO_REFUND_ENDPOINT = os.environ.get('MOMO_REFUND_ENDPOINT')

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
