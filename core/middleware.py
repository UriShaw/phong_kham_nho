"""
Middleware - Bảo mật và xác thực
CSRF token, login_required, role_required
"""
import os
import hashlib
import time
from functools import wraps
from flask import session, redirect, url_for, flash, request, abort


def generate_csrf_token():
    """Tạo CSRF token ngẫu nhiên và lưu vào session"""
    if '_csrf_token' not in session:
        session['_csrf_token'] = hashlib.sha256(
            os.urandom(32) + str(time.time()).encode()
        ).hexdigest()
    return session['_csrf_token']


def validate_csrf_token():
    """Kiểm tra CSRF token từ form"""
    token = session.get('_csrf_token')
    form_token = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
    if not token or token != form_token:
        abort(403, 'CSRF token không hợp lệ')


def login_required(f):
    """
    Decorator: Yêu cầu đăng nhập
    Chuyển hướng về trang đăng nhập nếu chưa login
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để tiếp tục.', 'warning')
            return redirect(url_for('auth.dang_nhap', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """
    Decorator: Yêu cầu vai trò cụ thể
    Sử dụng: @role_required('admin', 'bac_si')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Vui lòng đăng nhập để tiếp tục.', 'warning')
                return redirect(url_for('auth.dang_nhap'))
            if session.get('vai_tro') not in roles:
                flash('Bạn không có quyền truy cập trang này.', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_input(data, rules):
    """
    Validate input theo rules
    rules: dict {field: {required, min_length, max_length, type, pattern}}
    Trả về: (is_valid, errors)
    """
    errors = {}

    for field, rule in rules.items():
        value = data.get(field, '').strip() if isinstance(data.get(field), str) else data.get(field)

        # Kiểm tra bắt buộc
        if rule.get('required') and not value:
            errors[field] = rule.get('message', f'{field} là bắt buộc')
            continue

        if value:
            # Kiểm tra độ dài tối thiểu
            if rule.get('min_length') and len(str(value)) < rule['min_length']:
                errors[field] = f'Tối thiểu {rule["min_length"]} ký tự'

            # Kiểm tra độ dài tối đa
            if rule.get('max_length') and len(str(value)) > rule['max_length']:
                errors[field] = f'Tối đa {rule["max_length"]} ký tự'

            # Kiểm tra email đơn giản
            if rule.get('type') == 'email' and '@' not in str(value):
                errors[field] = 'Email không hợp lệ'

            # Kiểm tra số điện thoại
            if rule.get('type') == 'phone':
                phone = str(value).replace(' ', '').replace('-', '')
                if not phone.isdigit() or len(phone) < 9:
                    errors[field] = 'Số điện thoại không hợp lệ'

    is_valid = len(errors) == 0
    return is_valid, errors
