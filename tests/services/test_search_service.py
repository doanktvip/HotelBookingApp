import pytest
from unittest.mock import patch
from app.services.search_service import SearchService
from app.models import SearchHistory

@pytest.fixture
def search_service(test_session):
    return SearchService(db_session=test_session)

@patch('app.services.search_service.AIService.parse_search_query')
def test_semantic_search_success(mock_parse, test_app, search_service, sample_hotel, sample_customer):
    mock_parse.return_value = {
        "name": sample_hotel.name,
        "location": sample_hotel.location,
        "min_price": None,
        "max_price": None,
        "min_rating": None,
        "capacity": None,
        "bed_count": None,
        "check_in": None,
        "check_out": None,
        "tag_ids": [],
        "sort_by": None
    }
    
    with test_app.test_request_context():
        # Gọi tìm kiếm
        keyword = "Tìm khách sạn Nha Trang"
        pagination = search_service.semantic_search(keyword=keyword, user=sample_customer)
        
        # Kiểm tra kết quả có chứa sample_hotel không
        assert pagination is not None
        assert pagination.total > 0
        assert pagination.items[0].id == sample_hotel.id
        
        # Kiểm tra xem hệ thống đã lưu Lịch sử tìm kiếm vào DB chưa
        history = search_service.db.query(SearchHistory).filter_by(search_query=keyword).first()
        assert history is not None
        assert history.user_id == sample_customer.id
        assert history.is_useful is True

@patch('app.services.search_service.AIService.parse_search_query')
def test_semantic_search_no_useful_data(mock_parse, test_app, search_service):
    # Mock AI không tìm thấy dữ liệu lọc nào
    mock_parse.return_value = {
        "name": None, "location": None, "min_price": None, "max_price": None,
        "min_rating": None, "capacity": None, "bed_count": None, 
        "check_in": None, "check_out": None, "tag_ids": [], "sort_by": None
    }
    
    with test_app.test_request_context():
        keyword = "Xin chào bạn khoẻ không"
        result = search_service.semantic_search(keyword=keyword)
        
        # Nếu vô nghĩa thì phải trả về None thay vì tìm kiếm
        assert result is None
        
        # Kiểm tra lịch sử vẫn được lưu nhưng is_useful = False
        history = search_service.db.query(SearchHistory).filter_by(search_query=keyword).first()
        assert history is not None
        assert history.is_useful is False

def test_save_search_history_duplicate(search_service, sample_customer):
    keyword = "khách sạn giá rẻ"
    
    # Lưu lần 1
    search_service.save_search_history(keyword, {"price": 100}, True, sample_customer.id)
    count1 = search_service.db.query(SearchHistory).filter_by(search_query=keyword).count()
    assert count1 == 1
    
    # Lưu lần 2 y hệt
    search_service.save_search_history(keyword, {"price": 100}, True, sample_customer.id)
    count2 = search_service.db.query(SearchHistory).filter_by(search_query=keyword).count()
    
    # Số lượng record vẫn phải là 1 (không tạo thêm)
    assert count2 == 1

def test_search_booking_in_recept(test_app, search_service, sample_hotel, sample_customer, sample_booking, sample_booking_details):
    with test_app.test_request_context():
        search_id = f"BK-{sample_booking.id}"
        pagination1 = search_service.search_booking_in_recept(sample_hotel.id, search_id)
        assert pagination1.total == 1
        assert pagination1.items[0].id == sample_booking.id
        
        # 2. Tìm theo Tên Khách Hàng
        pagination2 = search_service.search_booking_in_recept(sample_hotel.id, sample_customer.username)
        assert pagination2.total >= 1
        
        # 3. Tìm theo SĐT Khách Hàng
        pagination3 = search_service.search_booking_in_recept(sample_hotel.id, sample_customer.phone)
        assert pagination3.total >= 1
        
        # 4. Tìm tào lao (sẽ ra 0)
        pagination4 = search_service.search_booking_in_recept(sample_hotel.id, "NOBODYHERE")
        assert pagination4.total == 0


# --- Merged from test_search_history.py ---

import pytest
from datetime import datetime, date, timedelta
from app.models import Hotel, RoomType, Floor, Room, User, UserRole, RoomStatus, SearchHistory
from app.extensions import db


