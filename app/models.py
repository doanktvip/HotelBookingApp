import enum
from datetime import datetime
from app.extensions import db
from flask_login import UserMixin
from app.utils import get_vn_time
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Float, Enum, DateTime, Date

# ================= ENUMS (Các kiểu liệt kê dùng chung) =================


class UserRole(enum.Enum):
    ADMIN = 'ADMIN'  # Quản trị viên hệ thống
    RECEPTIONIST = 'RECEPTIONIST'  # Nhân viên lễ tân tại quầy
    CUSTOMER = 'CUSTOMER'  # Khách hàng đặt phòng


class RoomStatus(enum.Enum):
    AVAILABLE = 'AVAILABLE'  # Phòng trống, sẵn sàng cho thuê
    BOOKED = 'BOOKED'  # Đã có người đặt nhưng chưa check-in
    OCCUPIED = 'OCCUPIED'  # Khách đang sử dụng (đã check-in)
    MAINTENANCE = 'MAINTENANCE'  # Phòng đang bảo trì, sửa chữa


class BookingStatus(enum.Enum):
    PENDING = 'PENDING'  # Chờ thanh toán
    CONFIRMED = 'CONFIRMED'  # Đã xác nhận (sau khi thanh toán 100%)
    CANCELLED = 'CANCELLED'  # Đã hủy đơn
    COMPLETED = 'COMPLETED'  # Hoàn tất (khách đã check-out)


class PaymentMethod(enum.Enum):
    MOMO = 'MOMO'
    # VNPAY = 'VNPAY'


class PaymentStatus(enum.Enum):
    PENDING = 'PENDING'  # Đang chờ xử lý
    SUCCESS = 'SUCCESS'  # Giao dịch thành công
    FAILED = 'FAILED'  # Giao dịch thất bại


# ================= MODELS (Định nghĩa Cơ sở dữ liệu) =================


class User(db.Model, UserMixin):
    """Lớp đối tượng người dùng chung (Admin, Lễ tân, Khách hàng)"""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)  # ID duy nhất của người dùng
    username = Column(String(80), unique=True, nullable=False)  # Tên đăng nhập
    email = Column(String(120), unique=True, nullable=False)  # Email (dùng để gửi OTP/Thông báo)
    password = Column(String(255), nullable=False)  # Mật khẩu (đã được mã hóa/hash)
    phone = Column(String(20), nullable=True)  # Số điện thoại liên hệ
    role = Column(Enum(UserRole, name='user_roles'), default=UserRole.CUSTOMER, nullable=False)  # Phân quyền tài khoản
    created_at = Column(DateTime, default=get_vn_time, nullable=False)  # Thời gian tạo tài khoản

    # Các mối quan hệ (Relationships)
    bookings = db.relationship('Booking', backref='customer', lazy=True, cascade='all, delete-orphan')
    search_histories = db.relationship('SearchHistory', backref='user', lazy=True)


class Hotel(db.Model):
    """Quản lý danh sách các khách sạn trên hệ thống"""

    __tablename__ = 'hotels'

    id = Column(Integer, primary_key=True)  # ID khách sạn
    name = Column(String(150), nullable=False)  # Tên khách sạn
    address = Column(String(255), nullable=False)  # Địa chỉ chi tiết
    location = Column(String(100), nullable=False)  # Tỉnh/Thành phố (Phục vụ YC1: Tìm theo địa điểm)
    description = Column(Text, nullable=True)  # Mô tả chung về khách sạn
    rating = Column(Float, default=0.0)  # Điểm đánh giá trung bình
    amenities = Column(Text, nullable=True)  # Các tiện nghi chung (như: Wifi, Hồ bơi, Bãi đỗ xe...)
    cancellation_policy_days = Column(Integer, default=7, nullable=False)  # Số ngày được phép hủy phòng
    created_at = Column(DateTime, default=get_vn_time, nullable=False)  # Ngày đăng ký khách sạn lên hệ thống

    # Các mối quan hệ
    rooms = db.relationship('Room', backref='hotel', lazy=True, cascade='all, delete-orphan')
    room_types = db.relationship('RoomType', backref='hotel', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='hotel', lazy=True)


class RoomType(db.Model):
    """Phân loại phòng (Ví dụ: Standard, Deluxe, Suite) để quản lý giá chung"""

    __tablename__ = 'room_types'

    id = Column(Integer, primary_key=True)  # ID loại phòng
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=False)  # Thuộc khách sạn nào
    name = Column(String(100), nullable=False)  # Tên loại phòng
    description = Column(Text, nullable=True)  # Mô tả chi tiết không gian phòng
    base_price = Column(Float, nullable=False)  # Giá niêm yết cơ bản
    max_occupancy = Column(Integer, default=2, nullable=False)  # Số lượng khách tối đa (Sức chứa)
    amenities = Column(Text, nullable=True)  # Các tiện nghi riêng trong phòng (Bồn tắm, Ban công, Tivi 4K...)

    # Các mối quan hệ
    rooms = db.relationship('Room', backref='room_type', lazy=True, cascade='all, delete-orphan')
    price_predictions = db.relationship('PricePrediction', backref='room_type', lazy=True, cascade='all, delete-orphan')


class Room(db.Model):
    """Quản lý căn phòng vật lý cụ thể (Ví dụ: Phòng 101, Phòng 102)"""

    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True)  # ID phòng vật lý
    room_type_id = Column(Integer, ForeignKey('room_types.id'), nullable=False)  # Thuộc loại phòng nào
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=False)  # Của khách sạn nào
    room_number = Column(String(50), nullable=False)  # Mã/Số phòng thực tế dán trên cửa
    status = Column(Enum(RoomStatus, name='room_statuses'), default=RoomStatus.AVAILABLE, nullable=False)

    # Các mối quan hệ
    booking_details = db.relationship('BookingDetail', backref='room', lazy=True)  # Lịch sử được đặt của phòng này


