"""
Model Bác Sĩ - Quản lý thông tin bác sĩ
"""
from core.model import BaseModel
from core.database import db


class BacSiModel(BaseModel):
    """Model cho bảng bac_si"""

    table_name = 'bac_si'

    @classmethod
    def lay_theo_nguoi_dung(cls, nguoi_dung_id):
        """Lấy thông tin bác sĩ theo nguoi_dung_id"""
        return cls.find_by('nguoi_dung_id', nguoi_dung_id)

    @classmethod
    def lay_chi_tiet(cls, bac_si_id):
        """Lấy thông tin chi tiết bác sĩ kèm chuyên khoa"""
        sql = """
            SELECT bs.*, nd.ho_ten, nd.email, nd.so_dien_thoai, nd.avatar,
                   ck.ten_chuyen_khoa, ck.icon as ck_icon
            FROM bac_si bs
            JOIN nguoi_dung nd ON bs.nguoi_dung_id = nd.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE bs.id = %s AND bs.trang_thai_duyet = 'da_duyet'
        """
        return db.get_one(sql, (bac_si_id,))

    @classmethod
    def tim_bac_si(cls, chuyen_khoa_id=None, search='', benh_vien='',
                   gia_tu=None, gia_den=None, sap_xep='danh_gia',
                   page=1, per_page=10, matched_specialties=None):
        """
        Tìm kiếm bác sĩ với bộ lọc nâng cao.
        matched_specialties: danh sách tên chuyên khoa khớp từ triệu chứng (symptom-based search)
        """
        where_parts = ["bs.trang_thai_duyet = 'da_duyet'"]
        params = []

        if chuyen_khoa_id:
            where_parts.append("bs.chuyen_khoa_id = %s")
            params.append(chuyen_khoa_id)

        if search:
            # Tìm theo tên bác sĩ, chuyên khoa, bệnh viện
            search_conditions = ["nd.ho_ten LIKE %s", "ck.ten_chuyen_khoa LIKE %s", "bs.benh_vien LIKE %s"]
            search_params = [f"%{search}%"] * 3

            # Nếu có chuyên khoa khớp từ triệu chứng, thêm điều kiện tìm theo tên chuyên khoa
            if matched_specialties:
                for spec_name in matched_specialties:
                    search_conditions.append("ck.ten_chuyen_khoa LIKE %s")
                    search_params.append(f"%{spec_name}%")

            where_parts.append(f"({' OR '.join(search_conditions)})")
            params.extend(search_params)

        if benh_vien:
            where_parts.append("bs.benh_vien LIKE %s")
            params.append(f"%{benh_vien}%")

        if gia_tu:
            where_parts.append("bs.gia_kham >= %s")
            params.append(gia_tu)

        if gia_den:
            where_parts.append("bs.gia_kham <= %s")
            params.append(gia_den)

        where = " AND ".join(where_parts)

        # Sắp xếp
        order_map = {
            'danh_gia': 'bs.danh_gia DESC',
            'gia_thap': 'bs.gia_kham ASC',
            'gia_cao': 'bs.gia_kham DESC',
            'kinh_nghiem': 'bs.kinh_nghiem DESC'
        }
        order = order_map.get(sap_xep, 'bs.danh_gia DESC')

        # Đếm tổng
        count_sql = f"""
            SELECT COUNT(*) as total FROM bac_si bs
            JOIN nguoi_dung nd ON bs.nguoi_dung_id = nd.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE {where}
        """
        total = db.get_one(count_sql, tuple(params))['total']

        # Lấy danh sách
        offset = (page - 1) * per_page
        sql = f"""
            SELECT bs.*, nd.ho_ten, nd.avatar, nd.email,
                   ck.ten_chuyen_khoa, ck.icon as ck_icon,
                   CONCAT(bs.hoc_vi, ' ', nd.ho_ten) as ten_hien_thi
            FROM bac_si bs
            JOIN nguoi_dung nd ON bs.nguoi_dung_id = nd.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE {where}
            ORDER BY {order}
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
    def bac_si_noi_bat(cls, limit=6):
        """Lấy bác sĩ nổi bật (đánh giá cao nhất)"""
        sql = """
            SELECT bs.*, nd.ho_ten, nd.avatar,
                   ck.ten_chuyen_khoa,
                   CONCAT(bs.hoc_vi, ' ', nd.ho_ten) as ten_hien_thi
            FROM bac_si bs
            JOIN nguoi_dung nd ON bs.nguoi_dung_id = nd.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE bs.trang_thai_duyet = 'da_duyet'
            ORDER BY bs.danh_gia DESC, bs.so_danh_gia DESC
            LIMIT %s
        """
        return db.query(sql, (limit,))

    @classmethod
    def cho_duyet(cls):
        """Lấy danh sách bác sĩ chờ duyệt (admin)"""
        sql = """
            SELECT bs.*, nd.ho_ten, nd.avatar, ck.ten_chuyen_khoa
            FROM bac_si bs
            JOIN nguoi_dung nd ON bs.nguoi_dung_id = nd.id
            JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
            WHERE bs.trang_thai_duyet = 'cho_duyet'
            ORDER BY bs.id DESC
        """
        return db.query(sql)

    @classmethod
    def duyet_bac_si(cls, bac_si_id, trang_thai):
        """Duyệt hoặc từ chối bác sĩ"""
        return cls.update(bac_si_id, {'trang_thai_duyet': trang_thai})
