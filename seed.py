import os
import random
from app import create_app
from app.extensions import db
from app.models import Hotel, RoomType, Room, User, UserRole, RoomStatus
from werkzeug.security import generate_password_hash


def seed_data():
    app = create_app()

    # Ép Flask chạy trong App Context để thao tác được với Database
    with app.app_context():
        print("Đang xóa dữ liệu cũ và tạo mới Database...")
        db.drop_all()
        db.create_all()

        print("Đang tạo User Admin và Khách hàng...")
        admin = User(
            username="admin",
            email="admin@hotel.com",
            password=generate_password_hash("123456"),
            role=UserRole.ADMIN,
            is_verified=True,
        )
        customer = User(
            username="khachhang",
            email="khach@hotel.com",
            password=generate_password_hash("123456"),
            role=UserRole.CUSTOMER,
            is_verified=True,
        )
        db.session.add_all([admin, customer])

        print("Đang tạo thông tin Khách sạn...")
        hotels_data = [
            {
                "name": "Khách Sạn Mường Thanh Luxury",
                "address": "123 Đường Bờ Biển, Nha Trang",
                "location": "Nha Trang",
                "description": "Khách sạn 5 sao đạt chuẩn quốc tế với view biển tuyệt đẹp.",
                "rating": 5.0,
                "amenities": "Wifi, Hồ bơi, Spa, Gym, Buffet sáng",
            },
            {
                "name": "Vinpearl Resort & Spa",
                "address": "Đảo Hòn Tre, Nha Trang",
                "location": "Nha Trang",
                "description": "Khu nghỉ dưỡng lý tưởng dành cho gia đình với công viên nước và biển riêng lãng mạn.",
                "rating": 4.9,
                "amenities": "Wifi, Hồ bơi, Bãi biển riêng, Công viên nước",
            },
            {
                "name": "InterContinental Saigon",
                "address": "Góc đường Hai Bà Trưng, Quận 1, TP HCM",
                "location": "Hồ Chí Minh",
                "description": "Khách sạn sang trọng nằm ở trung tâm thành phố, tuyệt vời cho các chuyến công tác.",
                "rating": 4.7,
                "amenities": "Wifi, Gym, Buffet sáng, Quán Bar",
            },
            {
                "name": "Sapa Horizon Hotel",
                "address": "097 Phạm Xuân Huân, Sapa",
                "location": "Sapa",
                "description": "Tận hưởng không khí se lạnh với view thung lũng mây mờ ảo cực kỳ lãng mạn.",
                "rating": 4.6,
                "amenities": "Wifi, Lò sưởi, Ban công view núi, Thuê xe",
            },
            {
                "name": "Melia Danang Beach Resort",
                "address": "Bãi biển Non Nước, Đà Nẵng",
                "location": "Đà Nẵng",
                "description": "Resort yên bình lãng mạn cạnh bãi biển, rất thích hợp cho kỳ nghỉ tuần trăng mật của cặp đôi.",
                "rating": 4.8,
                "amenities": "Wifi, Hồ bơi, Spa, Bãi biển riêng",
            }
        ]

        created_hotels = []
        for h_data in hotels_data:
            hotel = Hotel(**h_data)
            db.session.add(hotel)
            created_hotels.append(hotel)
        db.session.commit()

        print("Đang chuẩn bị Các Loại Phòng (RoomType) và tải hình ảnh đẹp...")
        room_types_data = [
            {
                "name": "Phòng Standard",
                "desc": "Phòng tiêu chuẩn dành cho 2 người, đầy đủ tiện nghi cơ bản.",
                "price": 800000.0,
                "max": 2,
                "amenities": "Wifi, Tivi, Điều hòa",
                "image": "https://images.unsplash.com/photo-1518733057094-95b53143d2a7?auto=format&fit=crop&w=800&q=80",
            },
            {
                "name": "Phòng Superior Sea View",
                "desc": "Phòng cao cấp hướng biển, đón bình minh tuyệt đẹp mỗi sáng.",
                "price": 1200000.0,
                "max": 2,
                "amenities": "Wifi, Tivi, Điều hòa, Bồn tắm, Ban công",
                "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80",
            },
            {
                "name": "Phòng Deluxe Family",
                "desc": "Phòng gia đình rộng rãi, không gian sinh hoạt chung thoải mái.",
                "price": 2000000.0,
                "max": 4,
                "amenities": "Wifi, Tivi 4K, Tủ lạnh lớn, Bồn tắm, Ban công",
                "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80",
            },
            {
                "name": "Presidential Suite VIP",
                "desc": "Phòng Tổng thống đẳng cấp sang trọng bậc nhất dành cho giới thượng lưu.",
                "price": 5500000.0,
                "max": 2,
                "amenities": "Wifi, Tivi 8K, Quầy Bar mini, Bồn tắm sục Jacuzzi",
                "image": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80",
            },
            {
                "name": "Bungalow Trên Biển",
                "desc": "Nhà gỗ trên biển mang lại cảm giác hòa mình vào thiên nhiên hoang sơ.",
                "price": 3500000.0,
                "max": 2,
                "amenities": "Hồ bơi riêng, Võng lưới, Vòi sen lộ thiên",
                "image": "https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?auto=format&fit=crop&w=800&q=80",
            },
            {
                "name": "Phòng Executive City View",
                "desc": "Phòng doanh nhân cao cấp nhìn ra toàn cảnh thành phố sầm uất về đêm.",
                "price": 1500000.0,
                "max": 2,
                "amenities": "Bàn làm việc lớn, Tivi, Máy pha cafe",
                "image": "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=800&q=80",
            },
            {
                "name": "Villa 3 Phòng Ngủ",
                "desc": "Biệt thự độc lập tuyệt đẹp với 3 phòng ngủ và khu vườn sinh thái.",
                "price": 8000000.0,
                "max": 6,
                "amenities": "Hồ bơi lớn, Sân BBQ, Nhà bếp đầy đủ",
                "image": "https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&w=800&q=80",
            },
            {
                "name": "Phòng Giường Đôi Mái Vòm",
                "desc": "Phòng mang kiến trúc độc đáo lãng mạn đặc biệt dành cho các cặp đôi.",
                "price": 2500000.0,
                "max": 2,
                "amenities": "Giường tròn, Đèn led nghệ thuật, Rượu vang",
                "image": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80",
            },
        ]

        print("Đang tạo Loại phòng và Căn phòng vật lý cho từng Khách sạn...")
        for hotel in created_hotels:
            # Chọn ngẫu nhiên 3-5 loại phòng cho mỗi khách sạn
            num_rt = random.randint(3, 5)
            selected_rts = random.sample(room_types_data, k=num_rt)
            
            created_room_types = []
            for rt in selected_rts:
                room_type = RoomType(
                    hotel_id=hotel.id,
                    name=rt["name"],
                    description=rt["desc"],
                    base_price=rt["price"],
                    max_occupancy=rt["max"],
                    amenities=rt["amenities"],
                    image_url=rt["image"],
                )
                db.session.add(room_type)
                created_room_types.append(room_type)
            db.session.commit()

            # Tạo 15 phòng vật lý cho khách sạn này
            for i in range(1, 16):
                rt = random.choice(created_room_types)
                room = Room(
                    room_type_id=rt.id,
                    hotel_id=hotel.id,
                    room_number=f"{random.randint(1, 9)}0{i % 10}",
                    status=RoomStatus.AVAILABLE,
                )
                db.session.add(room)
        
        db.session.commit()
        print("====== THÀNH CÔNG! ĐÃ SEED DỮ LIỆU HOÀN TẤT ======")


if __name__ == '__main__':
    seed_data()
