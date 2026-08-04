// date_sync.js - Dùng chung cho mọi form có check_in và check_out
document.addEventListener('DOMContentLoaded', function() {
    const checkInInputs = document.querySelectorAll('input[name="check_in"]');
    
    checkInInputs.forEach(checkInInput => {
        const form = checkInInput.closest('form');
        if (!form) return;
        
        const checkOutInput = form.querySelector('input[name="check_out"]');
        if (!checkOutInput) return;

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
                checkOutInput.dispatchEvent(new Event('change'));
            }
        }

        checkInInput.addEventListener('change', updateCheckOutMin);
        
        // Nếu chưa có giá trị, tự động điền ngày hôm nay
        if (!checkInInput.value) {
            checkInInput.value = todayStr;
        }
        
        // Cập nhật check_out
        if (checkInInput.value) {
            updateCheckOutMin();
        }
    });
});