def test_floor_and_room_relationship(test_session):
    """Kiểm tra tạo Tầng (Floor) và quan hệ Foreign Key với Hotel và Room"""
    hotel = Hotel(name="Test Hotel FK", address="123 Test St", location="Hà Nội", rating=4.5)
    test_session.add(hotel)
    test_session.commit()

    floor1 = Floor(hotel_id=hotel.id, floor_number=1, name="Tầng 1")
    floor2 = Floor(hotel_id=hotel.id, floor_number=2, name="Tầng 2")
    test_session.add_all([floor1, floor2])
    test_session.commit()

    room_type = RoomType(
        hotel_id=hotel.id,
        name="Deluxe",
        description="Phòng Deluxe",
        base_price=1500000.0,
        max_occupancy=2,
        bed_count=1,
        bed_type="giường đôi"
    )
    test_session.add(room_type)
    test_session.commit()

    room = Room(
        room_type_id=room_type.id,
        floor_id=floor1.id,
        floor=1,
        room_number="101",
        status=RoomStatus.AVAILABLE
    )
    test_session.add(room)
    test_session.commit()

    # Kiểm tra liên kết
    assert len(hotel.floors) >= 2
    assert room.floor_obj.id == floor1.id
    assert room.floor_obj.name == "Tầng 1"
    assert room.room_type.hotel_id == hotel.id
    assert room in floor1.rooms


def test_search_history_model_fields(test_session):
    """Kiểm tra đầy đủ các trường yêu cầu của model SearchHistory"""
    today = date.today()
    co_date = today + timedelta(days=3)

    history = SearchHistory(
        user_id=None,
        session_id="test_guest_session_123",
        ip_address="127.0.0.1",
        keyword="Khách sạn Hạ Long",
        location="Hạ Long",
        check_in_date=today,
        check_out_date=co_date,
        guest_count=2,
        room_count=1,
        is_useful=True
    )
    test_session.add(history)
    test_session.commit()

    assert history.id is not None
    assert history.session_id == "test_guest_session_123"
    assert history.keyword == "Khách sạn Hạ Long"
    assert history.location == "Hạ Long"
    assert history.check_in_date == today
    assert history.check_out_date == co_date
    assert history.guest_count == 2
    assert history.room_count == 1
    assert history.created_at is not None
    assert "Hạ Long" in history.display_text


def test_auto_record_search_and_view(client, test_session):
    """Kiểm tra tự động ghi nhận SearchHistory khi người dùng tìm kiếm và hiển thị ở /search-history"""
    # 1. Thực hiện tìm kiếm
    res = client.get('/hotels?location=Vũng+Tàu&check_in=2026-11-01&check_out=2026-11-03&guest_count=3&room_count=2')
    assert res.status_code == 200

    # 2. Kiểm tra bản ghi trong DB
    history = test_session.query(SearchHistory).filter_by(location="Vũng Tàu").first()
    assert history is not None
    assert history.guest_count == 3
    assert history.room_count == 2

    # 3. Truy cập trang /search-history
    res_view = client.get('/search-history')
    assert res_view.status_code == 200
    assert b"L\xc3\xadch s\xe1\xbb\xad t\xc3\xacm ki\xe1\xba\xbfm" in res_view.data or b"V\xc5\xa9ng T\xc3\xa0u" in res_view.data


def test_re_search_redirect(client, test_session):
    """Kiểm tra chức năng Tìm lại (Re-search) redirect đúng tham số"""
    history = SearchHistory(
        keyword="Novotel",
        location="Đà Nẵng",
        check_in_date=date(2026, 12, 10),
        check_out_date=date(2026, 12, 15),
        guest_count=2,
        room_count=1
    )
    test_session.add(history)
    test_session.commit()

    res = client.get(f'/search-history/{history.id}/re-search')
    assert res.status_code == 302
    assert 'hotels' in res.location
    assert 'keyword=Novotel' in res.location
    assert 'location=' in res.location
    assert 'check_in=2026-12-10' in res.location
    assert 'check_out=2026-12-15' in res.location


def test_delete_search_history_item(client, test_session):
    """Kiểm tra xóa từng mục lịch sử tìm kiếm"""
    with client.session_transaction() as sess:
        sess['guest_id'] = 'session_del_test'

    history = SearchHistory(
        session_id='session_del_test',
        keyword='Delete Test',
        location='Hà Nội'
    )
    test_session.add(history)
    test_session.commit()
    hid = history.id

    # Gửi yêu cầu xóa POST
    res = client.post(f'/search-history/{hid}/delete')
    assert res.status_code == 302

    deleted_item = test_session.get(SearchHistory, hid)
    assert deleted_item is None


