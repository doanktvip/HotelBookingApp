function previewAvatar(event) {
    var reader = new FileReader();
    reader.onload = function(){
        var output = document.getElementById('avatarPreview');
        if(output) {
            output.src = reader.result;
        }
    };
    if (event.target.files[0]) {
        reader.readAsDataURL(event.target.files[0]);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Hiện spinner khi submit để người dùng biết là đang upload lên Cloudinary
    var avatarUploadForm = document.getElementById('avatarUploadForm');
    if (avatarUploadForm) {
        avatarUploadForm.addEventListener('submit', function() {
            var btn = document.getElementById('btnUploadAvatar');
            if(btn) {
                btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Đang tải lên...';
                btn.disabled = true;
            }
        });
    }
});
