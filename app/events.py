from flask_socketio import emit, join_room, leave_room
from app.extensions import socketio

@socketio.on('join_payment_room')
def handle_join_payment_room(data):
    order_id = data.get('order_id')
    if order_id:
        join_room(order_id)
        print(f"Client joined payment room: {order_id}")
