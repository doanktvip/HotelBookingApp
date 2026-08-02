from flask_mail import Message
from flask import current_app, render_template
from app.extensions import mail

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