def test_clear_all_search_history(client, test_session):
    """Kiểm tra xóa toàn bộ lịch sử của người dùng"""
    with client.session_transaction() as sess:
        sess['guest_id'] = 'session_clear_all'

    h1 = SearchHistory(session_id='session_clear_all', keyword='Test 1')
    h2 = SearchHistory(session_id='session_clear_all', keyword='Test 2')
    test_session.add_all([h1, h2])
    test_session.commit()

    res = client.post('/search-history/clear')
    assert res.status_code == 302

    count = test_session.query(SearchHistory).filter_by(session_id='session_clear_all').count()
    assert count == 0


def test_receptionist_and_admin_permissions(client, test_session):
    """Kiểm tra phân quyền: Lễ tân chỉ quản lý khách sạn được gắn, Admin có toàn quyền"""
    import hashlib
    import uuid
    uid = uuid.uuid4().hex[:6]

    # 1. Tạo 2 khách sạn
    h1 = Hotel(name=f"Hotel Perm A {uid}", address="123 A", location="HN", rating=4.0)
    h2 = Hotel(name=f"Hotel Perm B {uid}", address="456 B", location="HCM", rating=4.0)
    test_session.add_all([h1, h2])
    test_session.commit()

    # 2. Tạo tầng và phòng cho từng khách sạn
    f1 = Floor(hotel_id=h1.id, floor_number=1, name="Tầng 1 - H1")
    f2 = Floor(hotel_id=h2.id, floor_number=1, name="Tầng 1 - H2")
    test_session.add_all([f1, f2])
    test_session.commit()

    rt1 = RoomType(hotel_id=h1.id, name=f"Type Perm 1 {uid}", base_price=1000000, is_active=True)
    rt2 = RoomType(hotel_id=h2.id, name=f"Type Perm 2 {uid}", base_price=2000000, is_active=True)
    test_session.add_all([rt1, rt2])
    test_session.commit()

    r1_num = f"101_{uid}"
    r2_num = f"201_{uid}"
    r1 = Room(room_type_id=rt1.id, floor_id=f1.id, floor=1, room_number=r1_num, is_active=True)
    r2 = Room(room_type_id=rt2.id, floor_id=f2.id, floor=1, room_number=r2_num, is_active=True)
    test_session.add_all([r1, r2])
    test_session.commit()

    # 3. Tạo tài khoản Lễ tân gắn với h1, Admin và Khách hàng
    pw_hash = hashlib.md5("123".encode('utf-8')).hexdigest()
    recept_username = f"recept_{uid}"
    recept = User(
        username=recept_username,
        email=f"recept_{uid}@hotel.com",
        password=pw_hash,
        role=UserRole.RECEPTIONIST,
        is_verified=True,
        hotel_id=h1.id
    )
    admin_username = f"admin_{uid}"
    admin = User(
        username=admin_username,
        email=f"admin_{uid}@hotel.com",
        password=pw_hash,
        role=UserRole.ADMIN,
        is_verified=True
    )
    cust_username = f"cust_{uid}"
    customer = User(
        username=cust_username,
        email=f"cust_{uid}@hotel.com",
        password=pw_hash,
        role=UserRole.CUSTOMER,
        is_verified=True
    )
    test_session.add_all([recept, admin, customer])
    test_session.commit()

    # 4. Khách hàng truy cập /recept -> 403 Forbidden
    client.post('/login', data={'username': cust_username, 'password': '123'})
    res_cust = client.get('/recept')
    assert res_cust.status_code == 403
    client.get('/logout')

    # 5. Lễ tân h1 truy cập /recept -> 200 OK, thấy phòng r1_num của h1 nhưng không thấy r2_num của h2
    client.post('/login', data={'username': recept_username, 'password': '123'})
    res_rec = client.get('/recept')
    assert res_rec.status_code == 200
    assert r1_num.encode() in res_rec.data
    assert r2_num.encode() not in res_rec.data
    client.get('/logout')

    # 6. Admin truy cập trang quản trị -> 200 OK
    client.post('/login', data={'username': admin_username, 'password': '123'})
    res_adm = client.get('/predictions')
    assert res_adm.status_code == 200
    client.get('/logout')

