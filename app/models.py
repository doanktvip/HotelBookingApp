import enum
from app.extensions import db
from flask_login import UserMixin
from app.utils import get_vn_time
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Float, Enum, DateTime


class UserRole(enum.Enum):
    ADMIN = 'ADMIN'  # Quản trị viên
    RECEPTIONIST = 'RECEPTIONIST'  # Nhân viên lễ tân
    CUSTOMER = 'CUSTOMER'  # Khách đặt phòng


class RoomStatus(enum.Enum):
    AVAILABLE = 'AVAILABLE'  # Phòng trống
    BOOKED = 'BOOKED'  # Đang được đặt
    OCCUPIED = 'OCCUPIED'  # Đang được sử dụng
    MAINTENANCE = 'MAINTENANCE'  # Đang bảo trì


class BookingStatus(enum.Enum):
    PENDING = 'PENDING'  # Đang chờ xác nhận
    CONFIRMED = 'CONFIRMED'  # Đã xác nhận
    CANCELLED = 'CANCELLED'  # Đã hủy


class PaymentMethod(enum.Enum):
    MOMO = 'MOMO'
    # VNPAY = 'VNPAY'


class PaymentStatus(enum.Enum):
    PENDING = 'PENDING'  # Đang chờ thanh toán
    SUCCESS = 'SUCCESS'  # Thanh toán thành công
    FAILED = 'FAILED'  # Thanh toán thất bại


