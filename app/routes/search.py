from flask import Blueprint, render_template, request
from flask_login import current_user
from app.services.search_service import SearchService

search_bp = Blueprint('search', __name__, url_prefix='/tim-kiem')
search_service = SearchService()


@search_bp.route('/', methods=['GET'])
def search():
    mode = request.args.get('mode', 'filter')
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('q', '').strip()
    user = current_user if current_user.is_authenticated else None

    if mode == 'keyword' and keyword:
        pagination = search_service.search_by_keyword(keyword, page=page, user=user)
    else:
        mode = 'filter'
        filters = {
            'location': request.args.get('location', '').strip(),
            'check_in': request.args.get('check_in', '').strip(),
            'check_out': request.args.get('check_out', '').strip(),
            'min_price': request.args.get('min_price', type=float),
            'max_price': request.args.get('max_price', type=float),
            'capacity': request.args.get('capacity', type=int),
            'tag_ids': request.args.getlist('tags', type=int),
            'rating_min': request.args.get('rating_min', type=float),
            'sort_by': request.args.get('sort_by', 'rating_desc'),
        }
        pagination = search_service.search_by_filter(filters, page=page)

    return render_template(
        'search.html',
        pagination=pagination,
        mode=mode,
        keyword=keyword,
        recommended_hotels=search_service.get_recommended_hotels(user=user),
        recommended_room_types=search_service.get_recommended_room_types(),
        all_tags=search_service.get_all_tags(),
    )
