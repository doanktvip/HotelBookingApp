import os
import csv
import sys
import copy
import random
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import create_app
from app.extensions import db
from app.models import (
    Hotel, RoomType, Floor, Room, User, UserRole, RoomStatus, Tag,
    Booking, BookingDetail, Payment, BookingStatus, PaymentMethod, PaymentStatus,
    SystemConfig, OTP, PricePrediction, SearchHistory, PriceHistory
)

SEED_DATA_DIR = Path(__file__).parent / 'seed_data'

TAGS_DATA = [
    {'name': 'Wifi', 'icon': 'bi-wifi'},
    {'name': 'Bãi biển riêng', 'icon': 'bi-umbrella'},
    {'name': 'Hồ bơi', 'icon': 'bi-water'},
    {'name': 'Spa', 'icon': 'bi-flower1'},
    {'name': 'Gym', 'icon': 'bi-bicycle'},
    {'name': 'Buffet sáng', 'icon': 'bi-cup-hot'},
    {'name': 'Quán Bar', 'icon': 'bi-cup-straw'},
    {'name': 'Lò sưởi', 'icon': 'bi-fire'},
    {'name': 'Buffet tối', 'icon': 'bi-egg-fried'},
    {'name': 'View núi', 'icon': 'bi-image'},
    {'name': 'View biển', 'icon': 'bi-tsunami'},
    {'name': 'Đưa đón sân bay', 'icon': 'bi-airplane'},
    {'name': 'Bãi đậu xe miễn phí', 'icon': 'bi-p-square'},
    {'name': 'Lễ tân 24/7', 'icon': 'bi-person-badge'},
    {'name': 'Cho phép mang thú cưng', 'icon': 'bi-suit-heart'},
    {'name': 'Sân chơi trẻ em', 'icon': 'bi-balloon'},
    {'name': 'Khu vực hút thuốc', 'icon': 'bi-sign-stop'}
]

DEFAULT_ROOM_TYPES_FALLBACK = [
    {"name": "Standard", "desc": "Phòng tiêu chuẩn tiện nghi cơ bản.", "price": 800000.0, "bed_type": "giường đôi", "bed_count": 1, "max_occ": 2},
    {"name": "Superior", "desc": "Phòng chất lượng cao không gian rộng rãi.", "price": 1200000.0, "bed_type": "giường đơn", "bed_count": 2, "max_occ": 2},
    {"name": "Deluxe", "desc": "Phòng sang trọng tầng cao nội thất cao cấp.", "price": 2000000.0, "bed_type": "giường đôi lớn", "bed_count": 1, "max_occ": 2},
    {"name": "Suite", "desc": "Phòng thượng hạng có khu tiếp khách riêng.", "price": 4500000.0, "bed_type": "giường đôi lớn", "bed_count": 2, "max_occ": 4},
    {"name": "Family Room", "desc": "Phòng gia đình rộng rãi cho đoàn khách.", "price": 3500000.0, "bed_type": "giường đôi và đơn", "bed_count": 3, "max_occ": 5}
]

ROOM_TYPE_IMAGES = {
    "Standard": [
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213198/Standard1_afqhsk.webp",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213199/Standard2_wu01wl.webp",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213199/Standard3_zrytbc.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213200/Standard4_wozpkp.jpg"
    ],
    "Superior": [
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213203/Superior1_hpfpfj.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213204/Superior2_bkojp9.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213204/Superior3_wgrh9q.jpg"
    ],
    "Deluxe": [
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213197/Deluxe1_etbfsb.webp",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213197/Deluxe2_h2infy.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213197/Deluxe3_rht7id.webp"
    ],
    "Suite": [
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213201/Suite1_xoxnnx.webp",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213202/Suite2_dwuo8m.jpg",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213202/Suite3_dy2bos.webp"
    ],
    "Family Room": [
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213197/Family_Room1_udwamd.webp",
        "https://res.cloudinary.com/db4bjqp4f/image/upload/v1785213198/Family_Room2_plc68e.webp"
    ]
}


def hash_password(password_str):
    return str(hashlib.md5(password_str.strip().encode('utf-8')).hexdigest())


