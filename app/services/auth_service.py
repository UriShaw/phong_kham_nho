"""
Auth Service - Xử lý đăng nhập, đăng ký, phiên đăng nhập
"""
from flask import session
from app.models.nguoi_dung_model import NguoiDungModel
from app.models.benh_nhan_model import BenhNhanModel
from core.middleware import validate_input
from core.database import db


class AuthService:
    """Service xác thực người dùng"""

    # Rules validate đăng ký
    RULES_DANG_KY = {
        'ho_ten': {'required': True, 'min_length': 2, 'max_length': 100, 'message': 'Vui lòng nhập họ tên'},
        'email': {'required': True, 'type': 'email', 'message': 'Vui lòng nhập email hợp lệ'},
        'mat_khau': {'required': True, 'min_length': 6, 'message': 'Mật khẩu tối thiểu 6 ký tự'},
        'so_dien_thoai': {'required': True, 'type': 'phone', 'message': 'Số điện thoại không hợp lệ'},
    }

    # Rules validate đăng nhập
    RULES_DANG_NHAP = {
        'tai_khoan': {'required': True, 'message': 'Vui lòng nhập email hoặc số điện thoại'},
        'mat_khau': {'required': True, 'message': 'Vui lòng nhập mật khẩu'},
    }

    @staticmethod
    def dang_ky(data):
        """
        Đăng ký tài khoản mới
        Trả về: (success, message, user_id)
        """
        # Validate input
        is_valid, errors = validate_input(data, AuthService.RULES_DANG_KY)
        if not is_valid:
            return False, errors, None

        # Kiểm tra xác nhận mật khẩu
        if data.get('mat_khau') != data.get('xac_nhan_mat_khau'):
            return False, {'xac_nhan_mat_khau': 'Mật khẩu xác nhận không khớp'}, None

        # Kiểm tra SĐT trùng
        existing_phone = db.get_one(
            "SELECT id FROM nguoi_dung WHERE so_dien_thoai = %s",
            (data.get('so_dien_thoai', '').strip(),)
        )
        if existing_phone:
            return False, {'so_dien_thoai': 'Số điện thoại đã được sử dụng'}, None

        # Tạo tài khoản
        user_id = NguoiDungModel.tao_nguoi_dung(
            ho_ten=data['ho_ten'].strip(),
            email=data['email'].strip().lower(),
            mat_khau=data['mat_khau'],
            so_dien_thoai=data.get('so_dien_thoai', '').strip(),
            vai_tro='benh_nhan'
        )

        if not user_id:
            return False, {'email': 'Email đã được sử dụng'}, None

        # Tạo hồ sơ bệnh nhân
        BenhNhanModel.tao_benh_nhan(user_id, {
            'ngay_sinh': data.get('ngay_sinh'),
            'gioi_tinh': data.get('gioi_tinh', 'Nam'),
        })

        return True, 'Đăng ký thành công!', user_id

    @staticmethod
    def dang_nhap(data):
        """
        Đăng nhập bằng email hoặc số điện thoại
        Trả về: (success, message, user)
        """
        is_valid, errors = validate_input(data, AuthService.RULES_DANG_NHAP)
        if not is_valid:
            return False, errors, None

        tai_khoan = data['tai_khoan'].strip()

        user = NguoiDungModel.xac_thuc(
            tai_khoan=tai_khoan,
            mat_khau=data['mat_khau']
        )

        if not user:
            return False, {'tai_khoan': 'Email/SĐT hoặc mật khẩu không đúng'}, None

        # Lưu session
        session.permanent = True
        session['user_id'] = user['id']
        session['ho_ten'] = user['ho_ten']
        session['email'] = user['email']
        session['vai_tro'] = user['vai_tro']
        session['avatar'] = user.get('avatar', '')

        # Nếu là bệnh nhân, lấy thêm thông tin
        if user['vai_tro'] == 'benh_nhan':
            bn = BenhNhanModel.lay_theo_nguoi_dung(user['id'])
            if bn:
                session['benh_nhan_id'] = bn['id']
                session['ma_benh_nhan'] = bn.get('ma_benh_nhan', '')

        # Nếu là bác sĩ
        if user['vai_tro'] == 'bac_si':
            from app.models.bac_si_model import BacSiModel
            bs = BacSiModel.lay_theo_nguoi_dung(user['id'])
            if bs:
                session['bac_si_id'] = bs['id']

        return True, 'Đăng nhập thành công!', user

    @staticmethod
    def dang_xuat():
        """Đăng xuất - Xóa session"""
        session.clear()

    @staticmethod
    def lay_user_hien_tai():
        """Lấy thông tin user hiện tại từ session"""
        if 'user_id' not in session:
            return None
        return {
            'id': session.get('user_id'),
            'ho_ten': session.get('ho_ten'),
            'email': session.get('email'),
            'vai_tro': session.get('vai_tro'),
            'avatar': session.get('avatar'),
        }