# ----------------------------------------------------
# 1. BẢNG NGƯỜI DÙNG (USERS)
# ----------------------------------------------------
class User(db.Model, UserMixin):
    """Lớp lưu trữ thông tin tất cả các đối tượng người dùng (Admin, Lễ tân, Khách hàng)."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(UserRole, name='user_roles'), default=UserRole.CUSTOMER, nullable=False)
    created_at = Column(DateTime, default=get_vn_time, nullable=False)

    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')
    search_histories = db.relationship('SearchHistory', backref='user', lazy=True)


# ----------------------------------------------------
# 2. BẢNG KHÁCH SẠN (HOTELS)
# ----------------------------------------------------
class Hotel(db.Model):
    """Lớp lưu trữ thông tin của các khách sạn trên nền tảng."""

    __tablename__ = 'hotels'

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    address = Column(String(255), nullable=False)
    location = Column(String(100), nullable=False)  # Tỉnh/Thành phố phục vụ chức năng tìm kiếm
    description = Column(Text, nullable=True)  # Mô tả khách sạn (Hỗ trợ tìm kiếm theo ngữ nghĩa)
    rating = Column(Float, default=0.0)
    amenities = Column(Text, nullable=True)  # Các tiện nghi chung (Wifi, hồ bơi, bãi đỗ xe...)
    created_at = Column(DateTime, default=get_vn_time, nullable=False)

    # Relationships
    rooms = db.relationship('Room', backref='hotel', lazy=True, cascade='all, delete-orphan')
    room_types = db.relationship('RoomType', backref='hotel', lazy=True, cascade='all, delete-orphan')


# ----------------------------------------------------
# 3. BẢNG LOẠI PHÒNG (ROOM_TYPES)
# ----------------------------------------------------
class RoomType(db.Model):
    """Lớp phân loại phòng tại mỗi khách sạn (Ví dụ: Single, Double, Deluxe, Suite)."""

    __tablename__ = 'room_types'

    id = Column(Integer, primary_key=True)
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)  # Mô tả chi tiết loại phòng (Hỗ trợ gợi ý thông minh)
    base_price = Column(Float, nullable=False)  # Giá cơ bản (chưa áp dụng biến động theo mùa/ngày lễ)
    max_occupancy = Column(Integer, default=2, nullable=False)  # Số lượng khách tối đa
    total_rooms = Column(Integer, default=0, nullable=False)  # Công suất tối đa (Tổng số lượng phòng thuộc loại này)
    amenities = Column(Text, nullable=True)  # Các tiện nghi riêng trong phòng (Tivi, Bồn tắm, Ban công...)

    # Relationships
    rooms = db.relationship('Room', backref='room_type', lazy=True, cascade='all, delete-orphan')
    pricing_rules = db.relationship('RoomPricingRule', backref='room_type', lazy=True, cascade='all, delete-orphan')


# ----------------------------------------------------
# 4. BẢNG PHÒNG CỤ THỂ (ROOMS)
# ----------------------------------------------------
class Room(db.Model):
    """Lớp quản lý từng phòng cụ thể và trạng thái thời gian thực của chúng."""

    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True)
    room_type_id = Column(Integer, ForeignKey('room_types.id'), nullable=False)
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=False)
    room_number = Column(String(50), nullable=False)

    # 4 Trạng thái chính của phòng theo yêu cầu
    status = Column(Enum(RoomStatus, name='room_statuses'), default=RoomStatus.AVAILABLE, nullable=False)

    # Relationships
    booking_details = db.relationship('BookingDetail', backref='room', lazy=True)


# ----------------------------------------------------
# 5. BẢNG ĐƠN ĐẶT PHÒNG (BOOKINGS)
# ----------------------------------------------------
class Booking(db.Model):
    """Lớp lưu trữ thông tin chung của giao dịch đặt phòng."""

    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    total_price = Column(Float, nullable=False)

    # Trạng thái đặt phòng
    status = Column(Enum(BookingStatus, name='booking_statuses'), default=BookingStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=get_vn_time, nullable=False)

    # Relationships
    booking_details = db.relationship('BookingDetail', backref='booking', lazy=True, cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='booking', uselist=False, cascade='all, delete-orphan')


# ----------------------------------------------------
# 6. CHI TIẾT ĐẶT PHÒNG (BOOKING_DETAILS)
# ----------------------------------------------------
class BookingDetail(db.Model):
    """Bảng trung gian liên kết Booking và Room để cho phép khách đặt nhiều phòng cùng lúc (Giới hạn từ 3-5 phòng)."""

    __tablename__ = 'booking_details'

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=False)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    price_at_booking = Column(Float, nullable=False)  # Lưu lại giá phòng thực tế tại thời điểm đặt phòng


# ----------------------------------------------------
# 7. BẢNG THANH TOÁN (PAYMENTS)
# ----------------------------------------------------
class Payment(db.Model):
    """Lớp lưu trữ thông tin giao dịch thanh toán 100% trực tuyến."""

    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'), unique=True, nullable=False)

    # Chỉ áp dụng các hình thức thanh toán trực tuyến
    payment_method = Column(Enum(PaymentMethod, name='payment_methods'), nullable=False)
    amount = Column(Float, nullable=False)  # Số tiền thanh toán (100% giá trị đơn hàng)
    transaction_id = Column(String(100), unique=True, nullable=True)  # Mã giao dịch trả về từ cổng thanh toán

    status = Column(Enum(PaymentStatus, name='payment_statuses'), default=PaymentStatus.PENDING, nullable=False)
    payment_date = Column(DateTime, nullable=True)


# ----------------------------------------------------
# 8. BẢNG QUẢN LÝ MÃ OTP (OTP_CODES)
# ----------------------------------------------------
class OTP(db.Model):
    """Lớp quản lý mã OTP gửi qua Email/SMS để xác thực đăng ký, đăng nhập."""

    __tablename__ = 'otp_codes'

    id = Column(Integer, primary_key=True)
    contact = Column(String(150), nullable=False)  # Email hoặc Số điện thoại nhận OTP
    otp_code = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=get_vn_time, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_verified = Column(Boolean, default=False)


# ----------------------------------------------------
# 9. BẢNG CẤU HÌNH HỆ THỐNG & CHÍNH SÁCH (SYSTEM_CONFIGS)
# ----------------------------------------------------
class SystemConfig(db.Model):
    """Lớp lưu trữ các thiết lập hệ thống động (Ví dụ: số phòng tối đa được đặt, số ngày hủy phòng cho phép)."""

    __tablename__ = 'system_configs'

    id = Column(Integer, primary_key=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)


# ----------------------------------------------------
# 10. BẢNG ĐIỀU CHỈNH / DỰ ĐOÁN GIÁ PHÒNG (ROOM_PRICING_RULES)
# ----------------------------------------------------
class RoomPricingRule(db.Model):
    """Lớp lưu trữ các luật biến động giá phòng để Admin điều chỉnh hoặc phục vụ thuật toán dự đoán giá."""

    __tablename__ = 'room_pricing_rules'

    id = Column(Integer, primary_key=True)
    room_type_id = Column(Integer, ForeignKey('room_types.id'), nullable=False)
    name = Column(String(100), nullable=False)  # Ví dụ: "Mùa hè cao điểm", "Ngày lễ Quốc Khánh"
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Hệ số điều chỉnh giá (Ví dụ: 1.5 là tăng 50%, 0.8 là giảm 20%)
    price_multiplier = Column(Float, default=1.0, nullable=False)

    is_holiday = Column(Boolean, default=False)
    description = Column(Text, nullable=True)


# ----------------------------------------------------
# 11. LỊCH SỬ TÌM KIẾM (SEARCH_HISTORIES) - HỖ TRỢ GỢI Ý THÔNG MINH
# ----------------------------------------------------
class SearchHistory(db.Model):
    """Lớp ghi nhận lịch sử tìm kiếm và nhu cầu tự nhiên của khách hàng phục vụ gợi ý thông minh và tìm kiếm ngữ nghĩa."""

    __tablename__ = 'search_histories'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Null nếu khách chưa đăng nhập
    search_query = Column(Text, nullable=True)  # Đoạn văn bản tự nhiên người dùng nhập vào để tìm kiếm ngữ nghĩa
    location = Column(String(100), nullable=True)
    min_price = Column(Float, nullable=True)
    max_price = Column(Float, nullable=True)
    searched_at = Column(DateTime, default=get_vn_time, nullable=False)
