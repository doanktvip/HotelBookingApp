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
    
    // Cập nhật tính toán
    function calculateTotal() {
        if (!checkInInput || !checkOutInput || !checkInInput.value || !checkOutInput.value) return;
        
        const d1 = new Date(checkInInput.value);
        const d2 = new Date(checkOutInput.value);
        
        // Lưu ý: Việc cập nhật min của check_out khi check_in thay đổi
        // và đẩy check_out tịnh tiến lên đã được xử lý ở date_sync.js
        
        // Vì date_sync.js có thể đang tự động sửa checkOutInput.value ngay lúc này,
        // ta cần đọc lại giá trị mới nhất của d2
        const finalD2 = new Date(checkOutInput.value);
        
        if (finalD2 <= d1) {
            return; // Tránh tính toán sai nếu d2 vẫn chưa được cập nhật kịp
        }
        
        const timeDiff = Math.abs(finalD2.getTime() - d1.getTime());
        const diffDays = Math.ceil(timeDiff / (1000 * 3600 * 24));
        
        const qty = quantityInput ? (parseInt(quantityInput.value) || 1) : 1;
        const subtotal = diffDays * qty * basePrice;
        
        // Sử dụng biến toàn cục TAX_FEE_PERCENT đã được truyền từ Jinja2
        const taxFeePercent = typeof TAX_FEE_PERCENT !== 'undefined' ? TAX_FEE_PERCENT : 0;
        const tax = subtotal * (taxFeePercent / 100);
        const total = subtotal + tax;
        
        const formattedSubtotal = subtotal.toLocaleString('vi-VN') + 'đ';
        const formattedTax = tax.toLocaleString('vi-VN') + 'đ';
        const formattedTotal = total.toLocaleString('vi-VN') + 'đ';
        const formattedBase = basePrice.toLocaleString('vi-VN') + 'đ';
        
        // Cập nhật DOM
        if (sCheckin) sCheckin.textContent = formatDateVN(checkInInput.value);
        if (sCheckout) sCheckout.textContent = formatDateVN(checkOutInput.value);
        if (sNights) sNights.textContent = `${diffDays} đêm`;
        if (sQty) sQty.textContent = `${qty} phòng`;
        
        const calcBasePriceEl = document.getElementById('calc-base-price');
        const calcNightsEl = document.getElementById('calc-nights');
        const calcQtyEl = document.getElementById('calc-qty');
        const summaryTaxEl = document.getElementById('summary-tax');
        
        if (calcBasePriceEl) calcBasePriceEl.textContent = formattedBase;
        if (calcNightsEl) calcNightsEl.textContent = diffDays;
        if (calcQtyEl) calcQtyEl.textContent = qty;
        
        if (sSubtotal) sSubtotal.textContent = formattedSubtotal;
        if (summaryTaxEl) summaryTaxEl.textContent = formattedTax;
        if (sTotal) sTotal.textContent = formattedTotal;
        if (btnTotal) btnTotal.textContent = formattedTotal;
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
