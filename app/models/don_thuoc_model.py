"""
Model Đơn Thuốc - Quản lý đơn thuốc điện tử
"""
from core.model import BaseModel
from core.database import db


class DonThuocModel(BaseModel):
    """Model cho bảng don_thuoc"""

    table_name = 'don_thuoc'

    @classmethod
    def tao_don_thuoc(cls, ho_so_id, benh_nhan_id, bac_si_id, ghi_chu, chi_tiet_list):
        """
        Tạo đơn thuốc kèm chi tiết
        chi_tiet_list: [{ten_thuoc, hoat_chat, lieu_dung, so_luong, don_vi, ghi_chu}]
        """
        # Tạo đơn thuốc
        don_thuoc_id = cls.create({
            'ho_so_id': ho_so_id,
            'benh_nhan_id': benh_nhan_id,
            'bac_si_id': bac_si_id,
            'ghi_chu': ghi_chu
        })

        if don_thuoc_id and chi_tiet_list:
            # Thêm chi tiết thuốc
            for thuoc in chi_tiet_list:
                db.execute("""
                    INSERT INTO chi_tiet_don_thuoc
                    (don_thuoc_id, ten_thuoc, hoat_chat, lieu_dung, so_luong, don_vi, ghi_chu)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    don_thuoc_id,
                    thuoc.get('ten_thuoc', ''),
                    thuoc.get('hoat_chat', ''),
                    thuoc.get('lieu_dung', ''),
                    thuoc.get('so_luong', 1),
                    thuoc.get('don_vi', 'viên'),
                    thuoc.get('ghi_chu', '')
                ))

        return don_thuoc_id

    @classmethod
    def lay_don_thuoc(cls, don_thuoc_id):
        """Lấy đơn thuốc kèm chi tiết"""
        don_thuoc = cls.get_by_id(don_thuoc_id)
        if don_thuoc:
            chi_tiet = db.query(
                "SELECT * FROM chi_tiet_don_thuoc WHERE don_thuoc_id = %s",
                (don_thuoc_id,)
            )
            don_thuoc['chi_tiet'] = chi_tiet
        return don_thuoc

    @classmethod
    def lay_theo_ho_so(cls, ho_so_id):
        """Lấy đơn thuốc theo hồ sơ bệnh án"""
        don_thuoc = cls.find_by('ho_so_id', ho_so_id)
        if don_thuoc:
            don_thuoc['chi_tiet'] = db.query(
                "SELECT * FROM chi_tiet_don_thuoc WHERE don_thuoc_id = %s",
                (don_thuoc['id'],)
            )
        return don_thuoc

    @classmethod
    def lay_tat_ca_theo_benh_nhan(cls, benh_nhan_id):
        """Lấy tất cả đơn thuốc của bệnh nhân kèm thông tin bác sĩ"""
        return db.query("""
            SELECT dt.*, nd.ho_ten AS ten_bac_si, ck.ten_chuyen_khoa,
                   hs.chan_doan, hs.ngay_tao AS ngay_kham
            FROM don_thuoc dt
            JOIN bac_si bs ON dt.bac_si_id = bs.id
            JOIN nguoi_dung nd ON bs.nguoi_dung_id = nd.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            JOIN ho_so_benh_an hs ON dt.ho_so_id = hs.id
            WHERE dt.benh_nhan_id = %s
            ORDER BY dt.ngay_tao DESC
        """, (benh_nhan_id,))

    @classmethod
    def lay_chi_tiet_cua_don(cls, don_thuoc_id):
        """Lấy chi tiết thuốc trong 1 đơn"""
        return db.query(
            "SELECT * FROM chi_tiet_don_thuoc WHERE don_thuoc_id = %s ORDER BY id",
            (don_thuoc_id,)
        )

    @classmethod
    def cap_nhat_don_thuoc(cls, don_thuoc_id, ghi_chu, chi_tiet_list):
        """Cập nhật đơn thuốc: xóa chi tiết cũ, thêm mới"""
        cls.update(don_thuoc_id, {'ghi_chu': ghi_chu})
        # Xóa chi tiết cũ
        db.execute("DELETE FROM chi_tiet_don_thuoc WHERE don_thuoc_id = %s", (don_thuoc_id,))
        # Thêm chi tiết mới
        for thuoc in chi_tiet_list:
            if thuoc.get('ten_thuoc', '').strip():
                db.execute("""
                    INSERT INTO chi_tiet_don_thuoc
                    (don_thuoc_id, ten_thuoc, hoat_chat, lieu_dung, so_luong, don_vi, ghi_chu)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    don_thuoc_id,
                    thuoc.get('ten_thuoc', ''),
                    thuoc.get('hoat_chat', ''),
                    thuoc.get('lieu_dung', ''),
                    thuoc.get('so_luong', 1),
                    thuoc.get('don_vi', 'viên'),
                    thuoc.get('ghi_chu', '')
                ))
        return don_thuoc_id

    @classmethod
    def xoa_don_thuoc(cls, don_thuoc_id):
        """Xóa đơn thuốc và chi tiết"""
        db.execute("DELETE FROM chi_tiet_don_thuoc WHERE don_thuoc_id = %s", (don_thuoc_id,))
        return cls.delete(don_thuoc_id)

    @classmethod
    def search_danh_muc(cls, keyword, limit=20):
        """Tìm thuốc từ danh mục (cho bác sĩ autocomplete)"""
        if not keyword or len(keyword) < 2:
            return []
        try:
            return db.query("""
                SELECT id, ten_thuoc, hoat_chat, nhom_thuoc, don_vi, ham_luong, lieu_dung_mau
                FROM danh_muc_thuoc
                WHERE trang_thai = 1
                  AND (ten_thuoc LIKE %s OR hoat_chat LIKE %s OR nhom_thuoc LIKE %s)
                ORDER BY ten_thuoc
                LIMIT %s
            """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit))
        except Exception:
            return []

    @classmethod
    def search_thuoc_theo_benh(cls, chan_doan, limit=30):
        """Tìm thuốc phù hợp theo chẩn đoán/bệnh của bệnh nhân"""
        if not chan_doan or len(chan_doan) < 2:
            return []
        try:
            # Tách từ khóa từ chẩn đoán
            keywords = [w.strip() for w in chan_doan.replace(',', ' ').split() if len(w.strip()) >= 2]
            if not keywords:
                return []

            # Tìm thuốc phù hợp
            conditions = []
            params = []
            for kw in keywords[:5]:  # Tối đa 5 từ khóa
                conditions.append("(nhom_thuoc LIKE %s OR hoat_chat LIKE %s OR ten_thuoc LIKE %s)")
                params.extend([f"%{kw}%"] * 3)

            where = " OR ".join(conditions)
            return db.query(f"""
                SELECT id, ten_thuoc, hoat_chat, nhom_thuoc, don_vi, ham_luong,
                       lieu_dung_mau
                FROM danh_muc_thuoc
                WHERE trang_thai = 1 AND ({where})
                ORDER BY ten_thuoc
                LIMIT %s
            """, tuple(params) + (limit,))
        except Exception:
            return []
