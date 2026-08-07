from .main import main_bp
from .hotel import hotel_bp
from .auth import auth_bp
from .profile import profile_bp
from .booking import booking_bp
from .admin import admin_bp

all_blueprints = [main_bp, hotel_bp, auth_bp, profile_bp, booking_bp, admin_bp]
