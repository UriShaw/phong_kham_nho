"""
Model Hồ Sơ Bệnh Án - Quản lý kết quả khám
"""
from core.model import BaseModel
from core.database import db


class HoSoModel(BaseModel):
    """Model cho bảng ho_so_benh_an"""

    table_name = 'ho_so_benh_an'

    @classmethod
    def tao_ho_so(cls, lich_kham_id, benh_nhan_id, bac_si_id, data):
        """Tạo hồ sơ bệnh án mới"""
        ho_so_data = {
            'lich_kham_id': lich_kham_id,
            'benh_nhan_id': benh_nhan_id,
            'bac_si_id': bac_si_id,
            'chan_doan': data.get('chan_doan', ''),
            'ghi_chu_lam_sang': data.get('ghi_chu_lam_sang', ''),
            'chi_dinh_can_lam_sang': data.get('chi_dinh_can_lam_sang', ''),
            'huyet_ap': data.get('huyet_ap', ''),
            'nhip_tim': data.get('nhip_tim'),
            'can_nang': data.get('can_nang'),
            'nhiet_do': data.get('nhiet_do'),
            'hen_tai_kham': data.get('hen_tai_kham'),
        }
        return cls.create(ho_so_data)

    @classmethod
    def cap_nhat_ho_so(cls, ho_so_id, data):
        """Cập nhật hồ sơ bệnh án"""
        allowed = [
            'chan_doan', 'ghi_chu_lam_sang', 'chi_dinh_can_lam_sang',
            'huyet_ap', 'nhip_tim', 'can_nang', 'nhiet_do', 'hen_tai_kham'
        ]
        update_data = {k: v for k, v in data.items() if k in allowed}
        if update_data:
            return cls.update(ho_so_id, update_data)
        return None

    @classmethod
    def xoa_ho_so(cls, ho_so_id):
        """Xóa hồ sơ bệnh án và đơn thuốc liên quan"""
        # Xóa chi tiết đơn thuốc
        db.execute("""
            DELETE ct FROM chi_tiet_don_thuoc ct
            JOIN don_thuoc dt ON ct.don_thuoc_id = dt.id
            WHERE dt.ho_so_id = %s
        """, (ho_so_id,))
        # Xóa đơn thuốc
        db.execute("DELETE FROM don_thuoc WHERE ho_so_id = %s", (ho_so_id,))
        # Xóa hồ sơ
        return cls.delete(ho_so_id)

    @classmethod
    def timeline_benh_nhan(cls, benh_nhan_id):
        """Lấy lịch sử khám dạng timeline"""
        sql = """
            SELECT hs.*, lk.ngay_kham, lk.gio_kham, lk.ly_do, lk.trang_thai,
                   nd.ho_ten as ten_bac_si, bs.hoc_vi, ck.ten_chuyen_khoa,
                   CONCAT(bs.hoc_vi, ' ', nd.ho_ten) as ten_hien_thi_bs
            FROM ho_so_benh_an hs
            JOIN lich_kham lk ON hs.lich_kham_id = lk.id
            JOIN bac_si bs ON hs.bac_si_id = bs.id
            JOIN nguoi_dung nd ON bs.nguoi_dung_id = nd.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE hs.benh_nhan_id = %s
            ORDER BY lk.ngay_kham DESC
        """
        return db.query(sql, (benh_nhan_id,))

    @classmethod
    def lay_theo_lich(cls, lich_kham_id):
        """Lấy hồ sơ theo lịch khám"""
        return cls.find_by('lich_kham_id', lich_kham_id)

    @classmethod
    def lay_chi_tiet_day_du(cls, ho_so_id):
        """Lấy chi tiết hồ sơ bệnh án đầy đủ kèm bệnh nhân, bác sĩ"""
        return db.get_one("""
            SELECT hs.*, lk.ngay_kham, lk.gio_kham, lk.ly_do, lk.trieu_chung, lk.phong_kham,
                   nd_bs.ho_ten AS ten_bac_si, bs.hoc_vi, ck.ten_chuyen_khoa,
                   CONCAT(bs.hoc_vi, ' ', nd_bs.ho_ten) AS ten_hien_thi_bs,
                   nd_bn.ho_ten AS ten_benh_nhan, bn.ma_benh_nhan,
                   bn.gioi_tinh, bn.ngay_sinh, nd_bn.email AS email_bn,
                   nd_bn.so_dien_thoai AS sdt_bn,
                   bn.nhom_mau, bn.tien_su_benh, bn.di_ung,
                   bn.bao_hiem_y_te, bn.dia_chi,
                   TIMESTAMPDIFF(YEAR, bn.ngay_sinh, CURDATE()) AS tuoi_bn
            FROM ho_so_benh_an hs
            JOIN lich_kham lk ON hs.lich_kham_id = lk.id
            JOIN bac_si bs ON hs.bac_si_id = bs.id
            JOIN nguoi_dung nd_bs ON bs.nguoi_dung_id = nd_bs.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            JOIN benh_nhan bn ON hs.benh_nhan_id = bn.id
            JOIN nguoi_dung nd_bn ON bn.nguoi_dung_id = nd_bn.id
            WHERE hs.id = %s
        """, (ho_so_id,))

    @classmethod
    def ho_so_cua_bac_si(cls, bac_si_id, search='', page=1, per_page=15):
        """Lấy danh sách hồ sơ bệnh án mà bác sĩ đã khám (phân trang, tìm kiếm)"""
        where = "hs.bac_si_id = %s"
        params = [bac_si_id]

        if search:
            where += " AND (nd_bn.ho_ten LIKE %s OR bn.ma_benh_nhan LIKE %s OR hs.chan_doan LIKE %s)"
            params.extend([f"%{search}%"] * 3)

        count_sql = f"""
            SELECT COUNT(*) as total
            FROM ho_so_benh_an hs
            JOIN benh_nhan bn ON hs.benh_nhan_id = bn.id
            JOIN nguoi_dung nd_bn ON bn.nguoi_dung_id = nd_bn.id
            WHERE {where}
        """
        total = db.get_one(count_sql, tuple(params))['total']

        offset = (page - 1) * per_page
        sql = f"""
            SELECT hs.*, lk.ngay_kham, lk.gio_kham,
                   nd_bn.ho_ten AS ten_benh_nhan, bn.ma_benh_nhan,
                   bn.gioi_tinh, bn.ngay_sinh, nd_bn.email AS email_bn,
                   nd_bn.so_dien_thoai AS sdt_bn,
                   ck.ten_chuyen_khoa,
                   TIMESTAMPDIFF(YEAR, bn.ngay_sinh, CURDATE()) AS tuoi_bn
            FROM ho_so_benh_an hs
            JOIN lich_kham lk ON hs.lich_kham_id = lk.id
            JOIN bac_si bs ON hs.bac_si_id = bs.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            JOIN benh_nhan bn ON hs.benh_nhan_id = bn.id
            JOIN nguoi_dung nd_bn ON bn.nguoi_dung_id = nd_bn.id
            WHERE {where}
            ORDER BY lk.ngay_kham DESC
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

    @classmethod
    def benh_nhan_cua_bac_si(cls, bac_si_id, search=''):
        """Lấy danh sách bệnh nhân đã/đang khám của bác sĩ (unique)"""
        where = "lk.bac_si_id = %s AND lk.trang_thai IN ('da_xac_nhan','dang_kham','hoan_thanh')"
        params = [bac_si_id]
        if search:
            where += " AND (nd.ho_ten LIKE %s OR bn.ma_benh_nhan LIKE %s)"
            params.extend([f"%{search}%"] * 2)

        sql = f"""
            SELECT DISTINCT bn.id, bn.ma_benh_nhan, bn.ngay_sinh, bn.gioi_tinh,
                   bn.nhom_mau, bn.tien_su_benh, bn.di_ung, bn.bao_hiem_y_te,
                   bn.chieu_cao, bn.can_nang, bn.huyet_ap, bn.nhip_tim,
                   nd.ho_ten, nd.email, nd.so_dien_thoai, nd.avatar,
                   bn.dia_chi,
                   TIMESTAMPDIFF(YEAR, bn.ngay_sinh, CURDATE()) AS tuoi,
                   (SELECT COUNT(*) FROM ho_so_benh_an hs2
                    WHERE hs2.benh_nhan_id = bn.id AND hs2.bac_si_id = %s) AS so_lan_kham
            FROM lich_kham lk
            JOIN benh_nhan bn ON lk.benh_nhan_id = bn.id
            JOIN nguoi_dung nd ON bn.nguoi_dung_id = nd.id
            WHERE {where}
            ORDER BY nd.ho_ten ASC
        """
        params.append(bac_si_id)
        return db.query(sql, tuple(params))

    @classmethod
    def thong_ke_bac_si(cls, bac_si_id):
        """Thống kê cho bác sĩ"""
        tong_ho_so = cls.count("bac_si_id = %s", (bac_si_id,))
        tong_bn = db.get_one("""
            SELECT COUNT(DISTINCT benh_nhan_id) AS total
            FROM ho_so_benh_an WHERE bac_si_id = %s
        """, (bac_si_id,))
        return {
            'tong_ho_so': tong_ho_so,
            'tong_benh_nhan': tong_bn['total'] if tong_bn else 0,
        }
