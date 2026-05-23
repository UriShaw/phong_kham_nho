"""
Theo doi suc khoe hang ngay va phan tich xu huong rule-based.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from statistics import mean
from typing import Any

from core.database import db
from app.services.utility_schema_service import UtilitySchemaService


logger = logging.getLogger(__name__)


class HealthTrackingService:
    """CRUD log suc khoe va phat hien bat thuong co ban."""

    @staticmethod
    def list_logs(benh_nhan_id: int | None, days: int = 30) -> list[dict[str, Any]]:
        if not benh_nhan_id or not UtilitySchemaService.ensure():
            return []
        return db.query(
            """
            SELECT *
            FROM suc_khoe_log
            WHERE benh_nhan_id = %s
            ORDER BY ngay DESC
            LIMIT %s
            """,
            (benh_nhan_id, days),
        )

    @staticmethod
    def save_daily_log(benh_nhan_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        if not UtilitySchemaService.ensure():
            raise RuntimeError("Chua ket noi duoc database.")

        values = HealthTrackingService._clean_payload(payload)
        ngay = values.pop("ngay")
        existing = db.get_one(
            "SELECT id FROM suc_khoe_log WHERE benh_nhan_id = %s AND ngay = %s",
            (benh_nhan_id, ngay),
        )

        params = (
            values["nhip_tim"],
            values["huyet_ap_tam_thu"],
            values["huyet_ap_tam_truong"],
            values["huyet_ap"],
            values["giac_ngu"],
            values["can_nang"],
            values["tam_trang"],
            values["muc_nang_luong"],
            values["nuoc_uong"],
            values["buoc_di"],
            values["ghi_chu"],
        )
        if existing:
            db.execute(
                """
                UPDATE suc_khoe_log
                SET nhip_tim = %s,
                    huyet_ap_tam_thu = %s,
                    huyet_ap_tam_truong = %s,
                    huyet_ap = %s,
                    giac_ngu = %s,
                    can_nang = %s,
                    tam_trang = %s,
                    muc_nang_luong = %s,
                    nuoc_uong = %s,
                    buoc_di = %s,
                    ghi_chu = %s
                WHERE id = %s
                """,
                params + (existing["id"],),
            )
            action = "updated"
        else:
            db.execute(
                """
                INSERT INTO suc_khoe_log
                (benh_nhan_id, ngay, nhip_tim, huyet_ap_tam_thu, huyet_ap_tam_truong,
                 huyet_ap, giac_ngu, can_nang, tam_trang, muc_nang_luong, nuoc_uong,
                 buoc_di, ghi_chu)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (benh_nhan_id, ngay) + params,
            )
            action = "created"

        logs = HealthTrackingService.list_logs(benh_nhan_id, days=30)
        return {
            "action": action,
            "analysis": HealthTrackingService.analyze(logs),
            "latest": logs[0] if logs else None,
        }

    @staticmethod
    def analyze(logs: list[dict[str, Any]]) -> dict[str, Any]:
        if not logs:
            return {
                "risk_level": "unknown",
                "score": 0,
                "summary": "Chưa có đủ dữ liệu để phân tích xu hướng.",
                "alerts": [],
                "trends": {},
            }

        sorted_logs = sorted(logs, key=lambda item: str(item.get("ngay")))
        latest = sorted_logs[-1]
        alerts: list[dict[str, str]] = []

        sys_bp = _to_int(latest.get("huyet_ap_tam_thu"))
        dia_bp = _to_int(latest.get("huyet_ap_tam_truong"))
        heart_rate = _to_int(latest.get("nhip_tim"))
        sleep_hours = _to_float(latest.get("giac_ngu"))

        if sys_bp and dia_bp:
            if sys_bp >= 140 or dia_bp >= 90:
                alerts.append({"type": "danger", "message": "Huyết áp cao, nên đo lại sau 5 phút nghỉ ngơi và liên hệ bác sĩ nếu lặp lại."})
            elif sys_bp < 90 or dia_bp < 60:
                alerts.append({"type": "warning", "message": "Huyết áp thấp, cần bổ sung nước và theo dõi chóng mặt/mệt mỏi."})

        if heart_rate:
            if heart_rate > 100:
                alerts.append({"type": "warning", "message": "Nhịp tim cao hơn mức nghỉ ngơi thông thường."})
            elif heart_rate < 50:
                alerts.append({"type": "warning", "message": "Nhịp tim thấp, cần chú ý nếu có mệt, choáng hoặc khó thở."})

        if sleep_hours is not None and sleep_hours < 6:
            alerts.append({"type": "warning", "message": "Giấc ngủ dưới 6 giờ, nên ưu tiên ngủ bù và giảm caffeine buổi chiều."})

        weight_trend = HealthTrackingService._trend(sorted_logs, "can_nang")
        if abs(weight_trend.get("delta", 0)) >= 1.5:
            alerts.append({"type": "info", "message": "Cân nặng thay đổi nhanh trong chu kỳ gần đây, nên theo dõi chế độ ăn/uống nước."})

        mood_values = [_to_int(item.get("tam_trang")) for item in sorted_logs[-7:]]
        mood_values = [v for v in mood_values if v is not None]
        if mood_values and mean(mood_values) <= 2:
            alerts.append({"type": "warning", "message": "Tâm trạng trung bình đang thấp, nên nghỉ ngơi và chia sẻ với người thân/bác sĩ."})

        score = max(0, 100 - len([a for a in alerts if a["type"] == "danger"]) * 35 - len(alerts) * 10)
        risk_level = "good" if score >= 80 else "watch" if score >= 55 else "risk"
        summary = {
            "good": "Chỉ số gần đây ổn định. Tiếp tục duy trì thói quen hiện tại.",
            "watch": "Có một vài tín hiệu cần theo dõi thêm trong các ngày tới.",
            "risk": "Có dấu hiệu bất thường, nên đặt lịch tư vấn bác sĩ nếu triệu chứng kéo dài.",
        }[risk_level]

        return {
            "risk_level": risk_level,
            "score": score,
            "summary": summary,
            "alerts": alerts,
            "trends": {
                "nhip_tim": HealthTrackingService._trend(sorted_logs, "nhip_tim"),
                "huyet_ap_tam_thu": HealthTrackingService._trend(sorted_logs, "huyet_ap_tam_thu"),
                "giac_ngu": HealthTrackingService._trend(sorted_logs, "giac_ngu"),
                "can_nang": weight_trend,
            },
        }

    @staticmethod
    def chart_data(logs: list[dict[str, Any]]) -> dict[str, list[Any]]:
        sorted_logs = sorted(logs, key=lambda item: str(item.get("ngay")))
        return {
            "labels": [str(item.get("ngay")) for item in sorted_logs],
            "nhip_tim": [_to_int(item.get("nhip_tim")) for item in sorted_logs],
            "huyet_ap_tam_thu": [_to_int(item.get("huyet_ap_tam_thu")) for item in sorted_logs],
            "huyet_ap_tam_truong": [_to_int(item.get("huyet_ap_tam_truong")) for item in sorted_logs],
            "giac_ngu": [_to_float(item.get("giac_ngu")) for item in sorted_logs],
            "can_nang": [_to_float(item.get("can_nang")) for item in sorted_logs],
        }

    @staticmethod
    def _clean_payload(payload: dict[str, Any]) -> dict[str, Any]:
        ngay = str(payload.get("ngay") or date.today().isoformat())
        try:
            datetime.strptime(ngay, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Ngay khong hop le.") from exc

        systolic = _to_int(payload.get("huyet_ap_tam_thu"))
        diastolic = _to_int(payload.get("huyet_ap_tam_truong"))
        bp_text = payload.get("huyet_ap")
        if (not systolic or not diastolic) and isinstance(bp_text, str) and "/" in bp_text:
            left, right = bp_text.split("/", 1)
            systolic = _to_int(left)
            diastolic = _to_int(right)

        if systolic and diastolic:
            bp_text = f"{systolic}/{diastolic}"

        return {
            "ngay": ngay,
            "nhip_tim": _bounded_int(payload.get("nhip_tim"), 25, 220),
            "huyet_ap_tam_thu": _bounded_int(systolic, 60, 260),
            "huyet_ap_tam_truong": _bounded_int(diastolic, 35, 160),
            "huyet_ap": str(bp_text or "")[:10],
            "giac_ngu": _bounded_float(payload.get("giac_ngu"), 0, 24),
            "can_nang": _bounded_float(payload.get("can_nang"), 10, 300),
            "tam_trang": _bounded_int(payload.get("tam_trang") or 3, 1, 5) or 3,
            "muc_nang_luong": _bounded_int(payload.get("muc_nang_luong") or 3, 1, 5) or 3,
            "nuoc_uong": _bounded_int(payload.get("nuoc_uong") or 0, 0, 10000) or 0,
            "buoc_di": _bounded_int(payload.get("buoc_di") or 0, 0, 100000) or 0,
            "ghi_chu": str(payload.get("ghi_chu") or "")[:1000],
        }

    @staticmethod
    def _trend(logs: list[dict[str, Any]], field: str) -> dict[str, Any]:
        values = [_to_float(item.get(field)) for item in logs if _to_float(item.get(field)) is not None]
        if len(values) < 2:
            return {"direction": "flat", "delta": 0, "avg": values[0] if values else None}
        delta = round(values[-1] - values[0], 1)
        direction = "up" if delta > 0 else "down" if delta < 0 else "flat"
        return {"direction": direction, "delta": delta, "avg": round(mean(values), 1)}


def _to_int(value: Any) -> int | None:
    try:
        if value in ("", None):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _bounded_int(value: Any, minimum: int, maximum: int) -> int | None:
    parsed = _to_int(value)
    if parsed is None:
        return None
    return max(minimum, min(maximum, parsed))


def _bounded_float(value: Any, minimum: float, maximum: float) -> float | None:
    parsed = _to_float(value)
    if parsed is None:
        return None
    return max(minimum, min(maximum, parsed))

