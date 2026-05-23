"""
Model Bệnh Nhân - Quản lý thông tin bệnh nhân
"""
from core.model import BaseModel
from core.database import db


class BenhNhanModel(BaseModel):
    """Model cho bảng benh_nhan"""

    table_name = 'benh_nhan'

    @classmethod
    def lay_theo_nguoi_dung(cls, nguoi_dung_id):
        """Lấy thông tin bệnh nhân theo nguoi_dung_id"""
        return cls.find_by('nguoi_dung_id', nguoi_dung_id)

    @classmethod
    def lay_chi_tiet(cls, benh_nhan_id):
        """Lấy thông tin chi tiết bệnh nhân kèm tên"""
        sql = """
            SELECT bn.*, nd.ho_ten, nd.email, nd.so_dien_thoai, nd.avatar
            FROM benh_nhan bn
            JOIN nguoi_dung nd ON bn.nguoi_dung_id = nd.id
            WHERE bn.id = %s
        """
        return db.get_one(sql, (benh_nhan_id,))

    @classmethod
    def tao_benh_nhan(cls, nguoi_dung_id, data=None):
        """Tạo hồ sơ bệnh nhân mới với mã tự động"""
        # Tạo mã bệnh nhân tự động
        count = cls.count() + 10293
        ma_bn = f"BN-{count}"

        benh_nhan_data = {
            'nguoi_dung_id': nguoi_dung_id,
            'ma_benh_nhan': ma_bn,
        }
        if data:
            benh_nhan_data.update(data)

        return cls.create(benh_nhan_data)

    @classmethod
    def cap_nhat_suc_khoe(cls, benh_nhan_id, data):
        """Cập nhật thông tin sức khỏe"""
        allowed = ['chieu_cao', 'can_nang', 'huyet_ap', 'nhip_tim', 'nhom_mau']
        update_data = {k: v for k, v in data.items() if k in allowed and v}
        if update_data:
            return cls.update(benh_nhan_id, update_data)
        return None

    @classmethod
    def lay_gia_dinh(cls, nhom_gia_dinh_id):
        """Lấy thành viên gia đình cùng nhóm"""
        if not nhom_gia_dinh_id:
            return []
        sql = """
            SELECT bn.*, nd.ho_ten, nd.avatar
            FROM benh_nhan bn
            JOIN nguoi_dung nd ON bn.nguoi_dung_id = nd.id
            WHERE bn.nhom_gia_dinh_id = %s
        """
        return db.query(sql, (nhom_gia_dinh_id,))

    @classmethod
    def danh_sach_benh_nhan(cls, page=1, per_page=10, search=''):
        """Danh sách bệnh nhân có phân trang và tìm kiếm"""
        where = "1=1"
        params = []
        if search:
            where = "(nd.ho_ten LIKE %s OR bn.ma_benh_nhan LIKE %s OR nd.so_dien_thoai LIKE %s)"
            params = [f"%{search}%", f"%{search}%", f"%{search}%"]

        # Đếm tổng
        count_sql = f"""
            SELECT COUNT(*) as total FROM benh_nhan bn
            JOIN nguoi_dung nd ON bn.nguoi_dung_id = nd.id
            WHERE {where}
        """
        total = db.get_one(count_sql, tuple(params))['total']

        # Lấy danh sách
        offset = (page - 1) * per_page
        sql = f"""
            SELECT bn.*, nd.ho_ten, nd.email, nd.so_dien_thoai, nd.avatar
            FROM benh_nhan bn
            JOIN nguoi_dung nd ON bn.nguoi_dung_id = nd.id
            WHERE {where}
            ORDER BY bn.id DESC
            LIMIT {per_page} OFFSET {offset}
        """
        items = db.query(sql, tuple(params))
        total_pages = (total + per_page - 1) // per_page

        return {
            'danh_sach': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages
        }
