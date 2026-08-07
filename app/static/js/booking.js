document.addEventListener('DOMContentLoaded', function() {
    const checkInInput = document.getElementById('check_in');
    const checkOutInput = document.getElementById('check_out');
    const quantityInput = document.getElementById('quantity');
    const paymentRadios = document.querySelectorAll('input[name="payment_method"]');
    const btnMethodText = document.getElementById('btn-method-text');
    
    // Tóm tắt DOM
    const sCheckin = document.getElementById('summary-checkin');
    const sCheckout = document.getElementById('summary-checkout');
    const sNights = document.getElementById('summary-nights');
    const sQty = document.getElementById('summary-qty');
    const sSubtotal = document.getElementById('summary-subtotal');
    const sTotal = document.getElementById('summary-total');
    const btnTotal = document.getElementById('btn-total');
    
    const basePriceElement = document.getElementById('basePrice');
    const basePrice = basePriceElement ? parseFloat(basePriceElement.dataset.price) : 0;
    
    // Lưu ý: Logic khởi tạo ngày (min, value ban đầu) và tự động đẩy ngày trả phòng
    // đã được chuyển sang file dùng chung date_sync.js
    
    
    // Format VN date
    function formatDateVN(dateStr) {
        if(!dateStr) return "-";
        const d = new Date(dateStr);
        return `${d.getDate()} tháng ${d.getMonth() + 1}, ${d.getFullYear()}`;
    }
    
    // Update phương thức thanh toán text
    function updateMethodText() {
        const checkedRadio = document.querySelector('input[name="payment_method"]:checked');
        if (!checkedRadio || !btnMethodText) return;
        const selected = checkedRadio.value;
        if(selected === 'MOMO') btnMethodText.textContent = 'qua MoMo';
        else btnMethodText.textContent = 'qua VNPAY';
    }
    
    paymentRadios.forEach(radio => radio.addEventListener('change', updateMethodText));
    
    // Cập nhật tính toán qua API
    async function calculateTotal() {
        if (!checkInInput || !checkOutInput || !checkInInput.value || !checkOutInput.value) return;
        
        const d1 = new Date(checkInInput.value);
        const finalD2 = new Date(checkOutInput.value);
        
        if (finalD2 <= d1) {
            return; // Tránh tính toán sai nếu d2 vẫn chưa được cập nhật kịp
        }
        
        const qty = quantityInput ? (parseInt(quantityInput.value) || 1) : 1;
        
        // Lấy room_type_id từ form
        const form = document.getElementById('bookingForm');
        let action = form.getAttribute('action');
        let roomTypeIdMatch = action.match(/\/booking\/room-type\/(\d+)/);
        let roomTypeId = roomTypeIdMatch ? roomTypeIdMatch[1] : null;

        if (!roomTypeId) return;

        try {
            const response = await fetch('/api/booking/calculate-price', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    check_in: checkInInput.value,
                    check_out: checkOutInput.value,
                    quantity: qty,
                    room_type_id: roomTypeId
                })
            });

            if (!response.ok) throw new Error('API Error');
            const data = await response.json();

            const subtotal = data.total_price / (1 + (typeof TAX_FEE_PERCENT !== 'undefined' ? TAX_FEE_PERCENT / 100 : 0));
            const tax = data.total_price - subtotal;
            const total = data.total_price;
            
            const formattedSubtotal = subtotal.toLocaleString('vi-VN') + 'đ';
            const formattedTax = tax.toLocaleString('vi-VN') + 'đ';
            const formattedTotal = total.toLocaleString('vi-VN') + 'đ';
            const formattedBase = basePrice.toLocaleString('vi-VN') + 'đ';
            
            // Cập nhật DOM
            if (sCheckin) sCheckin.textContent = formatDateVN(checkInInput.value);
            if (sCheckout) sCheckout.textContent = formatDateVN(checkOutInput.value);
            if (sNights) sNights.textContent = `${data.days} đêm`;
            if (sQty) sQty.textContent = `${qty} phòng`;
            
            const calcBasePriceEl = document.getElementById('calc-base-price');
            const calcNightsEl = document.getElementById('calc-nights');
            const calcQtyEl = document.getElementById('calc-qty');
            const summaryTaxEl = document.getElementById('summary-tax');
            
            // Nếu có API trả về giá trị avg_daily_price, ta có thể cập nhật chi tiết ở đây
            // UI sẽ cần cập nhật ở template jinja2. Ở JS tạm thời điền format cơ bản
            if (calcBasePriceEl) calcBasePriceEl.textContent = (data.average_daily_price || basePrice).toLocaleString('vi-VN') + 'đ';
            if (calcNightsEl) calcNightsEl.textContent = data.days;
            if (calcQtyEl) calcQtyEl.textContent = qty;
            
            if (sSubtotal) sSubtotal.textContent = formattedSubtotal;
            if (summaryTaxEl) summaryTaxEl.textContent = formattedTax;
            if (sTotal) sTotal.textContent = formattedTotal;
            if (btnTotal) btnTotal.textContent = formattedTotal;
            
            // Cập nhật màu sắc nếu giá thay đổi (tuỳ chọn thêm class)
            const priceWrapper = document.getElementById('price-wrapper');
            const basePriceEl = document.getElementById('basePrice');
            const strikeEl = document.getElementById('base-price-strikethrough');
            
            if (basePriceEl) {
                basePriceEl.textContent = (data.average_daily_price || basePrice).toLocaleString('vi-VN') + 'đ';
            }
            
            if (priceWrapper && data.average_daily_price < basePrice) {
                if (strikeEl) strikeEl.classList.remove('d-none');
                if (basePriceEl) {
                    basePriceEl.classList.remove('text-primary');
                    basePriceEl.classList.add('text-danger');
                }
            } else if (priceWrapper) {
                if (strikeEl) strikeEl.classList.add('d-none');
                if (basePriceEl) {
                    basePriceEl.classList.remove('text-danger');
                    basePriceEl.classList.add('text-primary');
                }
            }

        } catch (error) {
            console.error('Lỗi tính giá:', error);
        }
    }
    
    if (checkInInput) checkInInput.addEventListener('change', calculateTotal);
    if (checkOutInput) checkOutInput.addEventListener('change', calculateTotal);
    if (quantityInput) quantityInput.addEventListener('change', calculateTotal);
    
    // Ngăn chặn bấm nút Thanh toán nhiều lần (Double Submit Prevention)
    const bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            const submitBtn = bookingForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                if (submitBtn.disabled) {
                    e.preventDefault();
                    return;
                }
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Đang xử lý thanh toán...';
            }
        });
    }
    
    calculateTotal();
    updateMethodText();
});
