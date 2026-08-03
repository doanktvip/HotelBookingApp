from datetime import datetime
from sqlalchemy import func
from app.extensions import db
from app.models import (
    Hotel, RoomType, Room, Tag,
    Booking, BookingDetail, BookingStatus, SearchHistory,
)


class _SimplePagination:

    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = max(1, (total + per_page - 1) // per_page)
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1
        self.next_num = page + 1

    def iter_pages(self, *args, **kwargs):
        for i in range(1, self.pages + 1):
            yield i


class SearchService:

    PER_PAGE = 9

    # ================= 1. TÌM KIẾM THEO BỘ LỌC =================
    def search_by_filter(self, filters, page=1):
        query = (
            RoomType.query
            .join(Hotel, RoomType.hotel_id == Hotel.id)
            .filter(RoomType.is_active == True)
        )

        if filters.get('location'):
            query = query.filter(Hotel.location.ilike(f"%{filters['location']}%"))

        if filters.get('min_price'):
            query = query.filter(RoomType.base_price >= filters['min_price'])

        if filters.get('max_price'):
            query = query.filter(RoomType.base_price <= filters['max_price'])

        if filters.get('capacity'):
            query = query.filter(RoomType.max_occupancy >= filters['capacity'])

        if filters.get('rating_min'):
            query = query.filter(Hotel.rating >= filters['rating_min'])

        for tag_id in filters.get('tag_ids') or []:
            query = query.filter(Hotel.tags.any(Tag.id == tag_id))

        # Lọc theo tình trạng còn phòng trống trong khoảng ngày (nếu có chọn ngày)
        check_in, check_out = filters.get('check_in'), filters.get('check_out')
        ci = co = None
        if check_in and check_out:
            try:
                ci = datetime.strptime(check_in, '%Y-%m-%d').date()
                co = datetime.strptime(check_out, '%Y-%m-%d').date()
            except ValueError:
                ci = co = None

        if ci and co and co > ci:
            overlapping_room_ids = (
                db.session.query(BookingDetail.room_id)
                .join(Booking, Booking.id == BookingDetail.booking_id)
                .filter(
                    Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
                    Booking.check_in < co,
                    Booking.check_out > ci,
                )
            )
            room_available = Room.query.filter(
                Room.room_type_id == RoomType.id,
                Room.is_active == True,
                Room.id.notin_(overlapping_room_ids),
            ).exists()
            query = query.filter(room_available)
        else:
            # Không chọn ngày -> chỉ cần loại phòng có ít nhất 1 phòng vật lý đang hoạt động
            room_exists = Room.query.filter(
                Room.room_type_id == RoomType.id, Room.is_active == True
            ).exists()
            query = query.filter(room_exists)

        sort_by = filters.get('sort_by', 'rating_desc')
        if sort_by == 'price_asc':
            query = query.order_by(RoomType.base_price.asc())
        elif sort_by == 'price_desc':
            query = query.order_by(RoomType.base_price.desc())
        else:
            query = query.order_by(Hotel.rating.desc(), RoomType.base_price.asc())

        return query.paginate(page=page, per_page=self.PER_PAGE, error_out=False)

    # ================= 2. TÌM KIẾM THEO TỪ KHOÁ / NGỮ NGHĨA =================
    def search_by_keyword(self, keyword, page=1, user=None):
        tokens = [t for t in keyword.lower().split() if len(t) > 1]

        known_locations = [row[0] for row in db.session.query(Hotel.location).distinct()]
        matched_location = next(
            (loc for loc in known_locations if loc.lower() in keyword.lower()), None
        )

        # Lưu lại lịch sử tìm kiếm (phục vụ gợi ý thông minh sau này)
        try:
            db.session.add(SearchHistory(
                user_id=user.id if user else None,
                search_query=keyword,
                location=matched_location,
            ))
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Với dữ liệu nhỏ, load hết rồi chấm điểm bằng Python.
        # Nếu dữ liệu lớn hơn, nên chuyển sang MySQL FULLTEXT INDEX hoặc Elasticsearch.
        room_types = (
            RoomType.query.join(Hotel).filter(RoomType.is_active == True).all()
        )

        scored = []
        for rt in room_types:
            haystack = ' '.join(filter(None, [
                rt.hotel.name, rt.hotel.address, rt.hotel.location, rt.hotel.description,
                rt.name, rt.description, rt.bed_type,
                ' '.join(t.name for t in rt.hotel.tags),
            ])).lower()

            score = sum(haystack.count(tok) for tok in tokens)
            if matched_location and matched_location.lower() in rt.hotel.location.lower():
                score += 5

            if score > 0:
                scored.append((score, rt))

        scored.sort(key=lambda pair: (pair[0], pair[1].hotel.rating or 0), reverse=True)
        ranked = [rt for _, rt in scored]

        start = (page - 1) * self.PER_PAGE
        page_items = ranked[start:start + self.PER_PAGE]
        return _SimplePagination(page_items, page, self.PER_PAGE, len(ranked))

    # ================= 3. GỢI Ý KHÁCH SẠN & LOẠI PHÒNG =================
    def get_recommended_hotels(self, user=None, limit=4):
        preferred_location = None
        if user:
            recent = (
                SearchHistory.query
                .filter(SearchHistory.user_id == user.id, SearchHistory.location.isnot(None))
                .order_by(SearchHistory.searched_at.desc())
                .limit(5).all()
            )
            if recent:
                locations = [h.location for h in recent]
                preferred_location = max(set(locations), key=locations.count)

        hotels = []
        if preferred_location:
            hotels = (
                Hotel.query.filter(Hotel.location == preferred_location)
                .order_by(Hotel.rating.desc()).limit(limit).all()
            )

        if len(hotels) < limit:
            for h in Hotel.query.order_by(Hotel.rating.desc()).limit(limit * 2).all():
                if h not in hotels:
                    hotels.append(h)
                if len(hotels) >= limit:
                    break

        return hotels[:limit]

    def get_recommended_room_types(self, limit=4):
        popular = (
            db.session.query(RoomType, func.count(BookingDetail.id).label('cnt'))
            .join(Room, Room.room_type_id == RoomType.id)
            .join(BookingDetail, BookingDetail.room_id == Room.id)
            .filter(RoomType.is_active == True)
            .group_by(RoomType.id)
            .order_by(func.count(BookingDetail.id).desc())
            .limit(limit).all()
        )
        room_types = [rt for rt, _ in popular]

        if len(room_types) < limit:
            fallback = (
                RoomType.query.join(Hotel)
                .filter(RoomType.is_active == True)
                .order_by(Hotel.rating.desc())
                .limit(limit * 2).all()
            )
            for rt in fallback:
                if rt not in room_types:
                    room_types.append(rt)
                if len(room_types) >= limit:
                    break

        return room_types[:limit]

    def get_all_tags(self):
        return Tag.query.order_by(Tag.name).all()
