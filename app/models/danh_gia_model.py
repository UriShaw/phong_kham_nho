"""
Model đánh giá bác sĩ - CRUD cho bệnh nhân đánh giá bác sĩ
"""
from core.database import db


class DanhGiaBacSiModel:

    @staticmethod
    def lay_theo_bac_si(bac_si_id, limit=20):
        """Lấy danh sách đánh giá của 1 bác sĩ"""
        return db.query("""
            SELECT dg.*, nd.ho_ten AS ten_benh_nhan
            FROM danh_gia_bac_si dg
            JOIN benh_nhan bn ON dg.benh_nhan_id = bn.id
            JOIN nguoi_dung nd ON bn.nguoi_dung_id = nd.id
            WHERE dg.bac_si_id = %s
            ORDER BY dg.ngay_tao DESC
            LIMIT %s
        """, (bac_si_id, limit))

    @staticmethod
    def lay_theo_id(danh_gia_id):
        """Lấy chi tiết 1 đánh giá"""
        rows = db.query("SELECT * FROM danh_gia_bac_si WHERE id = %s", (danh_gia_id,))
        return rows[0] if rows else None

    @staticmethod
    def them(bac_si_id, benh_nhan_id, diem, noi_dung):
        """Thêm đánh giá mới"""
        db.execute("""
            INSERT INTO danh_gia_bac_si (bac_si_id, benh_nhan_id, diem, noi_dung)
            VALUES (%s, %s, %s, %s)
        """, (bac_si_id, benh_nhan_id, diem, noi_dung))
        # Cập nhật điểm trung bình cho bác sĩ
        DanhGiaBacSiModel._cap_nhat_diem_tb(bac_si_id)

    @staticmethod
    def sua(danh_gia_id, diem, noi_dung):
        """Sửa đánh giá"""
        dg = DanhGiaBacSiModel.lay_theo_id(danh_gia_id)
        if not dg:
            return False
        db.execute("""
            UPDATE danh_gia_bac_si SET diem = %s, noi_dung = %s WHERE id = %s
        """, (diem, noi_dung, danh_gia_id))
        DanhGiaBacSiModel._cap_nhat_diem_tb(dg['bac_si_id'])
        return True

    @staticmethod
    def xoa(danh_gia_id):
        """Xóa đánh giá"""
        dg = DanhGiaBacSiModel.lay_theo_id(danh_gia_id)
        if not dg:
            return False
        db.execute("DELETE FROM danh_gia_bac_si WHERE id = %s", (danh_gia_id,))
        DanhGiaBacSiModel._cap_nhat_diem_tb(dg['bac_si_id'])
        return True

    @staticmethod
    def _cap_nhat_diem_tb(bac_si_id):
        """Cập nhật điểm đánh giá trung bình cho bác sĩ"""
        rows = db.query("""
            SELECT COALESCE(AVG(diem), 5.0) AS avg_diem, COUNT(*) AS total
            FROM danh_gia_bac_si WHERE bac_si_id = %s
        """, (bac_si_id,))
        if rows:
            avg = round(float(rows[0]['avg_diem']), 1)
            total = rows[0]['total']
            db.execute("""
                UPDATE bac_si SET danh_gia = %s, so_danh_gia = %s WHERE id = %s
            """, (avg, total, bac_si_id))

    @staticmethod
    def da_danh_gia(bac_si_id, benh_nhan_id):
        """Kiểm tra bệnh nhân đã đánh giá bác sĩ chưa"""
        rows = db.query("""
            SELECT id FROM danh_gia_bac_si
            WHERE bac_si_id = %s AND benh_nhan_id = %s LIMIT 1
        """, (bac_si_id, benh_nhan_id))
        return rows[0] if rows else None
