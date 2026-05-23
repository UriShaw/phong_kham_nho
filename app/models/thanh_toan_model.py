"""
Model Thanh Toán - Quản lý giao dịch thanh toán
"""
from core.model import BaseModel
from core.database import db


class ThanhToanModel(BaseModel):
    """Model cho bảng thanh_toan"""

    table_name = 'thanh_toan'

    @classmethod
    def tao_giao_dich(cls, lich_kham_id, benh_nhan_id, so_tien):
        """Tạo giao dịch thanh toán mới"""
        count = cls.count() + 1
        ma_gd = f"GD-{str(count).zfill(8)}"
        noi_dung = f"KHAM_{lich_kham_id}"

        return cls.create({
            'ma_giao_dich': ma_gd,
            'lich_kham_id': lich_kham_id,
            'benh_nhan_id': benh_nhan_id,
            'so_tien': so_tien,
            'phuong_thuc': 'qr_mbbank',
            'trang_thai': 'cho_thanh_toan',
            'noi_dung_ck': noi_dung
        })

    @classmethod
    def xac_nhan_thanh_toan(cls, giao_dich_id):
        """Xác nhận đã thanh toán"""
        now = db.get_one("SELECT NOW() as now")['now']
        return cls.update(giao_dich_id, {
            'trang_thai': 'da_thanh_toan',
            'ngay_thanh_toan': now
        })

    @classmethod
    def lay_theo_lich(cls, lich_kham_id):
        """Lấy giao dịch theo lịch khám"""
        return cls.find_by('lich_kham_id', lich_kham_id)

    @classmethod
    def doanh_thu_thang(cls):
        """Tính doanh thu tháng hiện tại"""
        sql = """
            SELECT COALESCE(SUM(so_tien), 0) as tong
            FROM thanh_toan
            WHERE trang_thai = 'da_thanh_toan'
            AND MONTH(ngay_thanh_toan) = MONTH(CURDATE())
            AND YEAR(ngay_thanh_toan) = YEAR(CURDATE())
        """
        result = db.get_one(sql)
        return result['tong'] if result else 0

    @classmethod
    def lich_su_thanh_toan(cls, benh_nhan_id):
        """Lịch sử thanh toán của bệnh nhân"""
        sql = """
            SELECT tt.*, lk.ma_lich, lk.ngay_kham,
                   nd.ho_ten as ten_bac_si, bs.hoc_vi
            FROM thanh_toan tt
            JOIN lich_kham lk ON tt.lich_kham_id = lk.id
            JOIN bac_si bs ON lk.bac_si_id = bs.id
            JOIN nguoi_dung nd ON bs.nguoi_dung_id = nd.id
            WHERE tt.benh_nhan_id = %s
            ORDER BY tt.ngay_tao DESC
        """
        return db.query(sql, (benh_nhan_id,))
