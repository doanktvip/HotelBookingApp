document.addEventListener('DOMContentLoaded', function() {
    const minPriceInput = document.getElementById('minPriceInput');
    const maxPriceInput = document.getElementById('maxPriceInput');
    
    if (minPriceInput && maxPriceInput) {
        maxPriceInput.addEventListener('change', function() {
            const minVal = parseInt(minPriceInput.value) || 0;
            const maxVal = parseInt(maxPriceInput.value) || 0;
            
            // Nếu người dùng nhập giá Đến mà nhỏ hơn giá Từ (và giá Đến lớn hơn 0)
            if (maxPriceInput.value !== '' && maxVal < minVal) {
                maxPriceInput.value = minVal;
            }
        });
        
        minPriceInput.addEventListener('change', function() {
            const minVal = parseInt(minPriceInput.value) || 0;
            const maxVal = parseInt(maxPriceInput.value) || 0;
            
            // Nếu người dùng đẩy giá Từ lên cao hơn giá Đến hiện tại
            if (maxPriceInput.value !== '' && minVal > maxVal) {
                maxPriceInput.value = minVal;
            }
        });
    }
});
