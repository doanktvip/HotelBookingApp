import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import current_user
from app.extensions import db
from app.models import SearchHistory, UserRole

search_history_bp = Blueprint('search_history', __name__)


def get_current_user_or_guest():
    """Lấy user_id hoặc session_id cho khách vãng lai"""
    if current_user.is_authenticated:
        return current_user.id, None
    
    if 'guest_id' not in session:
        session['guest_id'] = str(uuid.uuid4())
    return None, session['guest_id']


@search_history_bp.route('/search-history', methods=['GET'])
def view_history():
    """Xem danh sách lịch sử tìm kiếm của người dùng hiện tại, sắp xếp mới nhất lên đầu"""
    user_id, session_id = get_current_user_or_guest()
    
    if user_id:
        query = SearchHistory.query.filter(SearchHistory.user_id == user_id)
    else:
        query = SearchHistory.query.filter(
            (SearchHistory.session_id == session_id) | (SearchHistory.ip_address == request.remote_addr),
            SearchHistory.user_id.is_(None)
        )
    
    histories = query.order_by(SearchHistory.created_at.desc()).all()
    
    return render_template('search_history.html', histories=histories)


@search_history_bp.route('/search-history/<int:history_id>', methods=['DELETE'])
@search_history_bp.route('/search-history/<int:history_id>/delete', methods=['POST'])
def delete_item(history_id):
    """Xóa một mục lịch sử tìm kiếm cụ thể"""
    item = db.session.get(SearchHistory, history_id)
    if not item:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'Không tìm thấy mục lịch sử'}), 404
        flash('Không tìm thấy mục lịch sử cần xóa.', 'warning')
        return redirect(url_for('search_history.view_history'))

    user_id, session_id = get_current_user_or_guest()
    is_owner = False
    
    if user_id:
        if item.user_id == user_id or (current_user.is_authenticated and current_user.role == UserRole.ADMIN):
            is_owner = True
    else:
        if item.session_id == session_id or item.ip_address == request.remote_addr:
            is_owner = True

    if not is_owner:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'Bạn không có quyền xóa mục này'}), 403
        flash('Bạn không có quyền xóa mục lịch sử này.', 'danger')
        return redirect(url_for('search_history.view_history'))

    db.session.delete(item)
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json or request.method == 'DELETE':
        return jsonify({'success': True, 'message': 'Đã xóa lịch sử tìm kiếm thành công'})

    flash('Đã xóa mục lịch sử tìm kiếm thành công.', 'success')
    return redirect(url_for('search_history.view_history'))


@search_history_bp.route('/search-history/clear', methods=['POST'])
def clear_all():
    """Xóa toàn bộ lịch sử tìm kiếm của người dùng hiện tại"""
    user_id, session_id = get_current_user_or_guest()

    if user_id:
        SearchHistory.query.filter(SearchHistory.user_id == user_id).delete(synchronize_session=False)
    else:
        SearchHistory.query.filter(
            (SearchHistory.session_id == session_id) | (SearchHistory.ip_address == request.remote_addr),
            SearchHistory.user_id.is_(None)
        ).delete(synchronize_session=False)

    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'message': 'Đã xóa toàn bộ lịch sử tìm kiếm'})

    flash('Đã làm sạch toàn bộ lịch sử tìm kiếm.', 'success')
    return redirect(url_for('search_history.view_history'))


@search_history_bp.route('/search-history/<int:history_id>/re-search', methods=['GET'])
def re_search(history_id):
    """Tìm lại: Redirect sang trang tìm kiếm với các tham số tương ứng đã lưu"""
    item = db.session.get(SearchHistory, history_id)
    if not item:
        flash('Không tìm thấy bản ghi lịch sử.', 'warning')
        return redirect(url_for('hotel.hotel'))

    params = {}
    if item.keyword:
        params['keyword'] = item.keyword
    if item.location:
        params['location'] = item.location
    if item.check_in_date:
        params['check_in'] = item.check_in_date.strftime('%Y-%m-%d')
    if item.check_out_date:
        params['check_out'] = item.check_out_date.strftime('%Y-%m-%d')
    if item.guest_count and item.guest_count > 1:
        params['guest_count'] = item.guest_count
    if item.room_count and item.room_count > 1:
        params['room_count'] = item.room_count

    return redirect(url_for('hotel.hotel', **params))
