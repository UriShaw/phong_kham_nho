"""
Tin nhan tu van co ban cho dashboard bac si.
"""
from __future__ import annotations

from typing import Any

from core.database import db
from app.services.utility_schema_service import UtilitySchemaService


class ConsultationService:
    """Luu va lay tin nhan tu van gan voi lich kham."""

    @staticmethod
    def list_messages(lich_kham_id: int | None) -> list[dict[str, Any]]:
        if not lich_kham_id or not UtilitySchemaService.ensure():
            return []
        return db.query(
            """
            SELECT *
            FROM tu_van_tin_nhan
            WHERE lich_kham_id = %s
            ORDER BY ngay_tao ASC
            LIMIT 50
            """,
            (lich_kham_id,),
        )

    @staticmethod
    def add_message(
        lich_kham_id: int | None,
        benh_nhan_id: int | None,
        bac_si_id: int | None,
        sender: str,
        content: str,
    ) -> dict[str, Any]:
        if not UtilitySchemaService.ensure():
            raise RuntimeError("Chua ket noi duoc database.")
        content = str(content or "").strip()
        if not content:
            raise ValueError("Noi dung tu van khong duoc de trong.")
        if sender not in {"bac_si", "benh_nhan", "ai"}:
            sender = "bac_si"

        message_id = db.execute(
            """
            INSERT INTO tu_van_tin_nhan
            (lich_kham_id, benh_nhan_id, bac_si_id, nguoi_gui, noi_dung)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (lich_kham_id, benh_nhan_id, bac_si_id, sender, content[:2000]),
        )
        return {
            "id": message_id,
            "lich_kham_id": lich_kham_id,
            "benh_nhan_id": benh_nhan_id,
            "bac_si_id": bac_si_id,
            "nguoi_gui": sender,
            "noi_dung": content[:2000],
        }

