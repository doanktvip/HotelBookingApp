from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db, socketio
from app.services.otp_service import OTPService
from app.services.user_service import UserService
from app.services.email_service import EmailService
from app.services.booking_service import BookingService
from app.models import BookingStatus

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    otp_service = OTPService(db.session)
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        user_service = UserService(db.session)
        
        if form_type == 'update_profile':
            phone = request.form.get('phone')
            email = request.form.get('email')
            
            try:
                updated = user_service.update_phone_and_email(current_user, phone, email)
                if updated:
                    flash('Cập nhật thông tin thành công!', 'success')
                else:
                    flash('Không có thay đổi nào được thực hiện.', 'info')
            except ValueError as e:
                flash(str(e), 'danger')
            except Exception:
                flash('Đã xảy ra lỗi khi lưu dữ liệu.', 'danger')
                
        elif form_type == 'change_password':
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            try:
                changed = user_service.change_password(current_user, old_password, new_password, confirm_password)
                if changed:
                    flash('Đã thay đổi mật khẩu thành công!', 'success')
            except ValueError as e:
                flash(str(e), 'danger')
            except Exception:
                flash('Đã xảy ra lỗi khi thay đổi mật khẩu.', 'danger')

        elif form_type == 'resend_verify_email':
            otp_code = otp_service.create_otp_code()
            success = EmailService.send_verification_email(current_user.email, otp_code)
            if success:
                otp_service.save_otp(current_user.id, otp_code)
                flash('Đã gửi lại mã xác nhận. Vui lòng kiểm tra email.', 'info')
            else:
                flash('Có lỗi xảy ra khi gửi email, vui lòng thử lại sau.', 'danger')
                
        elif form_type == 'update_avatar':
            avatar_file = request.files.get('avatar')
            if avatar_file and avatar_file.filename:
                try:
                    user_service.update_avatar_with_file(current_user, avatar_file)
                    flash('Cập nhật ảnh đại diện thành công!', 'success')
                except Exception as e:
                    flash(str(e), 'danger')
            else:
                flash('Vui lòng chọn ảnh trước khi tải lên.', 'warning')
        
        elif form_type == 'verify_otp':
            otp_code = request.form.get('otp_code')
            if not otp_code:
                flash('Vui lòng nhập mã xác thực.', 'danger')
            else:
                try:
                    otp_service.verify_otp(current_user, otp_code)
                    flash('Xác thực email thành công!', 'success')
                except ValueError as e:
                    flash(str(e), 'danger')
            
        return redirect(url_for('profile.profile'))
            
    has_active_otp = otp_service.has_active_otp(current_user.id)
    
    return render_template('profile.html', user=current_user, has_active_otp=has_active_otp)

@profile_bp.route('/my-bookings', methods=['GET'])
@login_required
def my_bookings():
    status = request.args.get('status', 'ALL')
    booking_service = BookingService(db.session)
    bookings = booking_service.get_user_bookings(current_user.id, status ,5)
    
    return render_template('my_bookings.html', user=current_user, bookings=bookings, current_status=status, BookingStatus=BookingStatus)

@profile_bp.route('/my-bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking_service = BookingService(db.session)
    try:
        booking = booking_service.cancel_user_booking(booking_id, current_user.id)
        flash('Hủy đặt phòng và hoàn tiền thành công!', 'success')
        
        # Bắn tín hiệu cập nhật số lượng phòng
        socketio.emit('booking_updated', {'hotel_id': booking.hotel_id})
        
    except ValueError as e:
        flash(str(e), 'danger')
        
    return redirect(url_for('profile.my_bookings'))

