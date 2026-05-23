"""
Model Thông Báo - Quản lý thông báo hệ thống
"""
from core.model import BaseModel
from core.database import db


class ThongBaoModel(BaseModel):
    """Model cho bảng thong_bao"""

    table_name = 'thong_bao'

    @classmethod
    def gui_thong_bao(cls, nguoi_dung_id, tieu_de, noi_dung, loai='he_thong', link=''):
        """Gửi thông báo mới"""
        return cls.create({
            'nguoi_dung_id': nguoi_dung_id,
            'tieu_de': tieu_de,
            'noi_dung': noi_dung,
            'loai': loai,
            'link': link,
            'da_doc': 0
        })

    @classmethod
    def lay_cua_nguoi_dung(cls, nguoi_dung_id, limit=20):
        """Lấy thông báo của người dùng"""
        sql = """
            SELECT * FROM thong_bao
            WHERE nguoi_dung_id = %s
            ORDER BY ngay_tao DESC
            LIMIT %s
        """
        return db.query(sql, (nguoi_dung_id, limit))

    @classmethod
    def dem_chua_doc(cls, nguoi_dung_id):
        """Đếm thông báo chưa đọc"""
        return cls.count("nguoi_dung_id = %s AND da_doc = 0", (nguoi_dung_id,))

    @classmethod
    def danh_dau_da_doc(cls, thong_bao_id):
        """Đánh dấu đã đọc"""
        return cls.update(thong_bao_id, {'da_doc': 1})

    @classmethod
    def doc_tat_ca(cls, nguoi_dung_id):
        """Đánh dấu tất cả đã đọc"""
        sql = "UPDATE thong_bao SET da_doc = 1 WHERE nguoi_dung_id = %s AND da_doc = 0"
        return db.execute(sql, (nguoi_dung_id,))
