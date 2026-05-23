"""
Tu khoi tao cac bang phu tro cho module Tien ich suc khoe.

Project goc da co MySQL va schema chinh. Service nay giup cac API moi
chay duoc tren database cu ma chua can nguoi dung import lai toan bo schema.
"""
from __future__ import annotations

import logging

from core.database import db


logger = logging.getLogger(__name__)
_SCHEMA_READY = False


class UtilitySchemaService:
    """Dam bao cac bang/cot can thiet ton tai truoc khi ghi du lieu."""

    @staticmethod
    def ensure() -> bool:
        global _SCHEMA_READY
        if _SCHEMA_READY:
            return True

        conn = db.get_connection()
        if not conn:
            logger.warning("Khong co ket noi database de tao schema tien ich.")
            return False

        try:
            cursor = conn.cursor()
            for statement in _CREATE_TABLES:
                cursor.execute(statement)
            conn.commit()

            for table, columns in _OPTIONAL_COLUMNS.items():
                for column_name, ddl in columns.items():
                    if not UtilitySchemaService._column_exists(cursor, table, column_name):
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")
            conn.commit()
            cursor.close()
            _SCHEMA_READY = True
            return True
        except Exception as exc:  # pragma: no cover - phu thuoc MySQL local
            logger.exception("Loi tao schema tien ich: %s", exc)
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            conn.close()

    @staticmethod
    def _column_exists(cursor, table: str, column: str) -> bool:
        cursor.execute(f"SHOW COLUMNS FROM {table} LIKE %s", (column,))
        return cursor.fetchone() is not None


_CREATE_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS suc_khoe_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        benh_nhan_id INT NOT NULL,
        ngay DATE NOT NULL,
        nhip_tim INT DEFAULT NULL,
        huyet_ap_tam_thu INT DEFAULT NULL,
        huyet_ap_tam_truong INT DEFAULT NULL,
        huyet_ap VARCHAR(10) DEFAULT NULL,
        giac_ngu DECIMAL(4,1) DEFAULT NULL,
        can_nang DECIMAL(5,1) DEFAULT NULL,
        tam_trang INT DEFAULT 3,
        muc_nang_luong INT DEFAULT 3,
        nuoc_uong INT DEFAULT 0,
        buoc_di INT DEFAULT 0,
        ghi_chu TEXT,
        ngay_tao DATETIME DEFAULT CURRENT_TIMESTAMP,
        ngay_cap_nhat DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uq_suc_khoe_ngay (benh_nhan_id, ngay),
        INDEX idx_suc_khoe_benh_nhan (benh_nhan_id),
        INDEX idx_suc_khoe_ngay (ngay)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS nhat_ky_tam_trang (
        id INT AUTO_INCREMENT PRIMARY KEY,
        benh_nhan_id INT NOT NULL,
        ngay DATE NOT NULL,
        muc_tam_trang TINYINT NOT NULL DEFAULT 3 COMMENT '1-5: rat buon -> rat vui',
        noi_dung TEXT,
        hoat_dong VARCHAR(500),
        giac_ngu_diem TINYINT DEFAULT 3,
        nang_luong_diem TINYINT DEFAULT 3,
        ai_phan_tich VARCHAR(100),
        ai_goi_y TEXT,
        ngay_tao DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uq_mood_ngay (benh_nhan_id, ngay),
        INDEX idx_mood_benh_nhan (benh_nhan_id),
        INDEX idx_mood_ngay (ngay)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_chan_doan_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        benh_nhan_id INT DEFAULT NULL,
        nguoi_dung_id INT DEFAULT NULL,
        trieu_chung_text TEXT,
        trieu_chung_json JSON,
        ket_qua_json JSON,
        muc_nguy_co VARCHAR(30),
        ngay_tao DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_ai_cd_benh_nhan (benh_nhan_id),
        INDEX idx_ai_cd_nguoi_dung (nguoi_dung_id),
        INDEX idx_ai_cd_ngay (ngay_tao)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS tu_van_tin_nhan (
        id INT AUTO_INCREMENT PRIMARY KEY,
        lich_kham_id INT DEFAULT NULL,
        benh_nhan_id INT DEFAULT NULL,
        bac_si_id INT DEFAULT NULL,
        nguoi_gui ENUM('bac_si', 'benh_nhan', 'ai') DEFAULT 'bac_si',
        noi_dung TEXT NOT NULL,
        ngay_tao DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_tv_lich (lich_kham_id),
        INDEX idx_tv_benh_nhan (benh_nhan_id),
        INDEX idx_tv_bac_si (bac_si_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
]


_OPTIONAL_COLUMNS = {
    "suc_khoe_log": {
        "nhip_tim": "nhip_tim INT DEFAULT NULL",
        "huyet_ap_tam_thu": "huyet_ap_tam_thu INT DEFAULT NULL",
        "huyet_ap_tam_truong": "huyet_ap_tam_truong INT DEFAULT NULL",
        "huyet_ap": "huyet_ap VARCHAR(10) DEFAULT NULL",
        "can_nang": "can_nang DECIMAL(5,1) DEFAULT NULL",
        "ngay_cap_nhat": "ngay_cap_nhat DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
    },
    "nhat_ky_tam_trang": {
        "hoat_dong": "hoat_dong VARCHAR(500)",
        "giac_ngu_diem": "giac_ngu_diem TINYINT DEFAULT 3",
        "nang_luong_diem": "nang_luong_diem TINYINT DEFAULT 3",
        "ai_phan_tich": "ai_phan_tich VARCHAR(100)",
        "ai_goi_y": "ai_goi_y TEXT",
    },
}

