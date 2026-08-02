import hashlib
import re
from flask import g
from app.models import User
from app.services import BaseService
import cloudinary.uploader

class UserService(BaseService):

    def get_user_by_id(self, user_id):
        return self.get_by_id(User, user_id)
        
    def get_first_user_by(self, **kwargs):
        return User.query.filter_by(**kwargs).first()
    
    def auth_user(self, username, password):
        if not username or not password:
            raise ValueError("Vui lòng nhập đầy đủ dữ liệu!")
        
        # if (len(username) < g.minimum_password_length or len(username) > g.maximum_password_lenght) or (len(password) < g.minimum_password_length or len(password) > g.maximum_password_lenght) or not username.isascii() or not password.isascii() or " " in password or " " in username:
        #     raise ValueError("Tên đăng nhập hoặc mật khẩu không chính xác")
        
        user = self.get_first_user_by(username=username)
        
        if user:
            hashed_input_password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
            
            if user.password == hashed_input_password:
                return user
            
        raise ValueError("Tên đăng nhập hoặc mật khẩu không chính xác")

    def add_user(self,username,email,password,confirm_password):
        if not username or not email or not password or not confirm_password:
            raise ValueError("Vui lòng nhập đầy đủ dữ liệu!")

        if password != confirm_password:
            raise ValueError("Mật khẩu xác nhận không khớp.")

        if len(username) < g.min_len or len(username) > g.max_len:
            raise ValueError(f"Tên đăng nhập phải từ {g.min_len} đến {g.max_len} ký tự.")

        if len(password) < g.min_len or len(password) > g.max_len:
            raise ValueError(f"Mật khẩu phải từ {g.min_len} đến {g.max_len} ký tự.")
            
        if not username.isascii():
            raise ValueError("Tên đăng nhập chỉ được dùng các ký tự cơ bản.")

        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            raise ValueError("Định dạng email không hợp lệ (ví dụ: abc@gmail.com).")
            
        if not email.isascii():
            raise ValueError("Email chỉ được dùng các ký tự cơ bản.")
        
        if not password.isascii():
            raise ValueError("Mật khẩu chỉ được dùng các ký tự cơ bản.")
            
        if " " in password or " " in username or " " in email:
            raise ValueError("Tên đăng nhập, email và mật khẩu không được chứa khoảng trắng.")
        
        existing_email = self.get_first_user_by(email=email)
        if existing_email:
            raise ValueError("Email đã tồn tại!")

        existing_user = self.get_first_user_by(username=username)
        if existing_user:
            raise ValueError("Tên đăng nhập đã tồn tại!")
        
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())

        new_user = User(
            username=username,
            email=email,
            password=password
        )

        # Đưa vào phiên giao dịch (phiên nháp)
        self.db.add(new_user)
        
        self.commit_or_rollback()
        
        return new_user
    
    def update_phone_and_email(self, user, phone, email):            
        updated = False
        
        if phone is not None and user.phone != phone:
            if phone != "":
                if not phone.isdigit():
                    raise ValueError("Số điện thoại chỉ được chứa các chữ số.")
                
                if len(phone) != 10:
                    raise ValueError("Số điện thoại phải có đúng 10 chữ số.")
                
            user.phone = phone
            updated = True
            
        if email is not None and user.email != email:
            if not email:
                raise ValueError("Vui lòng không để trống email!")

            if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
                raise ValueError("Định dạng email không hợp lệ (ví dụ: abc@gmail.com).")

            if not email.isascii():
                raise ValueError("Email chỉ được dùng các ký tự cơ bản.")

            if " " in email:
                raise ValueError("Email không được chứa khoảng trắng.")
                
            existing_user = self.get_first_user_by(email=email)
            if existing_user and existing_user.id != user.id:
                raise ValueError("Email này đã được sử dụng bởi tài khoản khác!")
            
            user.email = email
            user.is_verified = False
            updated = True
            
        if updated:
            self.commit_or_rollback()
            
        return updated
    
    def change_password(self, user, old_password, new_password, confirm_new_password):
        if not user or not old_password or not new_password or not confirm_new_password:
            raise ValueError("Vui lòng nhập đầy đủ dữ liệu!")
        
        hashed_old_password = str(hashlib.md5(old_password.strip().encode('utf-8')).hexdigest())
        
        if user.password != hashed_old_password:
            raise ValueError("Mật khẩu cũ không chính xác!")
        
        if new_password != confirm_new_password:
            raise ValueError("Mật khẩu xác nhận không khớp!")
        
        if len(new_password) < g.min_len or len(new_password) > g.max_len:
            raise ValueError(f"Mật khẩu phải từ {g.min_len} đến {g.max_len} ký tự.")
        
        if not new_password.isascii():
            raise ValueError("Mật khẩu chỉ được dùng các ký tự cơ bản.")
        
        if " " in new_password:
            raise ValueError("Mật khẩu không được chứa khoảng trắng.")
                
        user.password = str(hashlib.md5(new_password.strip().encode('utf-8')).hexdigest())
        self.commit_or_rollback()
        
        return True
        

    def update_avatar_with_file(self, user, avatar_file):
        try:
            upload_result = cloudinary.uploader.upload(avatar_file)
            secure_url = upload_result.get('secure_url')
            
            if secure_url:
                user.avatar_url = secure_url
                self.commit_or_rollback()
                return True
            else:
                raise ValueError("Không thể lấy đường dẫn ảnh từ máy chủ.")
        except Exception as e:
            raise ValueError(f"Lỗi khi tải ảnh lên hệ thống: {str(e)}")