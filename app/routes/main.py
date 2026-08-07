from flask import Blueprint, render_template
from flask_login import current_user
from app.services import RoomTypeService, HotelService
from app.extensions import db, cache
from app.models import UserRole
from app.services.recommendation_service import RecommendationService

# Định nghĩa Blueprint cho các tuyến đường chính
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    room_type_service = RoomTypeService(db.session)
    room_type_pagination = room_type_service.get_room_types()

    hotel_service = HotelService(db.session)
    hotels_pagination = hotel_service.get_hotels(per_page=4)
    
    return render_template(
        'index.html',
        room_type_pagination=room_type_pagination,
        hotels=hotels_pagination.items,
        UserRole=UserRole
    )

@main_bp.route('/api/recommendations')
def api_recommendations():
    # Phân loại người dùng và thiết lập Cache Key / Thời gian Cache
    if current_user.is_authenticated:
        cache_key = f"recommendations_user_{current_user.id}"
        timeout = 3600 # 1 tiếng
    else:
        cache_key = "recommendations_guest"
        timeout = 10800 # 3 tiếng
        
    # Kiểm tra xem HTML đã được sinh ra và lưu trong RAM chưa
    cached_html = cache.get(cache_key)
    if cached_html:
        return cached_html

    # Nếu chưa có trong RAM, tiến hành chạy AI để sinh kết quả
    user = current_user if current_user.is_authenticated else None
    recommendation_service = RecommendationService(db.session)
    recommended_hotels = recommendation_service.get_recommended_hotels(user=user, limit=4)
    
    # Render ra giao diện HTML
    html = render_template('partials/recommendations.html', recommended_hotels=recommended_hotels)
    
    # Lưu lại HTML vào RAM để dùng cho các lần sau
    cache.set(cache_key, html, timeout=timeout)
    
    return html
