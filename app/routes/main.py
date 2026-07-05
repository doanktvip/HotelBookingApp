from flask import Blueprint, render_template

# Định nghĩa Blueprint cho các tuyến đường chính
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Route trang chủ."""
    return render_template('index.html')
