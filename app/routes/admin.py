from flask import Blueprint, g, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models import PricePrediction, Hotel, UserRole, SystemConfig
from app.services.prediction_service import PredictionService
from app.utils import get_vn_time
from datetime import timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
def require_admin():
    if current_user.role != UserRole.ADMIN:
        flash("Bạn không có quyền truy cập trang quản trị.", "danger")
        return redirect(url_for('main.index'))

@admin_bp.route('/predictions', methods=['GET'])
def predictions():
    today = get_vn_time().date()
    end_date = today + timedelta(days=7)
    
    predictions = db.session.query(PricePrediction).join(Hotel).filter(
        PricePrediction.target_date >= today,
        PricePrediction.target_date <= end_date
    ).order_by(PricePrediction.target_date.asc(), Hotel.name.asc()).all()
    
    return render_template('admin/predictions.html', predictions=predictions)

@admin_bp.route('/predictions/<int:prediction_id>/toggle', methods=['POST'])
def toggle_prediction(prediction_id):
    prediction = db.session.query(PricePrediction).get_or_404(prediction_id)
    prediction.is_applied = not prediction.is_applied
    db.session.commit()
    flash(f"Đã {'áp dụng' if prediction.is_applied else 'hủy áp dụng'} dự báo cho {prediction.hotel.name} ngày {prediction.target_date.strftime('%d/%m/%Y')}.", "success")
    return redirect(url_for('admin.predictions'))

@admin_bp.route('/predictions/run', methods=['POST'])
def run_predictions():
    try:
        prediction_service = PredictionService(db.session)
        upsert_count = prediction_service.run_daily_prediction_job(g.ai_prediction_interval)
        
        flash(f"Đã chạy hệ thống AI dự báo thành công! Có {upsert_count} đề xuất mới/được cập nhật.", "success")
    except Exception as e:
        flash(f"Lỗi khi chạy dự báo AI: {str(e)}", "danger")
        
    return redirect(url_for('admin.predictions'))
