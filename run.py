from app import create_app

# Khởi tạo ứng dụng thông qua Application Factory
app = create_app()

if __name__ == '__main__':
    # Khởi chạy server phát triển
    app.run()
