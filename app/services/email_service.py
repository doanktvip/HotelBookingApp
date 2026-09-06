import threading
from flask_mail import Message
from flask import current_app, render_template
from app.extensions import mail

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"[EmailService] Lỗi gửi email: {e}")

class EmailService:
    @staticmethod
    def send_verification_email(user_email, otp_code):
        try:
            html_body = render_template('email/verify_email.html', otp_code=otp_code)
            
            msg = Message(
                subject='Mã xác thực tài khoản StayNow',
                recipients=[user_email],
                html=html_body,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )
            mail.send(msg)
            return True
        except Exception as e:
            return False

    @staticmethod
    def send_booking_confirmation_email(booking, user):
        try:
            html_body = render_template('email/booking_confirmation.html', booking=booking, user=user)
            
            msg = Message(
                subject=f'Xác nhận đặt phòng #{booking.id} - StayNow',
                recipients=[user.email],
                html=html_body,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )
            
            # Gửi email trong thread mới để không block luồng hiện tại
            app = current_app._get_current_object()
            thread = threading.Thread(target=send_async_email, args=(app, msg))
            thread.start()
            return True
        except Exception as e:
            print(f"[EmailService] Lỗi khi tạo thread gửi email: {e}")
            return False
