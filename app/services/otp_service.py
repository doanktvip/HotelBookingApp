import random
from datetime import timedelta

from flask import g
from app.models import OTP, get_vn_time
from app.services import BaseService

class OTPService(BaseService):
    def create_otp_code(self):
        return str(random.randint(0, 999999)).zfill(6)

    def save_otp(self, user_id, otp_code):
        self.db.query(OTP).filter_by(user_id=user_id, is_used=False).update({'is_used': True})
        
        expiration_minutes = g.otp_expiration_minutes
        now = get_vn_time()
        expires_at = now + timedelta(minutes=expiration_minutes)
        
        new_otp = OTP(
            user_id=user_id,
            otp_code=otp_code,
            created_at=now,
            expires_at=expires_at,
            is_used=False
        )
        self.db.add(new_otp)
        self.commit_or_rollback()
        return new_otp

    def verify_otp(self, user, otp_code):
        otp_records = self.db.query(OTP).filter_by(
            user_id=user.id, 
            otp_code=otp_code, 
            is_used=False
        ).all()
        
        if len(otp_records) > 1:
            for record in otp_records:
                record.is_used = True
            self.commit_or_rollback()
            raise ValueError("Phát hiện sự cố bảo mật. Mã hiện tại đã bị hủy, vui lòng lấy mã mới!")
            
        if not otp_records:
            raise ValueError("Mã xác thực không hợp lệ hoặc đã được sử dụng.")
            
        otp_record = otp_records[0]
            
        now = get_vn_time()
        if now > otp_record.expires_at:
            raise ValueError("Mã xác thực đã hết hạn.")
            
        otp_record.is_used = True
        user.is_verified=True
        self.commit_or_rollback()
        return True

    def has_active_otp(self, user_id):
        otp_records = self.db.query(OTP).filter_by(
            user_id=user_id, 
            is_used=False
        ).all()

        if len(otp_records) > 1:
            for record in otp_records:
                record.is_used = True
            self.commit_or_rollback()
            return False
        
        if not otp_records:
            return False
            
        otp_record = otp_records[0]
        now = get_vn_time()
        if now > otp_record.expires_at:
            return False
            
        return True
