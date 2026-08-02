import enum
from app.extensions import db, cache
from flask_login import UserMixin
from app.utils import get_vn_time
from datetime import timedelta
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Float, Enum, DateTime, Date, Table, DECIMAL

# ================= ENUMS (Các kiểu liệt kê dùng chung) =================


class TextChoices(enum.Enum):
    def __new__(cls, value, label):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.label = label
        return obj


class UserRole(TextChoices):
    ADMIN = 'ADMIN', 'Quản trị viên'
    RECEPTIONIST = 'RECEPTIONIST', 'Nhân viên lễ tân'
    CUSTOMER = 'CUSTOMER', 'Khách hàng'


class RoomStatus(TextChoices):
    AVAILABLE = 'AVAILABLE', 'Trống'
    BOOKED = 'BOOKED', 'Đã đặt'
    OCCUPIED = 'OCCUPIED', 'Đang ở'
    MAINTENANCE = 'MAINTENANCE', 'Bảo trì'


class BookingStatus(TextChoices):
    CONFIRMED = 'CONFIRMED', 'Đã xác nhận'
    CANCELLED = 'CANCELLED', 'Đã hủy đơn'
    COMPLETED = 'COMPLETED', 'Hoàn tất'


class PaymentMethod(TextChoices):
    MOMO = 'MOMO', 'Ví điện tử MoMo'
    VNPAY = 'VNPAY', 'Cổng thanh toán VNPAY'


class PaymentStatus(TextChoices):
    PENDING = 'PENDING', 'Đang chờ'
    SUCCESS = 'SUCCESS', 'Thành công'
    FAILED = 'FAILED', 'Thất bại'


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
    is_verified = Column(Boolean, default=False, nullable=False)  # Cờ xác nhận tài khoản đã verify email chưa
    created_at = Column(DateTime, default=get_vn_time, nullable=False)  # Thời gian tạo tài khoản
    avatar_url = Column(String(255), nullable=True)
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=True)  # ID khách sạn nếu là Lễ tân

    # Các mối quan hệ (Relationships)
    bookings = db.relationship('Booking', backref='customer', lazy=True, cascade='all, delete-orphan')

    search_histories = db.relationship('SearchHistory', backref='user', lazy=True)
    otps = db.relationship('OTP', backref='owner', lazy=True, cascade='all, delete-orphan')
    hotel = db.relationship('Hotel', backref='receptionists', lazy=True)

