import os
import random
import copy
from app import create_app
from app.extensions import db
from app.models import (
    Hotel, RoomType, Room, User, UserRole, RoomStatus, Tag,
    Booking, BookingDetail, Payment, BookingStatus, PaymentMethod, PaymentStatus,
    SystemConfig, OTP, PricePrediction, SearchHistory, PriceHistory
)
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

TAGS_DATA = [
    'Wifi',
    'Bãi biển riêng',
    'Hồ bơi',
    'Spa',
    'Gym',
    'Buffet sáng',
    'Quán Bar',
    'Lò sưởi',
    'Buffet tối',
    'View núi',
    'View biển',
    'Đưa đón sân bay',
    'Bãi đậu xe miễn phí',
    'Lễ tân 24/7',
    'Cho phép mang thú cưng',
    'Sân chơi trẻ em',
    'Khu vực hút thuốc'
]
HOTELS_DATA = [
    {
        'name': 'The Reverie Saigon',
        'address': '22-36 Nguyễn Huệ, Quận 1',
        'location': 'Thành phố Hồ Chí Minh',
        'description': 'Khách sạn 5 sao mang phong cách hoàng gia Ý tráng lệ, tọa lạc ngay phố đi bộ Nguyễn Huệ với tầm nhìn tuyệt đẹp ra sông Sài Gòn. Nơi hội tụ các nhà hàng ẩm thực cao cấp và không gian xa hoa bậc nhất.',
        'rating': 4.9,
        'cancellation_policy_days': 7,
        'image_url': 'https://res.cloudinary.com/db4bjqp4f/image/upload/v1785210595/The_Reverie_Saigon_qah7dr.avif',
    },
    {
        'name': 'Vinpearl Landmark 81, Autograph Collection',
        'address': '720A Điện Biên Phủ, Phường 22, Quận Bình Thạnh',
        'location': 'Thành phố Hồ Chí Minh',
        'description': 'Tọa lạc trên đỉnh tòa tháp cao nhất Việt Nam, khách sạn mang đến trải nghiệm lưu trú giữa những tầng mây. Hồ bơi vô cực ngoài trời, dịch vụ spa chuẩn quốc tế và tầm nhìn panorama bao trọn thành phố.',
        'rating': 4.8,
        'cancellation_policy_days': 7,
        'image_url': 'https://res.cloudinary.com/db4bjqp4f/image/upload/v1785210171/Vinpearl_Landmark_81_Autograph_Collection_rfpu0e.jpg',
    },
    {
        'name': 'Caravelle Saigon',
        'address': '19-23 Công trường Lam Sơn, Quận 1',
        'location': 'Thành phố Hồ Chí Minh',
        'description': 'Khách sạn biểu tượng mang đậm dấu ấn lịch sử nằm ngay kế bên Nhà hát Lớn Thành phố. Nổi tiếng với quán bar Saigon Saigon Rooftop và dịch vụ đẳng cấp thế giới.',
        'rating': 4.7,
        'cancellation_policy_days': 3,
        'image_url': 'https://res.cloudinary.com/db4bjqp4f/image/upload/v1785210167/Caravelle_Saigon_v7qmdy.jpg',
    },
    {
        'name': 'Liberty Central Saigon Citypoint',
        'address': '59 Pasteur, Phường Bến Nghé, Quận 1',
        'location': 'Thành phố Hồ Chí Minh',
        'description': 'Khách sạn 4 sao hiện đại nổi bật với rạp chiếu phim nội khu đầu tiên và duy nhất tại Sài Gòn. Hồ bơi sân thượng và quầy bar lý tưởng để thư giãn.',
        'rating': 4.5,
        'cancellation_policy_days': 7,
        'image_url': 'https://res.cloudinary.com/db4bjqp4f/image/upload/v1785210594/Liberty_Central_Saigon_Citypoint_o0d8bk.webp',
    },
    {
        'name': 'La Vela Saigon Hotel',
        'address': '280 Nam Kỳ Khởi Nghĩa, Phường 8, Quận 3',
        'location': 'Thành phố Hồ Chí Minh',
        'description': 'Sở hữu hồ bơi vô cực trên tầng thượng lớn nhất thành phố. Thiết kế sang trọng, tầm nhìn cực đẹp và ẩm thực đa dạng từ Á sang Âu.',
        'rating': 4.6,
        'cancellation_policy_days': 5,
        'image_url': 'https://res.cloudinary.com/db4bjqp4f/image/upload/v1785210166/La_Vela_Saigon_Hotel_edwakw.jpg',
    },
    {
        'name': 'Ibis Saigon Airport',
        'address': '2 Hồng Hà, Phường 2, Tân Bình',
        'location': 'Thành phố Hồ Chí Minh',
        'description': 'Chỉ cách sân bay Tân Sơn Nhất 5 phút đi bộ. Dịch vụ lưu trú thuận tiện, hiện đại, tích hợp The Hub bar và hồ bơi tầng thượng thư giãn.',
        'rating': 4.3,
        'cancellation_policy_days': 1,
        'image_url': 'https://res.cloudinary.com/db4bjqp4f/image/upload/v1785210594/Ibis_Saigon_Airport_tvbftn.webp',
    },
    {
        'name': 'Hotel Des Arts Saigon, MGallery',
        'address': '76-78 Nguyễn Thị Minh Khai, Quận 3',
        'location': 'Thành phố Hồ Chí Minh',
        'description': 'Một tác phẩm nghệ thuật kiến trúc kết hợp giữa nét lãng mạn của Pháp và vẻ đẹp đương đại Á Đông. Tự hào với bể bơi vô cực và Social Club độc đáo.',
        'rating': 4.8,
        'cancellation_policy_days': 7,
        'image_url': 'https://res.cloudinary.com/db4bjqp4f/image/upload/v1785210166/Hotel_Des_Arts_Saigon_MGallery_tdvivl.jpg',
    },
    {
        'name': 'New World Saigon Hotel',
        'address': '76 Lê Lai, Phường Bến Thành, Quận 1',
        'location': 'Thành phố Hồ Chí Minh',
        'description': 'Tọa lạc đối diện công viên 23/9 trong lành, kế bên chợ Bến Thành nhộn nhịp. Một điểm dừng chân hoàn hảo cho cả công tác và nghỉ dưỡng.',
        'rating': 4.6,
        'cancellation_policy_days': 7,
        'image_url': 'https://res.cloudinary.com/db4bjqp4f/image/upload/v1785210595/New_World_Saigon_Hotel_btv6pa.jpg',
    },
    {
        'name': 'Bay Hotel Ho Chi Minh',
        'address': '7 Ngô Văn Năm, Phường Bến Nghé, Quận 1',
        'location': 'Thành phố Hồ Chí Minh',
        'description': 'Khách sạn phong cách boutique hiện đại nằm khuất trong con đường rợp bóng cây ngay trung tâm Sài Gòn, dễ dàng tản bộ ra bến Bạch Đằng.',
        'rating': 4.2,
        'cancellation_policy_days': 3,
        'image_url': 'https://res.cloudinary.com/db4bjqp4f/image/upload/v1785210594/Bay_Hotel_Ho_Chi_Minh_tpawal.jpg',
    },
    {
        'name': 'Muong Thanh Luxury Saigon Hotel',
        'address': '261C Nguyễn Văn Trỗi, Phường 10, Phú Nhuận',
        'location': 'Thành phố Hồ Chí Minh',
        'description': 'Với phong cách trang trọng và mến khách mang đậm văn hóa Việt Nam. Điểm dừng chân lý tưởng trên trục đường nối sân bay và trung tâm.',
        'rating': 4.4,
        'cancellation_policy_days': 7,
        'image_url': 'https://res.cloudinary.com/db4bjqp4f/image/upload/v1785210170/Muong_Thanh_Luxury_Saigon_Hotel_opbhtp.jpg',
    },
    {
        'name': 'Silverland Yen Hotel',
        'address': '73-75 Thủ Khoa Huân, Phường Bến Thành, Quận 1',
        'location': 'Thành phố Hồ Chí Minh',
        'description': 'Một chốn bình yên tĩnh lặng mang hơi thở của thiền định giữa lòng Sài Gòn ồn ào náo nhiệt. Trà chiều miễn phí và Jacuzzi trên sân thượng.',
        'rating': 4.7,
        'cancellation_policy_days': 3,
        'image_url': 'https://res.cloudinary.com/db4bjqp4f/image/upload/v1785210169/Silverland_Yen_Hotel_wuihya.jpg',
    },
    {
        'name': 'Pullman Saigon Centre',
        'address': '148 Trần Hưng Đạo, Phường Nguyễn Cư Trinh, Quận 1',
        'location': 'Thành phố Hồ Chí Minh',
        'description': 'Sở hữu không gian sống hiện đại, view cực đỉnh nhìn toàn cảnh Sài Gòn. Nổi tiếng với ẩm thực thịt nướng cao cấp và Rooftop bar sôi động.',
        'rating': 4.6,
        'cancellation_policy_days': 7,
        'image_url': 'https://res.cloudinary.com/db4bjqp4f/image/upload/v1785210170/Pullman_Saigon_Centre_kekfqc.jpg',
    }
]