def safe_seed_tags():
    print("[1/7] Đang nạp danh mục Tiện ích (Tags)...")
    added, updated = 0, 0
    tag_map = {}
    for t_data in TAGS_DATA:
        tag = db.session.query(Tag).filter_by(name=t_data['name']).first()
        if not tag:
            tag = Tag(name=t_data['name'], icon=t_data['icon'])
            db.session.add(tag)
            added += 1
        else:
            if not tag.icon and t_data.get('icon'):
                tag.icon = t_data['icon']
                updated += 1
        tag_map[t_data['name']] = tag
    db.session.commit()
    print(f"  -> Hoàn thành Tags: Thêm mới {added}, Cập nhật {updated}.")
    return list(tag_map.values())


def safe_seed_hotels(all_tags):
    print("[2/7] Đang nạp danh sách Khách sạn từ seed_data/hotels.csv...")
    csv_path = SEED_DATA_DIR / 'hotels.csv'
    if not csv_path.exists():
        print(f"  [!] Không tìm thấy tệp {csv_path}")
        return []

    added, updated = 0, 0
    hotels = []
    with open(csv_path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get('name') or '').strip()
            if not name:
                continue

            rating = float(row.get('rating') or 0.0)
            days = int(row.get('cancellation_policy_days') or 7)
            address = (row.get('address') or '').strip()
            location = (row.get('location') or '').strip()
            description = (row.get('description') or '').strip()
            image_url = (row.get('image_url') or '').strip() or None

            hotel = db.session.query(Hotel).filter_by(name=name).first()
            if not hotel:
                hotel = Hotel(
                    name=name,
                    address=address,
                    location=location,
                    description=description,
                    rating=rating,
                    cancellation_policy_days=days,
                    image_url=image_url
                )
                db.session.add(hotel)
                added += 1
            else:
                hotel.address = address
                hotel.location = location
                hotel.description = description
                hotel.rating = rating
                hotel.cancellation_policy_days = days
                if image_url:
                    hotel.image_url = image_url
                updated += 1

            # Gán ngẫu nhiên 5-7 tiện ích nếu khách sạn chưa có tags
            if not hotel.tags and all_tags:
                num_tags = min(len(all_tags), random.randint(5, 7))
                hotel.tags = random.sample(all_tags, k=num_tags)

            hotels.append(hotel)

    db.session.commit()
    print(f"  -> Hoàn thành Khách sạn: Thêm mới {added}, Cập nhật {updated} (Tổng {len(hotels)} khách sạn).")
    return hotels


