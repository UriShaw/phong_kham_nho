"""
Model Chuyên Khoa - Quản lý danh mục chuyên khoa
"""
from core.model import BaseModel


class ChuyenKhoaModel(BaseModel):
    """Model quản lý chuyên khoa"""
    table_name = 'chuyen_khoa'

    # Mapping icon cho chuyên khoa
    ICON_MAP = {
        'Tim mạch': 'fa-heartbeat',
        'Nội khoa': 'fa-stethoscope',
        'Nhi khoa': 'fa-baby',
        'Da liễu': 'fa-hand-holding-medical',
        'Thần kinh': 'fa-brain',
        'Tai mũi họng': 'fa-head-side-cough',
        'Mắt': 'fa-eye',
        'Răng hàm mặt': 'fa-tooth',
        'Xương khớp': 'fa-bone',
        'Sản phụ khoa': 'fa-female',
    }

    @classmethod
    def lay_tat_ca_hoat_dong(cls):
        """Lấy tất cả chuyên khoa đang hoạt động"""
        from core.database import db
        result = db.query(
            "SELECT * FROM chuyen_khoa WHERE trang_thai = 1 ORDER BY ten_chuyen_khoa"
        )
        # Thêm icon
        for ck in result:
            ck['icon'] = cls.ICON_MAP.get(ck.get('ten_chuyen_khoa', ''), 'fa-hospital')
        return result