ROOM_TYPES_DATA = [
    {
        "name": "Standard",
        "desc": "Phòng tiêu chuẩn, mức giá cơ bản nhất với các tiện nghi thiết yếu.",
        "price": 800000.0,
    },
    {
        "name": "Superior",
        "desc": "Phòng chất lượng cao hơn, không gian rộng rãi và thoải mái hơn so với phòng Standard.",
        "price": 1200000.0,
    },
    {
        "name": "Deluxe",
        "desc": "Phòng sang trọng, thường nằm ở các tầng cao với tầm nhìn đẹp và nội thất cao cấp.",
        "price": 2000000.0,
    },
    {
        "name": "Suite",
        "desc": "Phòng thượng hạng, diện tích rất lớn, thường được thiết kế với khu vực phòng khách và phòng ngủ hoàn toàn riêng biệt.",
        "price": 5500000.0,
    },
    {
        "name": "Family Room",
        "desc": "Phòng dành cho gia đình, không gian rộng và được bố trí nhiều giường (giường đôi, giường đơn hoặc giường tầng) để phù hợp cho nhóm đông người.",
        "price": 3500000.0,
    }
]

ROOM_TYPE_IMAGES = {
    "Standard": [
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213202/Standard7_rny3ae.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213201/Standard6_un7hj1.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213200/Standard5_rkey00.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213200/Standard4_wozpkp.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213199/Standard3_zrytbc.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213199/Standard2_wu01wl.webp",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213198/Standard1_afqhsk.webp"
    ],
    "Superior": [
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213206/Superior6_v8bxty.webp",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213205/Superior5_eicsvr.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213205/Superior4_yy2j8g.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213204/Superior3_wgrh9q.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213204/Superior2_bkojp9.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213203/Superior1_hpfpfj.jpg"
    ],
    "Deluxe": [
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213197/Deluxe5_z6ug8k.webp",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213197/Deluxe4_kqwjji.webp",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213197/Deluxe3_rht7id.webp",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213197/Deluxe2_h2infy.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213197/Deluxe1_etbfsb.webp"
    ],
    "Suite": [
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213203/Suite4_ah776w.webp",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213202/Suite3_dy2bos.webp",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213202/Suite2_dwuo8m.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213201/Suite1_xoxnnx.webp"
    ],
    "Family Room": [
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213294/Family_Room3_taeubz.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213198/Family_Room2_plc68e.webp",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213197/Family_Room1_udwamd.webp"
    ]
}

