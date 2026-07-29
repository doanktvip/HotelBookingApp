# HotelBookingApp

Dự án Web ứng dụng Đặt phòng Khách sạn được xây dựng bằng Python Flask sử dụng kiến trúc **Application Factory Pattern** kết hợp với **Blueprints** và cơ sở dữ liệu **MySQL**.

## Cấu trúc thư mục dự án

```text
HotelBookingApp/
├── app/                        # Thư mục chính của ứng dụng
│   ├── __init__.py             # Cấu hình Application Factory
│   ├── extensions.py           # Khởi tạo db, migrate, login_manager
│   ├── models.py               # Toàn bộ database models liên kết nhau (User, Hotel, Room, Booking)
│   ├── services/               # Tầng xử lý logic nghiệp vụ & truy vấn Database (Service Layer)
│   │   └── __init__.py
│   ├── routes/                 # Thư mục chứa các phân hệ routes (Đón request & điều hướng)
│   │   ├── __init__.py
│   │   └── main.py             # Route trang chủ cơ bản
│   ├── static/                 # Tài nguyên tĩnh CSS, JS, hình ảnh
│   └── templates/              # Thư mục chứa giao diện Jinja2 HTML
├── tests/                      # Thư mục chứa các file kiểm thử tự động
├── config.py                   # Cấu hình môi trường chạy (Dev, Test, Prod)
├── requirements.txt            # Thư viện Python cần cài đặt
├── .env                        # Biến môi trường mẫu cấu hình DB
└── run.py                      # Điểm chạy chính của dự án
```

## Kiến trúc ứng dụng (Architecture)

Ứng dụng được thiết kế theo mô hình tách biệt trách nhiệm để dự án dễ bảo trì và phát triển lâu dài:
- **Tầng Định tuyến / Routing Layer (`app/routes/`)**: Định nghĩa các đường dẫn URL (Endpoints). Nhiệm vụ chính của tầng này là đón nhận request từ người dùng, đọc dữ liệu đầu vào (Form, JSON) và điều hướng (render template hoặc redirect).
- **Tầng Nghiệp vụ / Service Layer (`app/services/`)**: Nơi thực hiện toàn bộ logic xử lý nghiệp vụ, kiểm tra ràng buộc và trực tiếp truy vấn cơ sở dữ liệu. Tầng định tuyến sẽ gọi xuống tầng này để lấy hoặc xử lý dữ liệu.
- **Tầng Dữ liệu / Models (`app/models.py`)**: Nơi định nghĩa các bảng và mối quan hệ (ORM) bằng SQLAlchemy.


## Hướng dẫn cài đặt và khởi chạy

1. **Khởi tạo môi trường ảo (Virtual Environment)**:
   ```bash
   python -m venv venv
   ```

2. **Kích hoạt venv và cài đặt thư viện**:
   ```bash
   # Windows (PowerShell / Command Prompt)
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Cập nhật thông số kết nối Database**:
   Mở file `.env` và sửa các thông số của MySQL (`DB_USER`, `DB_PASSWORD`, `DB_NAME`) cho phù hợp với máy của bạn.

4. **Khởi động ứng dụng**:
   ```bash
   python run.py
   ```
   Sau đó mở trình duyệt truy cập `http://127.0.0.1:5000`.