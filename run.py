from app import create_app
from app.extensions import socketio

# Khởi tạo ứng dụng thông qua Application Factory
app = create_app()

if __name__ == '__main__':
    # Khởi chạy server phát triển với SocketIO
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