PASSWORD='123'

USERS_DATA = [
    {
        "username": "admin",
        "email": "admin@hotel.com",
        "password": PASSWORD,
        "role": UserRole.ADMIN,
        "is_verified": True,
    }
]

# Tạo 30 tài khoản khách hàng
for i in range(1, 31):
    USERS_DATA.append({
        "username": f"khachhang{i}",
        "email": f"khachhang{i}@hotel.com",
        "password": PASSWORD,
        "role": UserRole.CUSTOMER,
        "is_verified": True,
    })

def seed_users():
    print("Đang tạo Users...")
    for u_data in USERS_DATA:
        user = User(
            username=u_data["username"],
            email=u_data["email"],
            password=generate_password_hash(u_data["password"]),
            role=u_data["role"],
            is_verified=u_data["is_verified"],
        )
        db.session.add(user)
    db.session.commit()

def get_or_create_tag(tag_name):
    tag = db.session.query(Tag).filter_by(name=tag_name).first()
    if not tag:
        tag = Tag(name=tag_name)
        db.session.add(tag)
        db.session.commit()
    return tag

def seed_hotels_and_tags():
    print("Đang tạo Khách sạn và gán Tags...")
    created_hotels = []
    
    for h_data in HOTELS_DATA:
        hotel_dict = copy.deepcopy(h_data)
        hotel = Hotel(**hotel_dict)
        db.session.add(hotel)
        
        # Vì bạn đã xóa amenities cứng của từng khách sạn,
        # mình sẽ cho script tự bốc ngẫu nhiên 5-7 tag từ TAGS_DATA gán cho mỗi khách sạn luôn cho tiện.
        num_tags = random.randint(5, 7)
        selected_tags = random.sample(TAGS_DATA, k=num_tags)
        for t_name in selected_tags:
            tag = get_or_create_tag(t_name)
            hotel.tags.append(tag)
            
        created_hotels.append(hotel)
        
    db.session.commit()
    return created_hotels