hotel_tags = Table('hotel_tags', db.metadata,
    Column('hotel_id', Integer, ForeignKey('hotels.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Tag(db.Model):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    icon = Column(String(50), nullable=True, default="bi-star")


class Hotel(db.Model):
    """Quản lý danh sách các khách sạn trên hệ thống"""

    __tablename__ = 'hotels'

    id = Column(Integer, primary_key=True)  # ID khách sạn
    name = Column(String(150), nullable=False)  # Tên khách sạn
    address = Column(String(255), nullable=False)  # Địa chỉ chi tiết
    location = Column(String(100), nullable=False, index=True)  # Tỉnh/Thành phố (Phục vụ YC1: Tìm theo địa điểm)
    description = Column(Text, nullable=True)  # Mô tả chung về khách sạn
    rating = Column(Float, default=0.0)  # Điểm đánh giá trung bình
    cancellation_policy_days = Column(Integer, default=7, nullable=False)  # Số ngày được phép hủy phòng
    created_at = Column(DateTime, default=get_vn_time, nullable=False)  # Ngày đăng ký khách sạn lên hệ thống
    image_url = Column(String(255), nullable=True)

    # Các mối quan hệ
    room_types = db.relationship('RoomType', backref='hotel', lazy=True, cascade='all, delete-orphan')
    price_predictions = db.relationship('PricePrediction', backref='hotel', lazy=True, cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='hotel', lazy=True)
    tags = db.relationship('Tag', secondary=hotel_tags, lazy='subquery',backref=db.backref('hotels', lazy=True))

    @property
    def min_price(self):
        if self.room_types:
            return min([rt.base_price for rt in self.room_types])
        return 0.0

    @property
    def all_rooms(self):
        return [room for rt in self.room_types for room in rt.rooms]



class RoomType(db.Model):
    """Phân loại phòng (Ví dụ: Standard, Deluxe, Suite) để quản lý giá chung"""

    __tablename__ = 'room_types'

    id = Column(Integer, primary_key=True)  # ID loại phòng
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=False)  # Thuộc khách sạn nào
    name = Column(String(100), nullable=False)  # Tên loại phòng
    description = Column(Text, nullable=True)  # Mô tả chi tiết không gian phòng
    base_price = Column(DECIMAL(15, 2), nullable=False)  # Giá niêm yết cơ bản
    max_occupancy = Column(Integer, default=2, nullable=False)  # Số lượng khách tối đa (Sức chứa)
    bed_count = Column(Integer, default=1, nullable=False)  # Số lượng giường trong phòng
    bed_type = Column(String(50), nullable=True)  # Loại giường (Vd: 1 Giường đôi lớn, 2 Giường đơn...)
    image_url = Column(String(255), nullable=True)  # Ảnh đại diện cho loại phòng này
    is_active = Column(Boolean, default=True)  # Hỗ trợ Soft Delete cho loại phòng

    # Các mối quan hệ
    rooms = db.relationship('Room', backref='room_type', lazy=True)

    def soft_delete(self):
        self.is_active = False
        for room in self.rooms:
            room.is_active = False


class Room(db.Model):
    """Quản lý căn phòng vật lý cụ thể (Ví dụ: Phòng 101, Phòng 102)"""

    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True)  # ID phòng vật lý
    room_type_id = Column(Integer, ForeignKey('room_types.id'), nullable=False)  # Thuộc loại phòng nào
    room_number = Column(String(50), nullable=False)  # Mã/Số phòng thực tế dán trên cửa
    floor = Column(Integer, nullable=True)  # Tầng của phòng (hỗ trợ lọc/xếp phòng)
    is_active = Column(Boolean, default=True, index=True)  # Hỗ trợ "Xóa mềm" (Soft Delete)
    notes = Column(Text, nullable=True)  # Ghi chú riêng cho căn phòng đó
    status = Column(Enum(RoomStatus, name='room_statuses'), default=RoomStatus.AVAILABLE, nullable=False, index=True)

    # Các mối quan hệ
    booking_details = db.relationship('BookingDetail', backref='room', lazy=True)  # Lịch sử được đặt của phòng này


class Booking(db.Model):
    """Đơn đặt phòng chung của khách hàng (Có thể chứa nhiều phòng bên trong)"""

    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True)  # ID mã đơn đặt phòng
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Người đặt
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=False)  # Khách sạn được đặt
    room_type_id = Column(Integer, ForeignKey('room_types.id'), nullable=False)  # Loại phòng được đặt
    booking_date = Column(DateTime, default=get_vn_time, nullable=False)  # Thời điểm tạo đơn đặt phòng
    check_in = Column(Date, nullable=False, index=True)  # Ngày bắt đầu ở
    check_out = Column(Date, nullable=False, index=True)  # Ngày rời đi
    total_price = Column(DECIMAL(15, 2), nullable=False)  # Tổng số tiền cần thanh toán cho đơn này
    status = Column(Enum(BookingStatus, name='booking_statuses'), default=BookingStatus.CONFIRMED, nullable=False)

    # Các mối quan hệ
    booking_details = db.relationship('BookingDetail', backref='booking', lazy=True, cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='booking', uselist=False, cascade='all, delete-orphan')
    room_type = db.relationship('RoomType', backref='bookings', lazy=True)

    @property
    def can_cancel(self):
        policy_date = self.check_in - timedelta(days=self.hotel.cancellation_policy_days)
        return get_vn_time().date() <= policy_date


class BookingDetail(db.Model):
    """Chi tiết từng phòng nằm trong một Đơn đặt phòng (Vì hệ thống cho phép đặt 3-5 phòng/lần)"""

    __tablename__ = 'booking_details'

    id = Column(Integer, primary_key=True)  # ID dòng chi tiết
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=False)  # Thuộc mã đơn đặt phòng nào
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)  # Căn phòng cụ thể được chọn
    price_at_booking = Column(DECIMAL(15, 2), nullable=False)  # Giá của loại phòng chốt ngay tại thời điểm khách đặt


