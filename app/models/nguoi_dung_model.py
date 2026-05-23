"""
Model Người Dùng - Quản lý tài khoản đăng nhập
"""
from core.model import BaseModel
from core.database import db
from werkzeug.security import generate_password_hash, check_password_hash


class NguoiDungModel(BaseModel):
    """Model cho bảng nguoi_dung"""

    table_name = 'nguoi_dung'

    @classmethod
    def tao_nguoi_dung(cls, ho_ten, email, mat_khau, so_dien_thoai='', vai_tro='benh_nhan'):
        """
        Tạo người dùng mới với mật khẩu đã hash
        Trả về ID người dùng mới hoặc None nếu email đã tồn tại
        """
        # Kiểm tra email trùng
        if cls.find_by('email', email):
            return None

        mat_khau_hash = generate_password_hash(mat_khau, method='pbkdf2:sha256')
        return cls.create({
            'ho_ten': ho_ten,
            'email': email,
            'mat_khau_hash': mat_khau_hash,
            'so_dien_thoai': so_dien_thoai,
            'vai_tro': vai_tro,
            'trang_thai': 1
        })

    @classmethod
    def xac_thuc(cls, tai_khoan, mat_khau):
        """
        Xác thực đăng nhập bằng email hoặc số điện thoại
        Trả về thông tin người dùng nếu thành công, None nếu thất bại
        """
        # Tìm theo email hoặc SĐT
        user = db.get_one(
            "SELECT * FROM nguoi_dung WHERE (email = %s OR so_dien_thoai = %s) AND trang_thai = 1",
            (tai_khoan, tai_khoan)
        )
        if user and check_password_hash(user['mat_khau_hash'], mat_khau):
            # Cập nhật lần đăng nhập cuối
            cls.update(user['id'], {'lan_dang_nhap_cuoi': db.get_one("SELECT NOW() as now")['now']})
            return user
        return None

    @classmethod
    def doi_mat_khau(cls, user_id, mat_khau_cu, mat_khau_moi):
        """Đổi mật khẩu"""
        user = cls.get_by_id(user_id)
        if user and check_password_hash(user['mat_khau_hash'], mat_khau_cu):
            new_hash = generate_password_hash(mat_khau_moi, method='pbkdf2:sha256')
            return cls.update(user_id, {'mat_khau_hash': new_hash})
        return None

    @classmethod
    def dem_theo_vai_tro(cls, vai_tro):
        """Đếm số người dùng theo vai trò"""
        return cls.count("vai_tro = %s AND trang_thai = 1", (vai_tro,))

    @classmethod
    def cap_nhat_avatar(cls, user_id, avatar_path):
        """Cập nhật ảnh đại diện"""
        return cls.update(user_id, {'avatar': avatar_path})