def seed_rooms(created_hotels):
    print("Đang tạo Loại phòng (lấy theo cấp bậc) và Căn phòng vật lý...")
    for hotel in created_hotels:
        # Lấy từ 2 đến 5 loại phòng, LẤY THEO BẬC TỪ THẤP ĐẾN CAO
        num_rt = random.randint(2, 5)
        selected_rts = ROOM_TYPES_DATA[:num_rt]
        
        created_room_types = []
        for rt in selected_rts:
            # Randomize price (dao động +- 20% so với giá gốc, làm tròn đến 50k)
            base_price = rt["price"]
            variation = random.uniform(0.8, 1.2)
            final_price = round((base_price * variation) / 50000) * 50000
            
            # Chọn ngẫu nhiên 1 ảnh từ thư viện ảnh theo đúng tên loại phòng
            rt_name = rt["name"]
            
            # Khắc phục lỗi KeyError do thư viện ảnh cần mặc định
            images_list = ROOM_TYPE_IMAGES[rt_name]
            final_image = random.choice(images_list)
            
            # Random bed_type và bed_count (1 hoặc 2)
            final_bed_type = random.choice(["giường đôi", "giường đơn"])
            final_bed_count = random.choice([1, 2])
            
            # Tính max_occupancy dựa trên bed_count và bed_type
            if final_bed_type == "giường đôi":
                final_max_occupancy = final_bed_count * 2
            else:
                final_max_occupancy = final_bed_count * 1
            
            room_type = RoomType(
                hotel_id=hotel.id,
                name=rt["name"],
                description=rt["desc"],
                base_price=final_price,
                max_occupancy=final_max_occupancy,
                bed_count=final_bed_count,
                bed_type=final_bed_type,
                image_url=final_image,
            )
            db.session.add(room_type)
            created_room_types.append(room_type)
        db.session.commit()

        # Tạo ngẫu nhiên 15 phòng cho các RoomType này
        for i in range(1, 11):
            rt = random.choice(created_room_types)
            floor_num = random.randint(1, 5)
            room = Room(
                room_type_id=rt.id,
                room_number=f"{floor_num}0{i % 10}",
                floor=floor_num,
                is_active=True,
                notes=None,
                status=RoomStatus.AVAILABLE,
            )
            db.session.add(room)
    db.session.commit()

def seed_receptionists(created_hotels):
    print("Đang tạo 12 Lễ tân cho 12 khách sạn...")
    for i, hotel in enumerate(created_hotels):
        receptionist = User(
            username=f"letan{i+1}",
            email=f"letan{i+1}@hotel.com",
            password=generate_password_hash(PASSWORD),
            role=UserRole.RECEPTIONIST,
            is_verified=True,
            hotel_id=hotel.id
        )
        db.session.add(receptionist)
    db.session.commit()

