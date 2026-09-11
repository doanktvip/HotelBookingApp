document.addEventListener('DOMContentLoaded', function () {
    initTagsOverflow();
    initAIRecommendationsAsync();
    initSemanticSearchAsync();
});

function initAIRecommendationsAsync() {
    const container = document.getElementById('ai-recommendations-container');
    if (!container) return; // Chỉ chạy nếu ở trang chủ
    
    fetch('/api/recommendations')
        .then(response => {
            if (!response.ok) throw new Error("API Lỗi");
            return response.text();
        })
        .then(html => {
            container.innerHTML = html;
            // Sau khi render xong HTML mới, cần tính toán lại overflow của tags
            initTagsOverflow(); 
        })
        .catch(err => {
            console.error(err);
            const spinner = document.getElementById('ai-loading-spinner');
            if (spinner) {
                spinner.innerHTML = '<p class="text-danger">Lỗi khi tải gợi ý từ AI. Vui lòng thử lại sau.</p>';
            }
        });
}

function initSemanticSearchAsync() {
    const dataElement = document.getElementById('ai-search-data');
    if (!dataElement) return; // Nếu không có cờ này thì thôi (tức là tải bằng SQL bình thường)
    
    const keyword = dataElement.getAttribute('data-keyword');
    if (!keyword) return;

    // Lấy số trang từ URL hiện tại nếu có
    const urlParams = new URLSearchParams(window.location.search);
    const page = urlParams.get('page') || 1;

    fetchSemanticPage(keyword, page);
}

function fetchSemanticPage(keyword, page) {
    const container = document.getElementById('hotel-list-container');
    container.style.opacity = '0.5';
    
    fetch('/api/search?keyword=' + encodeURIComponent(keyword) + '&page=' + page)
        .then(response => {
            if (!response.ok) throw new Error("API Lỗi");
            return response.text();
        })
        .then(html => {
            container.innerHTML = html;
            container.style.opacity = '1';
            initTagsOverflow(); 
            bindSemanticPagination(keyword);
        })
        .catch(err => {
            console.error(err);
            container.style.opacity = '1';
            const spinner = document.getElementById('ai-loading-spinner');
            if (spinner) {
                spinner.innerHTML = '<p class="text-danger">Lỗi khi phân tích bằng AI. Vui lòng thử lại sau.</p>';
            }
        });
}

function bindSemanticPagination(keyword) {
    const container = document.getElementById('hotel-list-container');
    if (!container) return;
    
    const links = container.querySelectorAll('.pagination .page-link');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            if (!href || href === '#') return;
            
            const url = new URL(href, window.location.origin);
            const page = url.searchParams.get('page');
            
            if (page) {
                // Đổi URL trên trình duyệt
                const newUrl = new URL(window.location);
                newUrl.searchParams.set('page', page);
                newUrl.searchParams.set('keyword', keyword);
                window.history.pushState({}, '', newUrl);

                // Load dữ liệu trang mới
                fetchSemanticPage(keyword, page);
                
                // Cuộn nhẹ lên đầu vùng danh sách
                container.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

function initTagsOverflow() {
    const containers = document.querySelectorAll('.hotel-tags-container');
    containers.forEach(container => {
        // Lấy tất cả các tags ban đầu
        const badges = Array.from(container.querySelectorAll('.tag-badge-original'));
        const existingMore = container.querySelector('.tag-more-badge');
        if (existingMore) existingMore.remove();
        
        badges.forEach(b => b.style.display = 'inline-block');
        if (badges.length === 0) return;

        // Tính toán dòng
        let firstTop = badges[0].offsetTop;
        let hiddenBadges = [];
        
        // Bước 1: Ẩn các thẻ từ dòng thứ 3 trở đi
        for (let i = 0; i < badges.length; i++) {
            // Khoảng cách > 40px từ thẻ đầu tiên nghĩa là rớt xuống dòng 3
            if (badges[i].offsetTop > firstTop + 40) {
                hiddenBadges.push(badges[i]);
                badges[i].style.display = 'none';
            }
        }

        // Bước 2: Nếu có thẻ bị ẩn, thêm nút +N
        if (hiddenBadges.length > 0) {
            let moreBtn = document.createElement('span');
            moreBtn.className = 'badge tag-more-badge';
            moreBtn.style.cssText = 'background-color: #f0f7ff; color: #0d6efd; font-weight: 500; padding: 0.4rem 0.75rem; border-radius: 20px; cursor: help;';
            
            const updateMoreBtn = () => {
                moreBtn.textContent = '+' + hiddenBadges.length;
                moreBtn.title = hiddenBadges.map(b => b.textContent.trim()).join('\n');
            };
            
            updateMoreBtn();
            container.appendChild(moreBtn);

            // Bước 3: Đảm bảo nút +N không bị rớt xuống dòng 3 do thiếu chỗ ở dòng 2
            while (moreBtn.offsetTop > firstTop + 40) {
                const visibleBadges = badges.filter(b => b.style.display !== 'none');
                if (visibleBadges.length === 0) break;
                
                const lastVisible = visibleBadges[visibleBadges.length - 1];
                lastVisible.style.display = 'none';
                hiddenBadges.unshift(lastVisible);
                updateMoreBtn();
            }
        }
    });
}

// Chạy lại hàm tính toán khi người dùng thay đổi kích thước cửa sổ
window.addEventListener('resize', initTagsOverflow);

/* Hàm hỗ trợ UX cho AI Search */
function showAILoading(form) {
    const btn = form.querySelector('.ai-submit-btn');
    if(btn) {
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Đang phân tích...';
        btn.style.pointerEvents = 'none';
        btn.classList.add('opacity-75');
    }
}
