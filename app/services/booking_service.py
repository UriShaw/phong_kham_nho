"""
Booking Service - Xử lý đặt lịch khám
"""
from app.models.lich_kham_model import LichKhamModel
from app.models.bac_si_model import BacSiModel
from app.models.thanh_toan_model import ThanhToanModel
from app.models.thong_bao_model import ThongBaoModel


class BookingService:
    """Service đặt lịch khám bệnh"""

    @staticmethod
    def dat_lich(benh_nhan_id, bac_si_id, ngay_kham, gio_kham, ly_do=''):
        """
        Đặt lịch khám (3 bước: chọn BS → chọn giờ → xác nhận)
        Trả về: (success, message, data)
        """
        # Kiểm tra bác sĩ tồn tại
        bac_si = BacSiModel.lay_chi_tiet(bac_si_id)
        if not bac_si:
            return False, 'Không tìm thấy bác sĩ', None

        # Kiểm tra slot trống
        slots = LichKhamModel.lay_slot_trong(bac_si_id, ngay_kham)
        # Chuẩn hóa giờ khám về HH:MM:SS
        gio_check = gio_kham if len(gio_kham) == 8 else gio_kham + ':00'
        if gio_check not in slots:
            return False, 'Khung giờ này đã có người đặt, vui lòng chọn giờ khác', None

        # Tự động phân phòng
        phong_kham = BookingService._phan_phong(bac_si_id)

        # Tạo lịch khám
        lich_id = LichKhamModel.tao_lich(
            benh_nhan_id=benh_nhan_id,
            bac_si_id=bac_si_id,
            ngay_kham=ngay_kham,
            gio_kham=gio_kham,
            ly_do=ly_do,
            phong_kham=phong_kham
        )

        if not lich_id:
            return False, 'Không thể đặt lịch, khung giờ đã bị trùng', None

        # Tạo giao dịch thanh toán
        ThanhToanModel.tao_giao_dich(lich_id, benh_nhan_id, bac_si['gia_kham'])

        # Gửi thông báo cho bác sĩ
        ThongBaoModel.gui_thong_bao(
            bac_si['nguoi_dung_id'],
            'Lịch khám mới',
            f'Bạn có lịch khám mới vào {ngay_kham} lúc {gio_kham}',
            loai='lich_kham',
            link=f'/bac-si/lich-kham'
        )

        return True, 'Đặt lịch thành công!', {
            'lich_kham_id': lich_id,
            'gia_kham': bac_si['gia_kham']
        }

    @staticmethod
    def _phan_phong(bac_si_id):
        """Tự động phân phòng khám dựa trên bác sĩ"""
        rooms = {
            1: 'Phòng 102, Tầng 1',
            2: 'Phòng 205, Tầng 2',
            3: 'Phòng 301, Tầng 3',
            4: 'Phòng 103, Tầng 1',
            5: 'Phòng 402, Tầng 4'
        }
        return rooms.get(bac_si_id, f'Phòng {100 + bac_si_id}, Tầng 1')

    @staticmethod
    def lay_slots(bac_si_id, ngay_kham):
        """Lấy khung giờ trống cho đặt lịch"""
        return LichKhamModel.lay_slot_trong(bac_si_id, ngay_kham)

    @staticmethod
    def huy_lich(lich_id, benh_nhan_id):
        """Hủy lịch khám"""
        lich = LichKhamModel.chi_tiet_lich(lich_id)
        if not lich:
            return False, 'Không tìm thấy lịch khám'

        if lich['benh_nhan_id'] != benh_nhan_id:
            return False, 'Bạn không có quyền hủy lịch này'

        if lich['trang_thai'] in ('hoan_thanh', 'da_huy'):
            return False, 'Không thể hủy lịch đã hoàn thành hoặc đã hủy'

        LichKhamModel.cap_nhat_trang_thai(lich_id, 'da_huy')

        # Hủy thanh toán
        thanh_toan = ThanhToanModel.lay_theo_lich(lich_id)
        if thanh_toan and thanh_toan['trang_thai'] == 'cho_thanh_toan':
            ThanhToanModel.update(thanh_toan['id'], {'trang_thai': 'da_huy'})

        return True, 'Đã hủy lịch khám'
