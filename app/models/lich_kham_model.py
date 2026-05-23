"""
Model Lịch Khám - Quản lý lịch hẹn khám bệnh
"""
from core.model import BaseModel
from core.database import db


class LichKhamModel(BaseModel):
    """Model cho bảng lich_kham"""

    table_name = 'lich_kham'

    @classmethod
    def tao_lich(cls, benh_nhan_id, bac_si_id, ngay_kham, gio_kham, ly_do='', phong_kham=''):
        """Tạo lịch khám mới với mã tự động"""
        # Kiểm tra trùng lịch
        trung = db.get_one("""
            SELECT id FROM lich_kham
            WHERE bac_si_id = %s AND ngay_kham = %s AND gio_kham = %s
            AND trang_thai NOT IN ('da_huy', 'hoan_thanh')
        """, (bac_si_id, ngay_kham, gio_kham))

        if trung:
            return None  # Trùng lịch

        # Tạo mã lịch
        count = cls.count() + 1
        ma_lich = f"LK-{str(count).zfill(8)}"

        return cls.create({
            'ma_lich': ma_lich,
            'benh_nhan_id': benh_nhan_id,
            'bac_si_id': bac_si_id,
            'ngay_kham': ngay_kham,
            'gio_kham': gio_kham,
            'ly_do': ly_do,
            'phong_kham': phong_kham,
            'trang_thai': 'cho_xac_nhan'
        })

    @classmethod
    def lich_cua_benh_nhan(cls, benh_nhan_id, trang_thai=None):
        """Lấy lịch khám của bệnh nhân"""
        where = "lk.benh_nhan_id = %s"
        params = [benh_nhan_id]

        if trang_thai:
            where += " AND lk.trang_thai = %s"
            params.append(trang_thai)

        sql = f"""
            SELECT lk.*, nd.ho_ten as ten_bac_si, bs.hoc_vi,
                   ck.ten_chuyen_khoa, bs.gia_kham, nd.avatar as avatar_bs,
                   CONCAT(bs.hoc_vi, ' ', nd.ho_ten) as ten_hien_thi_bs
            FROM lich_kham lk
            JOIN bac_si bs ON lk.bac_si_id = bs.id
            JOIN nguoi_dung nd ON bs.nguoi_dung_id = nd.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE {where}
            ORDER BY lk.ngay_kham DESC, lk.gio_kham DESC
        """
        return db.query(sql, tuple(params))

    @classmethod
    def lich_cua_bac_si(cls, bac_si_id, ngay=None, trang_thai=None):
        """Lấy lịch khám của bác sĩ"""
        where = "lk.bac_si_id = %s"
        params = [bac_si_id]

        if ngay:
            where += " AND lk.ngay_kham = %s"
            params.append(ngay)

        if trang_thai:
            where += " AND lk.trang_thai = %s"
            params.append(trang_thai)

        sql = f"""
            SELECT lk.*, nd_bn.ho_ten as ten_benh_nhan, bn.ma_benh_nhan,
                   bn.gioi_tinh, bn.ngay_sinh, nd_bn.avatar as avatar_bn,
                   TIMESTAMPDIFF(YEAR, bn.ngay_sinh, CURDATE()) as tuoi
            FROM lich_kham lk
            JOIN benh_nhan bn ON lk.benh_nhan_id = bn.id
            JOIN nguoi_dung nd_bn ON bn.nguoi_dung_id = nd_bn.id
            WHERE {where}
            ORDER BY lk.gio_kham ASC
        """
        return db.query(sql, tuple(params))

    @classmethod
    def chi_tiet_lich(cls, lich_id):
        """Lấy chi tiết 1 lịch khám đầy đủ"""
        sql = """
            SELECT lk.*,
                   nd_bn.ho_ten as ten_benh_nhan, bn.ma_benh_nhan,
                   bn.gioi_tinh, bn.ngay_sinh, bn.huyet_ap as bn_huyet_ap,
                   bn.nhom_mau, nd_bn.so_dien_thoai as sdt_bn,
                   TIMESTAMPDIFF(YEAR, bn.ngay_sinh, CURDATE()) as tuoi,
                   nd_bs.ho_ten as ten_bac_si, bs.hoc_vi,
                   ck.ten_chuyen_khoa, bs.gia_kham, bs.benh_vien,
                   CONCAT(bs.hoc_vi, ' ', nd_bs.ho_ten) as ten_hien_thi_bs,
                   nd_bs.avatar as avatar_bs, nd_bn.avatar as avatar_bn
            FROM lich_kham lk
            JOIN benh_nhan bn ON lk.benh_nhan_id = bn.id
            JOIN nguoi_dung nd_bn ON bn.nguoi_dung_id = nd_bn.id
            JOIN bac_si bs ON lk.bac_si_id = bs.id
            JOIN nguoi_dung nd_bs ON bs.nguoi_dung_id = nd_bs.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE lk.id = %s
        """
        return db.get_one(sql, (lich_id,))

    @classmethod
    def cap_nhat_trang_thai(cls, lich_id, trang_thai):
        """Cập nhật trạng thái lịch khám"""
        return cls.update(lich_id, {'trang_thai': trang_thai})

    @classmethod
    def lay_slot_trong(cls, bac_si_id, ngay_kham):
        """Lấy khung giờ đã đặt của bác sĩ trong ngày"""
        sql = """
            SELECT gio_kham FROM lich_kham
            WHERE bac_si_id = %s AND ngay_kham = %s
            AND trang_thai NOT IN ('da_huy')
        """
        booked = db.query(sql, (bac_si_id, ngay_kham))
        booked_times = [str(r['gio_kham']) for r in booked]

        # Tất cả khung giờ có thể
        all_slots = [
            '08:00:00', '08:30:00', '09:00:00', '09:30:00', '10:00:00', '10:30:00', '11:00:00',
            '13:30:00', '14:00:00', '14:30:00', '15:00:00', '15:30:00', '16:00:00', '16:30:00'
        ]

        # Lọc khung giờ còn trống
        available = [s for s in all_slots if s not in booked_times]
        return available

    @classmethod
    def thong_ke_hom_nay(cls, bac_si_id=None):
        """Thống kê lịch khám hôm nay"""
        where = "ngay_kham = CURDATE()"
        params = []
        if bac_si_id:
            where += " AND bac_si_id = %s"
            params.append(bac_si_id)

        total = db.get_one(f"SELECT COUNT(*) as total FROM lich_kham WHERE {where}", tuple(params))
        completed = db.get_one(f"SELECT COUNT(*) as total FROM lich_kham WHERE {where} AND trang_thai = 'hoan_thanh'", tuple(params))

        return {
            'tong': total['total'] if total else 0,
            'hoan_thanh': completed['total'] if completed else 0
        }

    @classmethod
    def thong_ke_theo_chuyen_khoa(cls):
        """Thống kê lịch khám theo chuyên khoa (cho admin dashboard)"""
        sql = """
            SELECT ck.ten_chuyen_khoa, COUNT(lk.id) as so_luong
            FROM lich_kham lk
            JOIN bac_si bs ON lk.bac_si_id = bs.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE lk.ngay_kham >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY ck.id, ck.ten_chuyen_khoa
            ORDER BY so_luong DESC
        """
        return db.query(sql)

    @classmethod
    def kiem_tra_trang_thai(cls, lich_ids):
        """Kiểm tra trạng thái nhiều lịch (cho realtime polling)"""
        if not lich_ids:
            return []
        placeholders = ','.join(['%s'] * len(lich_ids))
        sql = f"SELECT id, trang_thai FROM lich_kham WHERE id IN ({placeholders})"
        return db.query(sql, tuple(lich_ids))
