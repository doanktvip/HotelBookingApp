// date_sync.js - Dùng chung cho mọi form có check_in và check_out
document.addEventListener('DOMContentLoaded', function() {
    const checkInInput = document.getElementById('check_in');
    const checkOutInput = document.getElementById('check_out');

    if (checkInInput && checkOutInput) {
        // Thiết lập min cho check_in là hôm nay (nếu chưa có)
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        const dd = String(today.getDate()).padStart(2, '0');
        const todayStr = `${yyyy}-${mm}-${dd}`;
        
        if (!checkInInput.min) {
            checkInInput.min = todayStr;
        }

        // Hàm cập nhật min của check_out dựa trên check_in
        function updateCheckOutMin() {
            const checkInDate = new Date(checkInInput.value);
            if (isNaN(checkInDate)) return;

            const nextDay = new Date(checkInDate);
            nextDay.setDate(nextDay.getDate() + 1);
            
            const n_yyyy = nextDay.getFullYear();
            const n_mm = String(nextDay.getMonth() + 1).padStart(2, '0');
            const n_dd = String(nextDay.getDate()).padStart(2, '0');
            const minCheckOutStr = `${n_yyyy}-${n_mm}-${n_dd}`;
            
            checkOutInput.min = minCheckOutStr;
            
            // Đẩy check_out lên nếu đang nhỏ hơn hoặc bằng check_in
            const currentCheckOut = new Date(checkOutInput.value);
            if (isNaN(currentCheckOut) || currentCheckOut <= checkInDate) {
                checkOutInput.value = minCheckOutStr;
                // Kích hoạt sự kiện change để các script khác (nếu có) nhận biết
                checkOutInput.dispatchEvent(new Event('change'));
            }
        }

        // Lắng nghe sự kiện change
        checkInInput.addEventListener('change', updateCheckOutMin);
        
        // Cập nhật ngay lúc load trang (nếu check_in đã có giá trị sẵn)
        if (checkInInput.value) {
            updateCheckOutMin();
        }
    }
});
