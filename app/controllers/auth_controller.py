"""
Auth Controller - Đăng nhập, Đăng ký, Đăng xuất
"""
from flask import Blueprint, request, redirect, url_for, flash, session
from core.controller import BaseController
from core.middleware import generate_csrf_token
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/dang-nhap', methods=['GET', 'POST'])
def dang_nhap():
    """Trang đăng nhập"""
    if 'user_id' in session:
        return _redirect_theo_vai_tro()

    if request.method == 'POST':
        data = {
            'tai_khoan': request.form.get('tai_khoan', ''),
            'mat_khau': request.form.get('mat_khau', ''),
        }

        success, message, user = AuthService.dang_nhap(data)

        if success:
            flash('Đăng nhập thành công! 🎉', 'success')
            # Redirect đến trang trước đó hoặc theo vai trò
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            return _redirect_theo_vai_tro()
        else:
            # message là dict errors
            if isinstance(message, dict):
                for field, msg in message.items():
                    flash(msg, 'danger')
            else:
                flash(message, 'danger')


    return BaseController.render('auth/dang_nhap.html')


@auth_bp.route('/dang-ky', methods=['GET', 'POST'])
def dang_ky():
    """Trang đăng ký"""
    if 'user_id' in session:
        return _redirect_theo_vai_tro()

    if request.method == 'POST':
        data = {
            'ho_ten': request.form.get('ho_ten', ''),
            'email': request.form.get('email', ''),
            'mat_khau': request.form.get('mat_khau', ''),
            'xac_nhan_mat_khau': request.form.get('xac_nhan_mat_khau', ''),
            'so_dien_thoai': request.form.get('so_dien_thoai', ''),
            'ngay_sinh': request.form.get('ngay_sinh'),
            'gioi_tinh': request.form.get('gioi_tinh', 'Nam'),
        }

        success, message, user_id = AuthService.dang_ky(data)

        if success:
            flash('Đăng ký thành công! Vui lòng đăng nhập. 🎉', 'success')
            return redirect(url_for('auth.dang_nhap'))
        else:
            if isinstance(message, dict):
                for field, msg in message.items():
                    flash(msg, 'danger')
            else:
                flash(message, 'danger')


    return BaseController.render('auth/dang_ky.html')


@auth_bp.route('/dang-xuat')
def dang_xuat():
    """Đăng xuất"""
    AuthService.dang_xuat()
    flash('Đã đăng xuất thành công.', 'info')
    return redirect(url_for('auth.dang_nhap'))


def _redirect_theo_vai_tro():
    """Chuyển hướng theo vai trò người dùng"""
    vai_tro = session.get('vai_tro')
    if vai_tro == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif vai_tro == 'bac_si':
        return redirect(url_for('bac_si.dashboard'))
    else:
        return redirect(url_for('benh_nhan.trang_chu'))
