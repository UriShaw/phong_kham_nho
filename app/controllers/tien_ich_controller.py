"""
Controller Tien ich suc khoe.

Routes HTML render giao dien, routes /api/* tra JSON theo REST de frontend
co the goi doc lap.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from flask import Blueprint, request, session

from core.controller import BaseController
from core.database import db
from core.middleware import login_required
from app.models.benh_nhan_model import BenhNhanModel
from app.services.bmi_service import BmiService
from app.services.diagnosis_service import DiagnosisService
from app.services.health_data_repository import HealthDataRepository
from app.services.health_tracking_service import HealthTrackingService
from app.services.mood_journal_service import MoodJournalService


tien_ich_bp = Blueprint("tien_ich", __name__)


@tien_ich_bp.route("/")
def dashboard():
    """Dashboard tong hop cac tien ich suc khoe."""
    benh_nhan_id = _current_benh_nhan_id()
    logs = HealthTrackingService.list_logs(benh_nhan_id, days=14)
    mood_entries = MoodJournalService.list_entries(benh_nhan_id, days=7)
    mood_stats = MoodJournalService.get_stats(benh_nhan_id, days=30)
    history = DiagnosisService.history(benh_nhan_id, limit=5)

    # BMI info from patient profile
    bmi_info = None
    if benh_nhan_id:
        bn = BenhNhanModel.get_by_id(benh_nhan_id)
        if bn and bn.get('chieu_cao') and bn.get('can_nang'):
            h = float(bn['chieu_cao'])
            w = float(bn['can_nang'])
            if h > 0:
                bmi_val = round(w / ((h / 100) ** 2), 1)
                bmi_info = {'bmi': bmi_val, 'chieu_cao': h, 'can_nang': w}

    return BaseController.render(
        "tien_ich/index.html",
        logs=logs,
        mood_entries=mood_entries,
        mood_stats=mood_stats,
        history=history,
        analysis=HealthTrackingService.analyze(logs),
        bmi_info=bmi_info,
    )


@tien_ich_bp.route("/bmi")
def bmi_calculator():
    return BaseController.render("tien_ich/bmi.html", data_stats=HealthDataRepository.stats())


@tien_ich_bp.route("/api/bmi", methods=["POST"])
def api_tinh_bmi():
    try:
        payload = request.get_json(silent=True) or {}
        result = BmiService.calculate(payload)
        benh_nhan_id = _current_benh_nhan_id()
        if benh_nhan_id:
            BenhNhanModel.cap_nhat_suc_khoe(
                benh_nhan_id,
                {
                    "chieu_cao": payload.get("chieu_cao"),
                    "can_nang": payload.get("can_nang"),
                },
            )
        return BaseController.json_response(result, message="Da tinh BMI thanh cong.")
    except ValueError as exc:
        return BaseController.json_error(str(exc), status=422)
    except Exception:
        return BaseController.json_error("Khong the tinh BMI luc nay.", status=500)


@tien_ich_bp.route("/api/bmi/data")
def api_bmi_data():
    data = HealthDataRepository.nutrition_data()
    return BaseController.json_response(
        {
            "stats": HealthDataRepository.stats(),
            "foods": data.get("foods", []),
            "exercises": data.get("exercises", []),
            "weekly_plans": data.get("weekly_plans", {}),
        }
    )


@tien_ich_bp.route("/suc-khoe")
@login_required
def suc_khoe_hang_ngay():
    benh_nhan_id = _current_benh_nhan_id()
    logs = HealthTrackingService.list_logs(benh_nhan_id, days=30)
    return BaseController.render(
        "tien_ich/suc_khoe.html",
        logs=logs,
        analysis=HealthTrackingService.analyze(logs),
        chart_data=HealthTrackingService.chart_data(logs),
        today=date.today().isoformat(),
    )


@tien_ich_bp.route("/api/suc-khoe", methods=["GET"])
@login_required
def api_suc_khoe_list():
    benh_nhan_id = _current_benh_nhan_id()
    days = max(7, min(120, request.args.get("days", 30, type=int)))
    logs = HealthTrackingService.list_logs(benh_nhan_id, days=days)
    return BaseController.json_response(
        _jsonable(
            {
                "logs": logs,
                "chart": HealthTrackingService.chart_data(logs),
                "analysis": HealthTrackingService.analyze(logs),
            }
        )
    )


@tien_ich_bp.route("/api/suc-khoe", methods=["POST"])
@login_required
def api_log_suc_khoe():
    benh_nhan_id = _current_benh_nhan_id()
    if not benh_nhan_id:
        return BaseController.json_error("Can hoan thien ho so benh nhan truoc.", status=403)
    try:
        result = HealthTrackingService.save_daily_log(benh_nhan_id, request.get_json(silent=True) or {})
        return BaseController.json_response(_jsonable(result), message="Da luu chi so suc khoe.")
    except ValueError as exc:
        return BaseController.json_error(str(exc), status=422)
    except RuntimeError as exc:
        return BaseController.json_error(str(exc), status=503)


@tien_ich_bp.route("/nhat-ky-tam-trang")
@login_required
def nhat_ky_tam_trang():
    benh_nhan_id = _current_benh_nhan_id()
    entries = MoodJournalService.list_entries(benh_nhan_id, days=7)
    stats = MoodJournalService.get_stats(benh_nhan_id, days=30)
    today_entry = MoodJournalService.get_today(benh_nhan_id)
    return BaseController.render(
        "tien_ich/nhat_ky_tam_trang.html",
        entries=entries,
        stats=stats,
        today_entry=today_entry,
    )


@tien_ich_bp.route("/api/tam-trang", methods=["GET"])
@login_required
def api_mood_list():
    benh_nhan_id = _current_benh_nhan_id()
    days = max(7, min(120, request.args.get("days", 30, type=int)))
    entries = MoodJournalService.list_entries(benh_nhan_id, days=days)
    stats = MoodJournalService.get_stats(benh_nhan_id, days=days)
    return BaseController.json_response(_jsonable({"entries": entries, "stats": stats}))


@tien_ich_bp.route("/api/tam-trang", methods=["POST"])
@login_required
def api_save_mood():
    benh_nhan_id = _current_benh_nhan_id()
    if not benh_nhan_id:
        return BaseController.json_error("Can hoan thien ho so benh nhan truoc.", status=403)
    try:
        result = MoodJournalService.save_entry(benh_nhan_id, request.get_json(silent=True) or {})
        return BaseController.json_response(_jsonable(result), message="Da luu nhat ky tam trang.")
    except ValueError as exc:
        return BaseController.json_error(str(exc), status=422)
    except RuntimeError as exc:
        return BaseController.json_error(str(exc), status=503)


@tien_ich_bp.route("/api/tam-trang/<int:entry_id>", methods=["DELETE"])
@login_required
def api_delete_mood(entry_id: int):
    MoodJournalService.delete_entry(entry_id, _current_benh_nhan_id())
    return BaseController.json_response(message="Da xoa nhat ky tam trang.")


@tien_ich_bp.route("/chan-doan")
def chan_doan():
    return BaseController.render(
        "tien_ich/chan_doan.html",
        symptoms=DiagnosisService.symptom_options(),
        history=DiagnosisService.history(_current_benh_nhan_id(), limit=5),
    )


@tien_ich_bp.route("/api/chan-doan", methods=["POST"])
def api_chan_doan():
    result = DiagnosisService.diagnose(
        request.get_json(silent=True) or {},
        user_id=session.get("user_id"),
        benh_nhan_id=_current_benh_nhan_id(),
    )
    return BaseController.json_response(_jsonable(result), message="Da phan tich trieu chung.")


@tien_ich_bp.route("/api/chan-doan/lich-su")
@login_required
def api_chan_doan_history():
    return BaseController.json_response(_jsonable({"items": DiagnosisService.history(_current_benh_nhan_id(), 20)}))


@tien_ich_bp.route("/api/chan-doan/<int:log_id>", methods=["DELETE"])
@login_required
def api_xoa_chan_doan(log_id: int):
    """Xóa log chẩn đoán AI."""
    benh_nhan_id = _current_benh_nhan_id()
    if benh_nhan_id:
        db.execute(
            "DELETE FROM ai_chan_doan_log WHERE id = %s AND benh_nhan_id = %s",
            (log_id, benh_nhan_id),
        )
    return BaseController.json_response(message="Đã xóa lịch sử chẩn đoán.")


@tien_ich_bp.route("/api/suc-khoe/<int:log_id>", methods=["DELETE"])
@login_required
def api_xoa_log_suc_khoe(log_id: int):
    """Xóa log sức khỏe."""
    benh_nhan_id = _current_benh_nhan_id()
    if benh_nhan_id:
        db.execute(
            "DELETE FROM suc_khoe_log WHERE id = %s AND benh_nhan_id = %s",
            (log_id, benh_nhan_id),
        )
    return BaseController.json_response(message="Đã xóa log sức khỏe.")


@tien_ich_bp.route("/api/suc-khoe/<int:log_id>", methods=["PUT"])
@login_required
def api_sua_log_suc_khoe(log_id: int):
    """Sửa log sức khỏe."""
    benh_nhan_id = _current_benh_nhan_id()
    if not benh_nhan_id:
        return BaseController.json_error("Chưa đăng nhập.", status=403)
    payload = request.get_json(silent=True) or {}
    fields = {}
    for key in ("nhip_tim", "huyet_ap_tam_thu", "huyet_ap_tam_truong",
                "can_nang", "giac_ngu", "ghi_chu"):
        if key in payload and payload[key] is not None:
            fields[key] = payload[key]
    if not fields:
        return BaseController.json_error("Không có dữ liệu để cập nhật.", status=400)
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [log_id, benh_nhan_id]
    db.execute(
        f"UPDATE suc_khoe_log SET {set_clause} WHERE id = %s AND benh_nhan_id = %s",
        tuple(values),
    )
    return BaseController.json_response(message="Đã cập nhật log sức khỏe.")


def _current_benh_nhan_id() -> int | None:
    if session.get("benh_nhan_id"):
        return session.get("benh_nhan_id")
    user_id = session.get("user_id")
    if not user_id:
        return None
    benh_nhan = BenhNhanModel.lay_theo_nguoi_dung(user_id)
    if benh_nhan:
        session["benh_nhan_id"] = benh_nhan["id"]
        return benh_nhan["id"]
    return None


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    return value