def seed_bookings_and_payments(created_hotels):
    print("Đang tạo Bookings và Payments với đa dạng trạng thái...")
    customers = User.query.filter_by(role=UserRole.CUSTOMER).all()
    
    for customer in customers:
        hotel = random.choice(created_hotels)
        # Lấy phòng trống
        available_rooms = Room.query.filter_by(status=RoomStatus.AVAILABLE).join(RoomType).filter(RoomType.hotel_id == hotel.id).all()
        if not available_rooms:
            continue
            
        num_rooms = random.randint(1, min(2, len(available_rooms)))
        selected_rooms = random.sample(available_rooms, num_rooms)
        
        b_status = random.choice([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.COMPLETED])
        
        if b_status == BookingStatus.COMPLETED:
            check_in_date = datetime.now().date() - timedelta(days=random.randint(3, 10))
            p_status = PaymentStatus.SUCCESS
            r_status = RoomStatus.AVAILABLE 
        elif b_status == BookingStatus.CANCELLED:
            check_in_date = datetime.now().date() + timedelta(days=random.randint(1, 10))
            p_status = random.choice([PaymentStatus.FAILED, PaymentStatus.PENDING])
            r_status = RoomStatus.AVAILABLE 
        elif b_status == BookingStatus.PENDING:
            check_in_date = datetime.now().date() + timedelta(days=random.randint(1, 10))
            p_status = PaymentStatus.PENDING
            r_status = RoomStatus.AVAILABLE 
        else: # CONFIRMED
            check_in_date = datetime.now().date() + timedelta(days=random.randint(1, 10))
            p_status = PaymentStatus.SUCCESS
            r_status = random.choice([RoomStatus.BOOKED, RoomStatus.OCCUPIED])
            
        check_out_date = check_in_date + timedelta(days=random.randint(1, 3))
        num_days = (check_out_date - check_in_date).days
        
        booking = Booking(
            user_id=customer.id,
            hotel_id=hotel.id,
            check_in=check_in_date,
            check_out=check_out_date,
            status=b_status,
            total_price=0 
        )
        db.session.add(booking)
        db.session.flush() 
        
        total_price = 0
        for room in selected_rooms:
            room.status = r_status 
            price = room.room_type.base_price
            total_price += price * num_days
            
            detail = BookingDetail(
                booking_id=booking.id,
                room_id=room.id,
                price_at_booking=price
            )
            db.session.add(detail)
            
        booking.total_price = total_price
        
        payment = Payment(
            booking_id=booking.id,
            payment_method=PaymentMethod.MOMO,
            amount=total_price,
            transaction_id=f"MOMO{random.randint(100000, 999999)}" if p_status == PaymentStatus.SUCCESS else None,
            status=p_status,
            payment_date=datetime.now() if p_status == PaymentStatus.SUCCESS else None
        )
        db.session.add(payment)
        
    db.session.commit()

def seed_other_tables(created_hotels):
    print("Đang tạo dữ liệu cho SystemConfig, OTP, PricePrediction, SearchHistory, PriceHistory...")
    
    # 1. SystemConfig
    configs = [
        SystemConfig(config_key='MAX_ROOMS_PER_BOOKING', config_value='5', description='Số phòng tối đa được đặt trong 1 đơn'),
        SystemConfig(config_key='CANCELLATION_FEE_PERCENTAGE', config_value='10', description='Phần trăm phí phạt nếu hủy phòng sát ngày'),
        SystemConfig(config_key='MAINTENANCE_MODE', config_value='false', description='Bật/tắt chế độ bảo trì toàn hệ thống')
    ]
    db.session.bulk_save_objects(configs)
    
    customers = User.query.filter_by(role=UserRole.CUSTOMER).limit(5).all()
    if customers:
        # 2. OTP & 4. SearchHistory
        for customer in customers:
            otp = OTP(
                user_id=customer.id,
                otp_code=str(random.randint(100000, 999999)),
                expires_at=datetime.now() + timedelta(minutes=5)
            )
            db.session.add(otp)
            
            search = SearchHistory(
                user_id=customer.id,
                search_query=random.choice(["Khách sạn view biển", "Khách sạn trung tâm Sài Gòn", "Resort 5 sao"]),
                location=random.choice(["Hồ Chí Minh", "Vũng Tàu", "Đà Nẵng"])
            )
            db.session.add(search)

    # 3. PricePrediction & 5. PriceHistory
    if created_hotels:
        for hotel in created_hotels[:3]:
            for rt in hotel.room_types:
                pred = PricePrediction(
                    room_type_id=rt.id,
                    target_date=datetime.now().date() + timedelta(days=30),
                    adjustment_percentage=0.15,
                    reason="Mùa du lịch cao điểm"
                )
                db.session.add(pred)
                
                history = PriceHistory(
                    room_type_id=rt.id,
                    old_price=float(rt.base_price) * 0.9,
                    new_price=rt.base_price
                )
                db.session.add(history)
                
    db.session.commit()

def seed_data():
    app = create_app()
    with app.app_context():
        print("Đang xóa dữ liệu cũ và tạo mới Database...")
        db.drop_all()
        db.create_all()

        seed_users()
        created_hotels = seed_hotels_and_tags()
        seed_receptionists(created_hotels)
        seed_rooms(created_hotels)
        seed_bookings_and_payments(created_hotels)
        seed_other_tables(created_hotels)

        print("====== THÀNH CÔNG! ĐÃ SEED DỮ LIỆU HOÀN TẤT ======")

if __name__ == '__main__':
    seed_data()