def safe_seed_room_types():
    print("[3/7] Đang nạp Loại phòng từ seed_data/room_types.csv...")
    csv_path = SEED_DATA_DIR / 'room_types.csv'
    added, updated = 0, 0

    if csv_path.exists():
        with open(csv_path, encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                hotel_name = (row.get('hotel_name') or '').strip()
                rt_name = (row.get('name') or '').strip()
                if not hotel_name or not rt_name:
                    continue

                hotel = db.session.query(Hotel).filter_by(name=hotel_name).first()
                if not hotel:
                    continue

                desc = (row.get('description') or '').strip()
                price = float(row.get('base_price') or 1000000)
                max_occ = int(row.get('max_occupancy') or 2)
                bed_count = int(row.get('bed_count') or 1)
                bed_type = (row.get('bed_type') or 'giường đôi').strip()
                image_url = (row.get('image_url') or '').strip() or None

                room_type = db.session.query(RoomType).filter_by(hotel_id=hotel.id, name=rt_name).first()
                if not room_type:
                    room_type = RoomType(
                        hotel_id=hotel.id,
                        name=rt_name,
                        description=desc,
                        base_price=price,
                        max_occupancy=max_occ,
                        bed_count=bed_count,
                        bed_type=bed_type,
                        image_url=image_url,
                        is_active=True
                    )
                    db.session.add(room_type)
                    added += 1
                else:
                    room_type.description = desc
                    room_type.base_price = price
                    room_type.max_occupancy = max_occ
                    room_type.bed_count = bed_count
                    room_type.bed_type = bed_type
                    if image_url:
                        room_type.image_url = image_url
                    room_type.is_active = True
                    updated += 1
        db.session.commit()

    # Tự động bổ sung loại phòng cho các khách sạn còn thiếu trong DB
    all_hotels = db.session.query(Hotel).all()
    for hotel in all_hotels:
        existing_types = {rt.name for rt in hotel.room_types}
        if not existing_types:
            for rt_def in DEFAULT_ROOM_TYPES_FALLBACK:
                imgs = ROOM_TYPE_IMAGES.get(rt_def['name'], [])
                chosen_img = random.choice(imgs) if imgs else None
                room_type = RoomType(
                    hotel_id=hotel.id,
                    name=rt_def['name'],
                    description=rt_def['desc'],
                    base_price=rt_def['price'],
                    max_occupancy=rt_def['max_occ'],
                    bed_count=rt_def['bed_count'],
                    bed_type=rt_def['bed_type'],
                    image_url=chosen_img,
                    is_active=True
                )
                db.session.add(room_type)
                added += 1
    db.session.commit()
    print(f"  -> Hoàn thành Loại phòng: Thêm mới {added}, Cập nhật {updated}.")


def safe_seed_floors_and_rooms():
    print("[4/7] Đang nạp Tầng (Floor) và Phòng (Room) từ seed_data/floors_rooms.csv...")
    csv_path = SEED_DATA_DIR / 'floors_rooms.csv'
    added_floors, updated_floors = 0, 0
    added_rooms, updated_rooms = 0, 0

    processed_hotels = set()

    if csv_path.exists():
        with open(csv_path, encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                hotel_name = (row.get('hotel_name') or '').strip()
                floor_num = int(row.get('floor_number') or 1)
                floor_name = (row.get('floor_name') or f'Tầng {floor_num}').strip()
                room_num = (row.get('room_number') or '').strip()
                rt_name = (row.get('room_type_name') or '').strip()
                status_str = (row.get('status') or 'AVAILABLE').strip().upper()
                notes = (row.get('notes') or '').strip() or None

                hotel = db.session.query(Hotel).filter_by(name=hotel_name).first()
                if not hotel:
                    continue

                processed_hotels.add(hotel.id)

                # 1. Tìm hoặc tạo Floor
                floor = db.session.query(Floor).filter_by(hotel_id=hotel.id, floor_number=floor_num).first()
                if not floor:
                    floor = Floor(hotel_id=hotel.id, floor_number=floor_num, name=floor_name)
                    db.session.add(floor)
                    db.session.flush()
                    added_floors += 1
                else:
                    if floor_name and floor.name != floor_name:
                        floor.name = floor_name
                        updated_floors += 1

                # 2. Tìm RoomType tương ứng
                room_type = db.session.query(RoomType).filter_by(hotel_id=hotel.id, name=rt_name).first()
                if not room_type:
                    # Lấy loại phòng đầu tiên nếu không khớp tên
                    room_type = db.session.query(RoomType).filter_by(hotel_id=hotel.id).first()
                    if not room_type:
                        continue

                # 3. Tìm hoặc tạo Room
                room_status = getattr(RoomStatus, status_str, RoomStatus.AVAILABLE)
                room = db.session.query(Room).join(RoomType).filter(
                    RoomType.hotel_id == hotel.id,
                    Room.room_number == room_num
                ).first()

                if not room:
                    room = Room(
                        room_type_id=room_type.id,
                        floor_id=floor.id,
                        floor=floor_num,
                        room_number=room_num,
                        status=room_status,
                        notes=notes,
                        is_active=True
                    )
                    db.session.add(room)
                    added_rooms += 1
                else:
                    room.floor_id = floor.id
                    room.floor = floor_num
                    room.room_type_id = room_type.id
                    room.status = room_status
                    room.notes = notes
                    room.is_active = True
                    updated_rooms += 1

        db.session.commit()

    # Bổ sung tầng và phòng mặc định cho bất kỳ khách sạn nào chưa có trong floors_rooms.csv
    all_hotels = db.session.query(Hotel).all()
    for hotel in all_hotels:
        if hotel.id in processed_hotels:
            continue

        existing_floors = {f.floor_number: f for f in hotel.floors}
        for f_num in [1, 2, 3]:
            if f_num not in existing_floors:
                floor = Floor(hotel_id=hotel.id, floor_number=f_num, name=f"Tầng {f_num}")
                db.session.add(floor)
                db.session.flush()
                existing_floors[f_num] = floor
                added_floors += 1

        existing_rooms = {r.room_number for rt in hotel.room_types for r in rt.rooms}
        if not existing_rooms and hotel.room_types:
            rts = hotel.room_types
            for f_num in [1, 2, 3]:
                floor_obj = existing_floors[f_num]
                for r_idx in range(1, 4):
                    r_num = f"{f_num}{r_idx:02d}"
                    assigned_rt = rts[(f_num + r_idx) % len(rts)]
                    room = Room(
                        room_type_id=assigned_rt.id,
                        floor_id=floor_obj.id,
                        floor=f_num,
                        room_number=r_num,
                        status=RoomStatus.AVAILABLE,
                        notes=f"Phòng {r_num} tiện nghi",
                        is_active=True
                    )
                    db.session.add(room)
                    added_rooms += 1

    db.session.commit()
    print(f"  -> Hoàn thành Tầng: Thêm mới {added_floors}, Cập nhật {updated_floors}.")
    print(f"  -> Hoàn thành Phòng: Thêm mới {added_rooms}, Cập nhật {updated_rooms}.")


def safe_seed_users():
    print("[5/7] Đang nạp Người dùng (Users) từ seed_data/users.csv...")
    csv_path = SEED_DATA_DIR / 'users.csv'
    added, updated = 0, 0

    if csv_path.exists():
        with open(csv_path, encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                username = (row.get('username') or '').strip()
                email = (row.get('email') or '').strip()
                raw_password = (row.get('password') or '123').strip()
                role_str = (row.get('role') or 'CUSTOMER').strip().upper()
                hotel_name = (row.get('hotel_name') or '').strip()
                is_verified = (row.get('is_verified') or 'True').strip().lower() == 'true'
                phone = (row.get('phone') or '').strip() or None

                if not username or not email:
                    continue

                role = getattr(UserRole, role_str, UserRole.CUSTOMER)
                hotel_id = None
                if hotel_name:
                    hotel = db.session.query(Hotel).filter_by(name=hotel_name).first()
                    if hotel:
                        hotel_id = hotel.id

                user = db.session.query(User).filter(
                    (User.username == username) | (User.email == email)
                ).first()

                if not user:
                    user = User(
                        username=username,
                        email=email,
                        password=hash_password(raw_password),
                        role=role,
                        is_verified=is_verified,
                        phone=phone,
                        hotel_id=hotel_id
                    )
                    db.session.add(user)
                    added += 1
                else:
                    user.username = username
                    user.email = email
                    user.role = role
                    user.is_verified = is_verified
                    if phone:
                        user.phone = phone
                    if hotel_id is not None:
                        user.hotel_id = hotel_id
                    updated += 1
        db.session.commit()

    # Đảm bảo có ít nhất 1 Admin và Lễ tân cho từng khách sạn
    admin_user = db.session.query(User).filter_by(role=UserRole.ADMIN).first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@hotel.com',
            password=hash_password('123'),
            role=UserRole.ADMIN,
            is_verified=True,
            phone='0901234567'
        )
        db.session.add(admin_user)
        added += 1

    # Đảm bảo 2 khách sạn đầu tiên đều có lễ tân được gắn đúng hotel_id
    hotels = db.session.query(Hotel).limit(2).all()
    for idx, hotel in enumerate(hotels, start=1):
        recept_username = f"letan_ks{idx}"
        recept_email = f"letan{idx}@hotel.com"
        recept = db.session.query(User).filter(
            (User.username == recept_username) | (User.email == recept_email)
        ).first()
        if not recept:
            recept = User(
                username=recept_username,
                email=recept_email,
                password=hash_password('123'),
                role=UserRole.RECEPTIONIST,
                is_verified=True,
                phone=f"090234567{idx}",
                hotel_id=hotel.id
            )
            db.session.add(recept)
            added += 1
        else:
            recept.username = recept_username
            recept.hotel_id = hotel.id
            recept.role = UserRole.RECEPTIONIST
            updated += 1

    db.session.commit()
    print(f"  -> Hoàn thành Người dùng: Thêm mới {added}, Cập nhật {updated}.")


def safe_seed_system_configs():
    print("[6/7] Đang nạp Cấu hình hệ thống (SystemConfig)...")
    configs = [
        ('MAX_ROOMS_PER_BOOKING', '5', 'Số phòng tối đa được đặt trong 1 đơn'),
        ('CANCELLATION_FEE_PERCENTAGE', '10', 'Phần trăm phí phạt nếu hủy phòng sát ngày'),
        ('MAINTENANCE_MODE', 'false', 'Bật/tắt chế độ bảo trì toàn hệ thống'),
        ('MAXIMUM_PASSWORD_LENGHT', '20', 'Độ dài tối đa của mật khẩu'),
        ('MINIMUM_PASSWORD_LENGTH', '6', 'Độ dài tối thiếu của mật khẩu'),
        ('DEFAULT_PER_PAGE', '12', 'Số lượng mục hiển thị mặc định trên mỗi trang'),
        ('CHECK_IN_TIME', '14:00', 'Thời gian nhận phòng mặc định (HH:MM)'),
        ('CHECK_OUT_TIME', '12:00', 'Thời gian trả phòng mặc định (HH:MM)'),
        ('HOTLINE_NUMBER', '19001508', 'Số điện thoại hotline hỗ trợ khách hàng'),
        ('OTP_EXPIRATION_MINUTES', '5', 'Thời gian tồn tại của mã OTP (phút)'),
        ('TAX_FEE_PERCENTAGE', '0', 'Phần trăm thuế/phí áp dụng cho đơn đặt phòng'),
        ('AI_PREDICTION_INTERVAL', '7', 'Số ngày dự báo giá tự động'),
        ('MAX_PRICE_ADJUSTMENT_PERCENTAGE', '20', 'Phần trăm tăng giá tối đa')
    ]

    added, updated = 0, 0
    for key, val, desc in configs:
        cfg = db.session.query(SystemConfig).filter_by(config_key=key).first()
        if not cfg:
            cfg = SystemConfig(config_key=key, config_value=val, description=desc)
            db.session.add(cfg)
            added += 1
        else:
            if not cfg.description:
                cfg.description = desc
                updated += 1
    db.session.commit()
    print(f"  -> Hoàn thành SystemConfig: Thêm mới {added}, Cập nhật {updated}.")


def safe_seed_search_histories_and_sample_data():
    print("[7/7] Đang nạp Lịch sử Tìm kiếm mẫu & Dự báo giá...")
    customer = db.session.query(User).filter_by(role=UserRole.CUSTOMER).first()
    user_id = customer.id if customer else None

    # Mẫu lịch sử tìm kiếm đa dạng
    sample_searches = [
        {
            "user_id": user_id,
            "keyword": "Wyndham Legend Halong",
            "location": "Hạ Long",
            "check_in_date": datetime.now().date() + timedelta(days=5),
            "check_out_date": datetime.now().date() + timedelta(days=7),
            "guest_count": 2,
            "room_count": 1,
            "search_query": "Wyndham Legend Halong Hạ Long",
            "is_useful": True
        },
        {
            "user_id": user_id,
            "keyword": "Khách sạn hướng biển có hồ bơi",
            "location": "Hạ Long",
            "check_in_date": datetime.now().date() + timedelta(days=12),
            "check_out_date": datetime.now().date() + timedelta(days=15),
            "guest_count": 4,
            "room_count": 2,
            "search_query": "Khách sạn hướng biển có hồ bơi Hạ Long",
            "is_useful": True
        },
        {
            "user_id": None,  # Khách vãng lai
            "session_id": "guest_session_demo_12345",
            "ip_address": "127.0.0.1",
            "keyword": "FLC Grand Hotel Hạ Long",
            "location": "Hạ Long",
            "check_in_date": datetime.now().date() + timedelta(days=20),
            "check_out_date": datetime.now().date() + timedelta(days=22),
            "guest_count": 2,
            "room_count": 1,
            "search_query": "FLC Grand Hotel Hạ Long",
            "is_useful": True
        }
    ]

    added = 0
    for s_data in sample_searches:
        existing = db.session.query(SearchHistory).filter_by(
            user_id=s_data.get('user_id'),
            keyword=s_data.get('keyword'),
            location=s_data.get('location')
        ).first()

        if not existing:
            sh = SearchHistory(
                user_id=s_data.get('user_id'),
                session_id=s_data.get('session_id'),
                ip_address=s_data.get('ip_address'),
                keyword=s_data.get('keyword'),
                location=s_data.get('location'),
                check_in_date=s_data.get('check_in_date'),
                check_out_date=s_data.get('check_out_date'),
                guest_count=s_data.get('guest_count', 1),
                room_count=s_data.get('room_count', 1),
                search_query=s_data.get('search_query'),
                is_useful=s_data.get('is_useful', True)
            )
            db.session.add(sh)
            added += 1

    # Tạo giá dự báo mẫu cho các khách sạn
    first_hotel = db.session.query(Hotel).first()
    if first_hotel:
        existing_pred = db.session.query(PricePrediction).filter_by(hotel_id=first_hotel.id).first()
        if not existing_pred:
            pred = PricePrediction(
                hotel_id=first_hotel.id,
                target_date=datetime.now().date() + timedelta(days=30),
                adjustment_percentage=0.15,
                reason="Mùa du lịch cao điểm",
                is_applied=True
            )
            db.session.add(pred)

    db.session.commit()
    print(f"  -> Hoàn thành Lịch sử Tìm kiếm mẫu: Thêm mới {added}.")


def ensure_schema_upgrades():
    from sqlalchemy import text, inspect
    inspector = inspect(db.engine)
    
    # Kiểm tra cột floor_id trong bảng rooms
    if 'rooms' in inspector.get_table_names():
        room_cols = [c['name'] for c in inspector.get_columns('rooms')]
        if 'floor_id' not in room_cols:
            print("  [*] Tự động bổ sung cột 'floor_id' vào bảng 'rooms'...")
            try:
                db.session.execute(text("ALTER TABLE rooms ADD COLUMN floor_id INT NULL"))
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"      [Lưu ý khi thêm floor_id]: {e}")

    # Kiểm tra các cột mở rộng trong bảng search_histories
    if 'search_histories' in inspector.get_table_names():
        sh_cols = [c['name'] for c in inspector.get_columns('search_histories')]
        cols_to_add = [
            ('session_id', 'VARCHAR(100) NULL'),
            ('ip_address', 'VARCHAR(50) NULL'),
            ('keyword', 'VARCHAR(255) NULL'),
            ('location', 'VARCHAR(100) NULL'),
            ('check_in_date', 'DATE NULL'),
            ('check_out_date', 'DATE NULL'),
            ('guest_count', 'INT DEFAULT 1'),
            ('room_count', 'INT DEFAULT 1'),
            ('created_at', 'DATETIME NULL'),
        ]
        for col_name, col_type in cols_to_add:
            if col_name not in sh_cols:
                try:
                    db.session.execute(text(f"ALTER TABLE search_histories ADD COLUMN {col_name} {col_type}"))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        try:
            db.session.execute(text("UPDATE search_histories SET created_at = searched_at WHERE created_at IS NULL AND searched_at IS NOT NULL"))
            db.session.commit()
        except Exception:
            db.session.rollback()


def run_seed(reset_db=False):
    app = create_app()
    with app.app_context():
        print("=" * 60)
        if reset_db:
            print("[CẢNH BÁO] Chế độ --reset: Đang xóa sạch và khởi tạo lại Database...")
            db.drop_all()
            db.create_all()
            print("  -> Khởi tạo lại bảng thành công.")
        else:
            print("[SAFE MODE] Đang đảm bảo cấu trúc bảng và nạp dữ liệu an toàn...")
            db.create_all()
            ensure_schema_upgrades()

        all_tags = safe_seed_tags()
        safe_seed_hotels(all_tags)
        safe_seed_room_types()
        safe_seed_floors_and_rooms()
        safe_seed_users()
        safe_seed_system_configs()
        safe_seed_search_histories_and_sample_data()

        print("=" * 60)
        print("====== NẠP DỮ LIỆU THÀNH CÔNG (IDEMPOTENT / AN TOÀN) ======")


if __name__ == '__main__':
    reset = '--reset' in sys.argv
    run_seed(reset_db=reset)