class Booking(db.Model):
    """Đơn đặt phòng chung của khách hàng (Có thể chứa nhiều phòng bên trong)"""

    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True)  # ID mã đơn đặt phòng
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Người đặt
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=False)  # Khách sạn được đặt
    booking_date = Column(DateTime, default=get_vn_time, nullable=False)  # Thời điểm tạo đơn đặt phòng
    check_in = Column(Date, nullable=False)  # Ngày bắt đầu ở
    check_out = Column(Date, nullable=False)  # Ngày rời đi
    total_price = Column(Float, nullable=False)  # Tổng số tiền cần thanh toán cho đơn này
    status = Column(Enum(BookingStatus, name='booking_statuses'), default=BookingStatus.PENDING, nullable=False)

    # Các mối quan hệ
    booking_details = db.relationship('BookingDetail', backref='booking', lazy=True, cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='booking', uselist=False, cascade='all, delete-orphan')


class BookingDetail(db.Model):
    """Chi tiết từng phòng nằm trong một Đơn đặt phòng (Vì hệ thống cho phép đặt 3-5 phòng/lần)"""

    __tablename__ = 'booking_details'

    id = Column(Integer, primary_key=True)  # ID dòng chi tiết
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=False)  # Thuộc mã đơn đặt phòng nào
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)  # Căn phòng cụ thể được chọn
    price_at_booking = Column(Float, nullable=False)  # Giá của loại phòng chốt ngay tại thời điểm khách đặt


class Payment(db.Model):
    """Giao dịch thanh toán 100% qua cổng trực tuyến (YC3)"""

    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)  # ID giao dịch
    booking_id = Column(Integer, ForeignKey('bookings.id'), unique=True, nullable=False)  # Thuộc về đơn đặt phòng nào
    payment_method = Column(Enum(PaymentMethod, name='payment_methods'), nullable=False)  # Phương thức (MoMo / VNPAY)
    amount = Column(Float, nullable=False)  # Số tiền đã thanh toán (Luôn = 100% total_price)
    transaction_id = Column(String(100), unique=True, nullable=True)  # Mã giao dịch trả về từ MoMo/VNPAY
    status = Column(Enum(PaymentStatus, name='payment_statuses'), default=PaymentStatus.PENDING, nullable=False)
    payment_date = Column(DateTime, nullable=True)  # Thời điểm chuyển tiền thành công


class OTP(db.Model):
    """Lưu trữ mã OTP dùng một lần cho bảo mật đăng nhập/đăng ký"""

    __tablename__ = 'otp_codes'

    id = Column(Integer, primary_key=True)  # ID mã OTP
    contact = Column(String(150), nullable=False)  # Email hoặc Số điện thoại nhận mã
    otp_code = Column(String(10), nullable=False)  # Chuỗi OTP (VD: 123456)
    created_at = Column(DateTime, default=get_vn_time, nullable=False)  # Thời điểm sinh mã
    expires_at = Column(DateTime, nullable=False)  # Thời điểm mã hết hạn (VD: 5 phút sau khi tạo)
    is_verified = Column(Boolean, default=False)  # Cờ đánh dấu OTP đã được người dùng sử dụng chưa


class SystemConfig(db.Model):
    """Bảng cấu hình hệ thống động cho phép Admin sửa đổi không cần đụng tới Code (YC3)"""

    __tablename__ = 'system_configs'

    id = Column(Integer, primary_key=True)  # ID cấu hình
    config_key = Column(String(100), unique=True, nullable=False)  # Khóa cấu hình (VD: 'MAX_ROOMS_PER_BOOKING')
    config_value = Column(String(255), nullable=False)  # Giá trị cấu hình (VD: '5')
    description = Column(Text, nullable=True)  # Lời giải thích cho cấu hình này


class PricePrediction(db.Model):
    """Dữ liệu dự báo/điều chỉnh giá phòng do AI gợi ý hoặc Admin thiết lập (Tính năng nâng cao)"""

    __tablename__ = 'price_predictions'

    id = Column(Integer, primary_key=True)  # ID đề xuất
    room_type_id = Column(Integer, ForeignKey('room_types.id'), nullable=False)  # Áp dụng cho loại phòng nào
    target_date = Column(Date, nullable=False)  # Ngày áp dụng giá mới (Ví dụ: 30/04/2026)
    suggested_price = Column(Float, nullable=False)  # Mức giá mới được đề xuất
    reason = Column(String(255))  # Lý do đổi giá (Ví dụ: "Lễ 30/4", "Mùa thấp điểm")
    is_applied = Column(Boolean, default=False)  # Trạng thái: Admin đã click đồng ý áp dụng mức giá này chưa?


class SearchHistory(db.Model):
    """Lịch sử tìm kiếm của người dùng - Phục vụ Yêu cầu NLP & Gợi ý thông minh (Tính năng nâng cao)"""

    __tablename__ = 'search_histories'

    id = Column(Integer, primary_key=True)  # ID dòng lịch sử
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Khách hàng nào tìm (Nếu chưa đăng nhập thì null)
    search_query = Column(Text, nullable=True)  # Câu truy vấn tự nhiên
    location = Column(String(100), nullable=True)  # Địa điểm trích xuất được
    searched_at = Column(DateTime, default=get_vn_time, nullable=False)  # Thời điểm tìm kiếm
