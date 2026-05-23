"""
Notification Service - Thông báo, nhắc lịch, email
"""
from app.models.thong_bao_model import ThongBaoModel
from app.models.lich_kham_model import LichKhamModel
from core.database import db


class NotificationService:
    """Service quản lý thông báo"""

    @staticmethod
    def nhac_lich_kham():
        """
        Kiểm tra và gửi nhắc nhở lịch khám sắp tới (24h trước)
        Chạy định kỳ hoặc khi user truy cập
        """
        # Lịch khám trong 24h tới chưa được nhắc
        sql = """
            SELECT lk.id, lk.ngay_kham, lk.gio_kham, lk.benh_nhan_id,
                   bn.nguoi_dung_id,
                   nd_bs.ho_ten as ten_bac_si
            FROM lich_kham lk
            JOIN benh_nhan bn ON lk.benh_nhan_id = bn.id
            JOIN bac_si bs ON lk.bac_si_id = bs.id
            JOIN nguoi_dung nd_bs ON bs.nguoi_dung_id = nd_bs.id
            WHERE lk.ngay_kham = CURDATE() + INTERVAL 1 DAY
            AND lk.trang_thai IN ('cho_xac_nhan', 'da_xac_nhan')
            AND lk.id NOT IN (
                SELECT CAST(SUBSTRING_INDEX(link, '/', -1) AS UNSIGNED)
                FROM thong_bao WHERE loai = 'nhac_nho'
                AND ngay_tao >= CURDATE()
            )
        """
        lich_list = db.query(sql)

        for lich in lich_list:
            ThongBaoModel.gui_thong_bao(
                lich['nguoi_dung_id'],
                '⏰ Nhắc lịch khám ngày mai',
                f'Bạn có lịch khám với {lich["ten_bac_si"]} vào lúc {lich["gio_kham"]} ngày mai.',
                loai='nhac_nho',
                link=f'/lich-kham/{lich["id"]}'
            )

        return len(lich_list)

    @staticmethod
    def gui_email_nhac(email, ho_ten, ngay_kham, gio_kham, ten_bac_si):
        """
        Gửi email nhắc lịch (cần cấu hình SMTP)
        Hiện tại chỉ log ra console
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from config import Config

            if not Config.SMTP_USER:
                print(f"[EMAIL LOG] Nhac lich -> {email}: Kham voi {ten_bac_si} luc {gio_kham} ngay {ngay_kham}")
                return True

            msg = MIMEText(f"""
            Xin chào {ho_ten},

            Bạn có lịch khám bệnh:
            - Bác sĩ: {ten_bac_si}
            - Thời gian: {gio_kham} ngày {ngay_kham}

            Vui lòng đến đúng giờ.

            Trân trọng,
            Hệ thống MedPro
            """)
            msg['Subject'] = f'[MedPro] Nhắc lịch khám ngày {ngay_kham}'
            msg['From'] = Config.SMTP_USER
            msg['To'] = email

            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USER, Config.SMTP_PASS)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"[ERROR] Loi gui email: {e}")
            return False
