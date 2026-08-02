from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.extensions import db
from app.services.user_service import UserService
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_service = UserService(db.session)
        
        try:
            user = user_service.auth_user(username, password)
            login_user(user)
            return redirect(url_for('main.index'))
        except ValueError as e:
            flash(str(e), 'danger')
            return redirect(url_for('auth.login'))
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    user_service = UserService(db.session)
    
    try:
        user_service.add_user(username, email, password, confirm_password)
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('auth.login'))
    
    flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
    