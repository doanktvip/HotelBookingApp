document.addEventListener('DOMContentLoaded', function() {
    var socket = io();
    
    // Đảm bảo biến toàn cục ORDER_ID và MOMO_RETURN_URL đã được khai báo ở file HTML
    if (typeof ORDER_ID === 'undefined' || typeof MOMO_RETURN_URL === 'undefined') {
        console.error("Missing global variables ORDER_ID or MOMO_RETURN_URL");
        return;
    }
    
    socket.on('connect', function() {
        socket.emit('join_payment_room', { order_id: ORDER_ID });
    });
    
    socket.on('payment_success', function(data) {
        // Hiện overlay màu xanh loading
        var overlay = document.getElementById('qr-loading-overlay');
        if (overlay) {
            overlay.classList.remove('d-none');
        }
        
        // Chờ 2 giây rồi chuyển trang
        setTimeout(function() {
            var redirectUrl = MOMO_RETURN_URL + "?resultCode=0";
            if (data && data.order_id) {
                redirectUrl += "&orderId=" + data.order_id;
            }
            window.location.href = redirectUrl;
        }, 2000);
    });
    
    socket.on('payment_refunded', function(data) {
        // Hiện overlay màu đỏ báo lỗi
        var overlay = document.getElementById('qr-error-overlay');
        if (overlay) {
            overlay.classList.remove('d-none');
        }
        
        // Cập nhật lý do nếu có
        if (data && data.reason) {
            var reasonEl = document.getElementById('qr-error-reason');
            if (reasonEl) {
                reasonEl.textContent = "Xin lỗi, đã hoàn tiền. Lý do: " + data.reason;
            }
        }
        
        // Chờ 4 giây rồi chuyển về trang chủ
        setTimeout(function() {
            window.location.href = MY_BOOKINGS_URL;
        }, 4000);
    });
    
    // Xử lý sự kiện click nút Giả lập IPN (Dành cho DEV)
    var btnMockIpn = document.getElementById('btn-mock-ipn');
    if (btnMockIpn) {
        btnMockIpn.addEventListener('click', function() {
            // Thay đổi giao diện nút để báo đang xử lý
            btnMockIpn.disabled = true;
            btnMockIpn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Đang bắn IPN...';
            
            // Đóng gói payload giả lập MoMo
            var payload = {
                orderId: ORDER_ID,
                transId: "MOCK_" + Date.now(),
                amount: AMOUNT,
                resultCode: 0,
                extraData: EXTRA_DATA,
                signature: "TEST_DEV_SIGNATURE"
            };
            
            // Gửi request POST tới route momo-ipn
            fetch(MOMO_IPN_URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            }).then(function(res) {
                console.log("Mock IPN request completed with status: " + res.status);
            }).catch(function(err) {
                console.error("Mock IPN request failed:", err);
                btnMockIpn.disabled = false;
                btnMockIpn.innerHTML = 'Thử lại';
            });
        });
    }
});