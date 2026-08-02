document.addEventListener("DOMContentLoaded", function() {
    if (typeof io === 'undefined' || typeof window.HOTEL_ID === 'undefined') {
        return;
    }
    
    const socket = io();
    const hotelId = window.HOTEL_ID;
    
    socket.on('booking_updated', function(data) {
        // Nếu có ai đó vừa đặt phòng ở đúng Khách sạn này
        if (data.hotel_id == hotelId) {        
            // Lấy ngày hiện tại trên form
            const checkInInput = document.getElementById('check_in');
            const checkOutInput = document.getElementById('check_out');
            const checkIn = checkInInput ? checkInInput.value : '';
            const checkOut = checkOutInput ? checkOutInput.value : '';
            
            // Gọi API ngầm để lấy số liệu mới
            fetch(`/api/hotel/${hotelId}/availability?check_in=${checkIn}&check_out=${checkOut}`)
                .then(response => response.json())
                .then(data => {
                    // Cập nhật lại UI cho từng loại phòng
                    for (const [roomTypeId, info] of Object.entries(data)) {
                        const badge = document.getElementById(`room-avail-badge-${roomTypeId}`);
                        const btn = document.getElementById(`room-book-btn-${roomTypeId}`);
                        
                        if (badge) {
                            if (info.available_count > 0) {
                                badge.textContent = `Còn ${info.available_count} trống`;
                                badge.className = "position-absolute";
                                badge.style = "top: 0.75rem; left: 0.75rem; z-index: 2; font-size: 0.75rem; font-weight: 700; padding: 0.25rem 0.75rem; border-radius: 9999px; background-color: #10b981; color: white;";
                            } else {
                                badge.textContent = "Hết phòng";
                                badge.className = "position-absolute";
                                badge.style = "top: 0.75rem; left: 0.75rem; z-index: 2; font-size: 0.75rem; font-weight: 700; padding: 0.25rem 0.75rem; border-radius: 9999px; background-color: #ef4444; color: white;";
                            }
                        }
                        
                        if (btn) {
                            if (info.available_count > 0) {
                                if (btn.tagName === 'BUTTON') {
                                    // Cần đổi thành thẻ A để bấm được
                                    const newBtn = document.createElement('a');
                                    newBtn.id = btn.id;
                                    newBtn.href = `/booking/room-type/${roomTypeId}?check_in=${checkIn}&check_out=${checkOut}`;
                                    newBtn.className = "btn btn-primary rounded-pill px-4 fw-medium shadow-sm";
                                    newBtn.style.border = "none";
                                    newBtn.innerHTML = '<i class="bi bi-plus"></i>Đặt phòng ngay';
                                    btn.parentNode.replaceChild(newBtn, btn);
                                }
                            } else {
                                if (btn.tagName === 'A') {
                                    // Cần đổi thành nút Button bị disabled
                                    const newBtn = document.createElement('button');
                                    newBtn.id = btn.id;
                                    newBtn.className = "btn btn-secondary rounded-pill px-4 fw-medium";
                                    newBtn.disabled = true;
                                    newBtn.textContent = "Đã hết";
                                    btn.parentNode.replaceChild(newBtn, btn);
                                }
                            }
                        }
                    }
                })
                .catch(err => console.error('Error fetching availability:', err));
        }
    });
});