class Payment(db.Model):
    """Giao dịch thanh toán 100% qua cổng trực tuyến (YC3)"""

    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)  # ID giao dịch
    booking_id = Column(Integer, ForeignKey('bookings.id'), unique=True, nullable=False)  # Thuộc về đơn đặt phòng nào
    payment_method = Column(Enum(PaymentMethod, name='payment_methods'), nullable=False)  # Phương thức (MoMo / VNPAY)
    amount = Column(DECIMAL(15, 2), nullable=False)  # Số tiền đã thanh toán (Luôn = 100% total_price)
    transaction_id = Column(String(100), unique=True, nullable=True)  # Mã giao dịch trả về từ MoMo/VNPAY
    status = Column(Enum(PaymentStatus, name='payment_statuses'), default=PaymentStatus.PENDING, nullable=False)
    payment_date = Column(DateTime, nullable=True)  # Thời điểm chuyển tiền thành công


class OTP(db.Model):
    """Lưu trữ mã OTP dùng một lần, có liên kết trực tiếp với User"""

    __tablename__ = 'otp_codes'

    id = Column(Integer, primary_key=True)  # ID mã OTP
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Khóa ngoại nối trực tiếp với bảng User
    otp_code = Column(String(10), nullable=False)  # Chuỗi OTP (VD: 123456)
    created_at = Column(DateTime, default=get_vn_time, nullable=False)  # Thời điểm sinh mã
    expires_at = Column(DateTime, nullable=False)  # Thời điểm mã hết hạn (VD: 5 phút sau khi tạo)
    is_used = Column(Boolean, default=False)  # Đánh dấu OTP đã được dùng chưa (tránh Replay Attack)


class SystemConfig(db.Model):
    """Bảng cấu hình hệ thống động cho phép Admin sửa đổi không cần đụng tới Code (YC3)"""

    __tablename__ = 'system_configs'

    id = Column(Integer, primary_key=True)  # ID cấu hình
    config_key = Column(String(100), unique=True, nullable=False)  # Khóa cấu hình (VD: 'MAX_ROOMS_PER_BOOKING')
    config_value = Column(String(255), nullable=False)  # Giá trị cấu hình (VD: '5')
    description = Column(Text, nullable=True)  # Lời giải thích cho cấu hình này
    
    @staticmethod
    @cache.memoize()
    def get_all_raw_configs():
        configs = SystemConfig.query.all()
        return {c.config_key: c.config_value for c in configs}

    @classmethod
    def get_value(cls, key, default=None, type_func=None):
        all_configs = cls.get_all_raw_configs()
        val = all_configs.get(key)
        
        if val is not None:
            if type_func is None and default is not None:
                type_func = type(default)
                
            if type_func is bool:
                return str(val).lower() == 'true'
                
            if type_func is None:
                return val
                
            try:
                return type_func(val)
            except (ValueError, TypeError):
                return default
                
        return default


class PricePrediction(db.Model):
    """Dữ liệu dự báo/điều chỉnh giá phòng do AI gợi ý hoặc Admin thiết lập (Tính năng nâng cao)"""

    __tablename__ = 'price_predictions'

    id = Column(Integer, primary_key=True)  # ID đề xuất
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=False)  # Áp dụng cho toàn bộ khách sạn
    target_date = Column(Date, nullable=False)  # Ngày áp dụng giá mới (Ví dụ: 30/04/2026)
    adjustment_percentage = Column(Float, nullable=False)  # Tỉ lệ thay đổi giá so với giá gốc (VD: 0.1 = 10%)
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

class PriceHistory(db.Model):
    """Bảng lưu vết lịch sử thay đổi giá (Audit Log cho Admin)"""

    __tablename__ = 'price_histories'

    id = Column(Integer, primary_key=True)
    room_type_id = Column(Integer, ForeignKey('room_types.id'), nullable=False)
    old_price = Column(DECIMAL(15, 2), nullable=False)
    new_price = Column(DECIMAL(15, 2), nullable=False)
    changed_at = Column(DateTime, default=get_vn_time, nullable=False)

class RefundLog(db.Model):
    """Bảng lưu vết các giao dịch hoàn tiền tự động (vd: do Overbooking)"""
    __tablename__ = 'refund_logs'

    id = Column(Integer, primary_key=True)
    order_id = Column(String(100), nullable=False, index=True)
    trans_id = Column(String(100), nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=get_vn_time, nullable=False)
