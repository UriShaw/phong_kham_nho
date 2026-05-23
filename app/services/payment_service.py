"""
Payment Service - Xử lý thanh toán QR MB Bank
"""
from config import Config
from app.models.thanh_toan_model import ThanhToanModel
from app.models.lich_kham_model import LichKhamModel
from app.models.thong_bao_model import ThongBaoModel


class PaymentService:
    """Service thanh toán QR"""

    @staticmethod
    def tao_qr_url(so_tien, noi_dung):
        """
        Tạo URL mã QR thanh toán từ VietQR API
        Format: https://img.vietqr.io/image/{BANK_ID}-{STK}-compact2.png?amount={}&addInfo={}&accountName={}
        """
        bank_id = Config.MBBANK_BANK_ID
        stk = Config.MBBANK_STK
        ten = Config.MBBANK_TEN

        qr_url = (
            f"https://img.vietqr.io/image/{bank_id}-{stk}-compact2.png"
            f"?amount={int(so_tien)}"
            f"&addInfo={noi_dung}"
            f"&accountName={ten}"
        )
        return qr_url

    @staticmethod
    def lay_thong_tin_thanh_toan(lich_kham_id):
        """Lấy thông tin thanh toán cho 1 lịch khám"""
        thanh_toan = ThanhToanModel.lay_theo_lich(lich_kham_id)
        lich = LichKhamModel.chi_tiet_lich(lich_kham_id)

        if not thanh_toan or not lich:
            return None

        qr_url = PaymentService.tao_qr_url(thanh_toan['so_tien'], thanh_toan['noi_dung_ck'])

        return {
            'thanh_toan': thanh_toan,
            'lich_kham': lich,
            'qr_url': qr_url,
            'bank_info': {
                'ngan_hang': 'MB Bank',
                'stk': Config.MBBANK_STK,
                'chu_tai_khoan': Config.MBBANK_TEN,
                'noi_dung_ck': thanh_toan['noi_dung_ck']
            }
        }

    @staticmethod
    def xac_nhan_da_chuyen(lich_kham_id, benh_nhan_id):
        """
        Bệnh nhân xác nhận đã chuyển khoản
        (Trong thực tế sẽ check webhook ngân hàng)
        """
        thanh_toan = ThanhToanModel.lay_theo_lich(lich_kham_id)
        if not thanh_toan:
            return False, 'Không tìm thấy giao dịch'

        if thanh_toan['benh_nhan_id'] != benh_nhan_id:
            return False, 'Bạn không có quyền xác nhận giao dịch này'

        if thanh_toan['trang_thai'] != 'cho_thanh_toan':
            return False, 'Giao dịch đã được xử lý'

        # Xác nhận thanh toán
        ThanhToanModel.xac_nhan_thanh_toan(thanh_toan['id'])

        # Cập nhật trạng thái lịch khám sang đã xác nhận
        LichKhamModel.cap_nhat_trang_thai(lich_kham_id, 'da_xac_nhan')

        # Gửi thông báo
        lich = LichKhamModel.chi_tiet_lich(lich_kham_id)
        if lich:
            # Lấy nguoi_dung_id từ bệnh nhân
            from app.models.benh_nhan_model import BenhNhanModel
            bn = BenhNhanModel.get_by_id(benh_nhan_id)
            if bn:
                ThongBaoModel.gui_thong_bao(
                    bn['nguoi_dung_id'],
                    'Thanh toán thành công',
                    f'Thanh toán {int(thanh_toan["so_tien"]):,}d da duoc xac nhan.',
                    loai='thanh_toan'
                )

        return True, 'Xác nhận thanh toán thành công!'
