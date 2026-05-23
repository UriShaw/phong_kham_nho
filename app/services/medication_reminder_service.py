"""
Nhac uong thuoc qua Gmail SMTP va scheduler nen nhe.
Benh nhan chi dat nhac tu don thuoc bac si ke, khong tu nhap.
"""
from __future__ import annotations

import logging
import re
import smtplib
import socket
import threading
import time
from datetime import date, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from config import Config
from core.database import db
from app.services.utility_schema_service import UtilitySchemaService


logger = logging.getLogger(__name__)
_SCHEDULER_STARTED = False


class MedicationReminderService:
    """Quan ly lich nhac thuoc va gui email."""

    @staticmethod
    def list_reminders(benh_nhan_id: int | None) -> list[dict[str, Any]]:
        if not benh_nhan_id or not UtilitySchemaService.ensure():
            return []
        return db.query(
            """
            SELECT nt.*, ct.don_vi AS thuoc_don_vi
            FROM nhac_thuoc nt
            LEFT JOIN chi_tiet_don_thuoc ct ON nt.chi_tiet_don_thuoc_id = ct.id
            WHERE nt.benh_nhan_id = %s AND nt.trang_thai = 1
            ORDER BY nt.gio_nhac ASC
            """,
            (benh_nhan_id,),
        )

    @staticmethod
    def list_prescriptions(benh_nhan_id: int | None) -> list[dict[str, Any]]:
        """Lay tat ca don thuoc cua benh nhan kem chi tiet."""
        if not benh_nhan_id:
            return []
        try:
            don_list = db.query("""
                SELECT dt.id, dt.ghi_chu, dt.ngay_tao,
                       nd.ho_ten AS ten_bac_si, hs.chan_doan
                FROM don_thuoc dt
                JOIN bac_si bs ON dt.bac_si_id = bs.id
                JOIN nguoi_dung nd ON bs.nguoi_dung_id = nd.id
                JOIN ho_so_benh_an hs ON dt.ho_so_id = hs.id
                WHERE dt.benh_nhan_id = %s
                ORDER BY dt.ngay_tao DESC
                LIMIT 50
            """, (benh_nhan_id,))
            for dt in don_list:
                dt['chi_tiet'] = db.query(
                    "SELECT * FROM chi_tiet_don_thuoc WHERE don_thuoc_id = %s ORDER BY id",
                    (dt['id'],)
                )
            return don_list
        except Exception as exc:
            logger.warning("Loi lay don thuoc: %s", exc)
            return []

    @staticmethod
    def add_reminder_from_prescription(
        benh_nhan_id: int, user_email: str, payload: dict[str, Any]
    ) -> int:
        """Tao nhac thuoc tu chi tiet don thuoc bac si ke."""
        if not UtilitySchemaService.ensure():
            raise RuntimeError("Chua ket noi duoc database.")

        chi_tiet_id = payload.get("chi_tiet_don_thuoc_id")
        if not chi_tiet_id:
            raise ValueError("Vui long chon thuoc tu don thuoc bac si ke.")

        # Verify chi_tiet belongs to this patient
        ct = db.get_one("""
            SELECT ct.*, dt.benh_nhan_id, dt.id AS don_thuoc_id
            FROM chi_tiet_don_thuoc ct
            JOIN don_thuoc dt ON ct.don_thuoc_id = dt.id
            WHERE ct.id = %s
        """, (chi_tiet_id,))

        if not ct or ct.get('benh_nhan_id') != benh_nhan_id:
            raise ValueError("Khong tim thay thuoc trong don cua ban.")

        gio_nhac = str(payload.get("gio_nhac") or "").strip()
        MedicationReminderService._validate_time(gio_nhac)

        email_nhan = str(payload.get("email_nhan") or user_email or "").strip()
        MedicationReminderService._validate_email(email_nhan)

        return db.execute(
            """
            INSERT INTO nhac_thuoc
            (benh_nhan_id, ten_thuoc, gio_nhac, lieu_dung, ghi_chu, email_nhan,
             lap_lai, ngay_bat_dau, ngay_ket_thuc, trang_thai,
             don_thuoc_id, chi_tiet_don_thuoc_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s)
            """,
            (
                benh_nhan_id,
                ct.get('ten_thuoc', '')[:200],
                gio_nhac,
                ct.get('lieu_dung', '')[:255],
                str(payload.get("ghi_chu") or "")[:1000],
                email_nhan[:120],
                str(payload.get("lap_lai") or "hang_ngay"),
                payload.get("ngay_bat_dau") or None,
                payload.get("ngay_ket_thuc") or None,
                ct.get('don_thuoc_id'),
                chi_tiet_id,
            ),
        )

    @staticmethod
    def delete_reminder(reminder_id: int, benh_nhan_id: int | None) -> None:
        if not benh_nhan_id or not UtilitySchemaService.ensure():
            return
        db.execute(
            "UPDATE nhac_thuoc SET trang_thai = 0 WHERE id = %s AND benh_nhan_id = %s",
            (reminder_id, benh_nhan_id),
        )

    @staticmethod
    def send_test(reminder_id: int, benh_nhan_id: int | None) -> dict[str, Any]:
        if not benh_nhan_id or not UtilitySchemaService.ensure():
            raise ValueError("Khong tim thay ho so benh nhan.")
        reminder = db.get_one(
            "SELECT * FROM nhac_thuoc WHERE id = %s AND benh_nhan_id = %s",
            (reminder_id, benh_nhan_id),
        )
        if not reminder:
            raise ValueError("Khong tim thay loi nhac.")
        return MedicationReminderService._send_email(reminder)

    @staticmethod
    def start_scheduler_once(interval_seconds: int = 60) -> None:
        global _SCHEDULER_STARTED
        if _SCHEDULER_STARTED:
            return
        _SCHEDULER_STARTED = True
        thread = threading.Thread(
            target=MedicationReminderService._scheduler_loop,
            args=(interval_seconds,),
            name="medication-reminder-scheduler",
            daemon=True,
        )
        thread.start()
        logger.info("Medication reminder scheduler started.")

    @staticmethod
    def _scheduler_loop(interval_seconds: int) -> None:
        while True:
            try:
                MedicationReminderService.send_due_reminders()
            except Exception as exc:
                logger.exception("Loi scheduler nhac thuoc: %s", exc)
            time.sleep(interval_seconds)

    @staticmethod
    def send_due_reminders() -> int:
        if not UtilitySchemaService.ensure():
            return 0
        now_hm = datetime.now().strftime("%H:%M")
        today = date.today().isoformat()
        rows = db.query(
            """
            SELECT nt.*, nd.email AS default_email, nd.ho_ten
            FROM nhac_thuoc nt
            JOIN benh_nhan bn ON nt.benh_nhan_id = bn.id
            JOIN nguoi_dung nd ON bn.nguoi_dung_id = nd.id
            WHERE nt.trang_thai = 1
              AND DATE_FORMAT(nt.gio_nhac, '%%H:%%i') = %s
              AND (nt.lan_gui_cuoi IS NULL OR nt.lan_gui_cuoi < CURDATE())
              AND (nt.ngay_bat_dau IS NULL OR nt.ngay_bat_dau <= CURDATE())
              AND (nt.ngay_ket_thuc IS NULL OR nt.ngay_ket_thuc >= CURDATE())
            """,
            (now_hm,),
        )
        sent_count = 0
        for reminder in rows:
            reminder["email_nhan"] = reminder.get("email_nhan") or reminder.get("default_email")
            result = MedicationReminderService._send_email(reminder)
            if result.get("sent") or result.get("logged"):
                db.execute("UPDATE nhac_thuoc SET lan_gui_cuoi = %s WHERE id = %s", (today, reminder["id"]))
                sent_count += 1
        return sent_count

    @staticmethod
    def _validate_email(email: str) -> None:
        """Kiểm tra email hợp lệ: format + tồn tại domain MX record."""
        if not email:
            raise ValueError("Email nhận không được trống.")

        # Check format
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValueError(f"Email '{email}' không đúng định dạng.")

        # Check domain has MX records (email server exists)
        domain = email.split('@')[1]
        try:
            import dns.resolver
            mx_records = dns.resolver.resolve(domain, 'MX')
            if not mx_records:
                raise ValueError(f"Domain '{domain}' không có mail server.")
        except ImportError:
            # dns.resolver not available, fallback to socket check
            try:
                socket.getaddrinfo(domain, 25, socket.AF_INET)
            except socket.gaierror:
                raise ValueError(f"Domain '{domain}' không tồn tại. Kiểm tra lại email.")
        except Exception:
            # DNS check failed, try basic socket fallback
            try:
                socket.getaddrinfo(domain, 25, socket.AF_INET)
            except socket.gaierror:
                raise ValueError(f"Domain '{domain}' không tồn tại. Kiểm tra lại email.")

    @staticmethod
    def _send_email(reminder: dict[str, Any]) -> dict[str, Any]:
        email_to = reminder.get("email_nhan") or reminder.get("default_email")
        if not email_to:
            return {"sent": False, "message": "Lời nhắc chưa có email nhận."}

        # Validate email trước khi gửi
        try:
            MedicationReminderService._validate_email(email_to)
        except ValueError as ve:
            return {"sent": False, "message": str(ve)}

        subject = f"💊 MedPro - Nhắc uống thuốc: {reminder.get('ten_thuoc')}"
        html = MedicationReminderService._email_html(reminder)

        if not Config.SMTP_USER or not Config.SMTP_PASS:
            logger.info("[EMAIL LOG] %s -> %s", subject, email_to)
            return {
                "sent": False,
                "logged": True,
                "message": "Chưa cấu hình SMTP Gmail. Vui lòng cấu hình SMTP_USER và SMTP_PASS trong file .env",
            }

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"MedPro Health <{Config.SMTP_USER}>"
            msg["To"] = email_to
            msg.attach(MIMEText(html, "html", "utf-8"))

            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(Config.SMTP_USER, Config.SMTP_PASS)
                server.sendmail(Config.SMTP_USER, [email_to], msg.as_string())

            # Cập nhật lần gửi cuối
            if reminder.get('id'):
                try:
                    db.execute(
                        "UPDATE nhac_thuoc SET lan_gui_cuoi = NOW() WHERE id = %s",
                        (reminder['id'],)
                    )
                except Exception:
                    pass

            logger.info("✅ Đã gửi email nhắc thuốc tới %s", email_to)
            return {"sent": True, "message": f"Đã gửi email nhắc thuốc tới {email_to} thành công!"}

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP auth failed for %s", Config.SMTP_USER)
            return {
                "sent": False,
                "message": "Lỗi xác thực Gmail. Hãy dùng App Password (Mật khẩu ứng dụng) thay vì mật khẩu Gmail thường. "
                           "Vào https://myaccount.google.com/apppasswords để tạo."
            }
        except smtplib.SMTPRecipientsRefused:
            return {"sent": False, "message": f"Email '{email_to}' bị từ chối. Kiểm tra lại địa chỉ email."}
        except smtplib.SMTPException as exc:
            logger.exception("SMTP error: %s", exc)
            return {"sent": False, "message": f"Lỗi SMTP: {exc}"}
        except Exception as exc:
            logger.exception("Lỗi gửi email: %s", exc)
            return {"sent": False, "message": f"Lỗi gửi email: {exc}"}

    @staticmethod
    def _email_html(reminder: dict[str, Any]) -> str:
        gio = str(reminder.get("gio_nhac") or "")[:5]
        ten = reminder.get('ten_thuoc', '')
        lieu = reminder.get('lieu_dung') or 'Theo hướng dẫn của bác sĩ'
        ghi_chu = reminder.get('ghi_chu') or 'Uống với nước lọc, theo dõi phản ứng cơ thể.'
        ho_ten = reminder.get('ho_ten', 'Bạn')

        return f"""
        <!DOCTYPE html>
        <html><head><meta charset="utf-8"></head>
        <body style="margin:0;padding:0;background:#f0fdf4;font-family:'Segoe UI',Arial,sans-serif;">
            <div style="max-width:600px;margin:20px auto;background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
                <div style="background:linear-gradient(135deg,#059669 0%,#0d9488 50%,#0891b2 100%);padding:32px 28px;text-align:center;">
                    <div style="font-size:36px;margin-bottom:8px;">💊</div>
                    <h1 style="color:#ffffff;font-size:22px;margin:0 0 4px;">Đến giờ uống thuốc</h1>
                    <p style="color:#d1fae5;font-size:14px;margin:0;">MedPro Health Reminder System</p>
                </div>
                <div style="padding:28px;">
                    <p style="color:#334155;font-size:16px;line-height:1.6;margin:0 0 20px;">
                        Xin chào <strong>{ho_ten}</strong>,<br>
                        Đã đến giờ uống thuốc theo đơn bác sĩ kê:
                    </p>
                    <div style="background:linear-gradient(135deg,#ecfdf5,#f0fdfa);border-radius:16px;padding:20px;margin-bottom:20px;border-left:4px solid #059669;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
                            <span style="font-size:18px;font-weight:800;color:#0f172a;">{ten}</span>
                            <span style="background:#059669;color:#fff;padding:4px 14px;border-radius:20px;font-size:13px;font-weight:700;">{gio}</span>
                        </div>
                        <div style="color:#475569;font-size:14px;line-height:1.8;">
                            <div>📋 <strong>Liều dùng:</strong> {lieu}</div>
                            <div>📝 <strong>Ghi chú:</strong> {ghi_chu}</div>
                        </div>
                    </div>
                    <div style="background:#fffbeb;border-radius:12px;padding:14px 18px;margin-bottom:20px;border:1px solid #fde68a;">
                        <p style="color:#92400e;font-size:13px;margin:0;line-height:1.6;">
                            ⚠️ <strong>Lưu ý:</strong> Không tự ý thay đổi liều khi chưa hỏi bác sĩ. Nếu quên uống thuốc, hãy uống ngay khi nhớ ra (trừ khi gần giờ uống tiếp theo).
                        </p>
                    </div>
                    <div style="text-align:center;padding-top:12px;border-top:1px solid #e2e8f0;">
                        <p style="color:#94a3b8;font-size:12px;margin:0;">
                            Email tự động từ hệ thống MedPro · <a href="http://localhost:5000" style="color:#059669;text-decoration:none;">medpro.vn</a>
                        </p>
                    </div>
                </div>
            </div>
        </body></html>
        """

    @staticmethod
    def _validate_time(value: str) -> None:
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError:
            try:
                datetime.strptime(value, "%H:%M:%S")
            except ValueError as exc:
                raise ValueError("Gio nhac phai co dinh dang HH:MM.") from exc
