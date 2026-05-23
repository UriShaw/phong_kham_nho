"""
AI chan doan rule-based tu trieu chung.

Day khong phai mo hinh y khoa thay the bac si. Logic duoc viet ro rang:
map keyword -> symptom id, tinh trong so trung khop voi dataset benh,
sap xep do tin cay va de xuat chuyen khoa.
"""
from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from core.database import db
from app.services.health_data_repository import HealthDataRepository
from app.services.utility_schema_service import UtilitySchemaService


class DiagnosisService:
    """Tra cuu benh theo trieu chung va luu lich su."""

    @staticmethod
    def symptom_options() -> list[dict[str, Any]]:
        return HealthDataRepository.diagnosis_data().get("symptoms", [])

    @staticmethod
    def diagnose(payload: dict[str, Any], user_id: int | None = None, benh_nhan_id: int | None = None) -> dict[str, Any]:
        data = HealthDataRepository.diagnosis_data()
        text = str(payload.get("trieu_chung_text") or payload.get("text") or "")
        selected = payload.get("symptoms") or payload.get("trieu_chung") or []
        selected_ids = {str(item) for item in selected if item}
        detected = DiagnosisService._detect_symptoms(text, selected_ids, data.get("symptoms", []))

        if not detected:
            return {
                "detected_symptoms": [],
                "results": [],
                "risk_level": "unknown",
                "advice": "Hay nhap it nhat 1 trieu chung ro rang de he thong phan tich.",
                "disclaimer": DiagnosisService.disclaimer(),
            }

        results = []
        detected_ids = {item["id"] for item in detected}
        normalized_text = _normalize(text)
        for disease in data.get("diseases", []):
            weights = disease.get("symptoms", {})
            total_weight = sum(float(value) for value in weights.values()) or 1
            matched_weight = sum(float(weights[sid]) for sid in detected_ids if sid in weights)
            confidence = round(min(96, (matched_weight / total_weight) * 100))
            red_flags = [
                flag for flag in disease.get("red_flags", [])
                if _normalize(flag) in normalized_text
            ]
            if red_flags:
                confidence = min(98, confidence + 12)
            if confidence >= 18:
                results.append({
                    "id": disease.get("id"),
                    "name": disease.get("name"),
                    "confidence": confidence,
                    "description": disease.get("description"),
                    "specialist": disease.get("specialist"),
                    "advice": disease.get("advice"),
                    "red_flags": red_flags,
                    "matched_symptoms": [
                        symptom for symptom in detected
                        if symptom["id"] in weights
                    ],
                })

        results.sort(key=lambda item: item["confidence"], reverse=True)
        risk_level = DiagnosisService._risk_level(results)
        output = {
            "detected_symptoms": detected,
            "results": results[:5],
            "risk_level": risk_level,
            "advice": DiagnosisService._general_advice(risk_level, results),
            "disclaimer": DiagnosisService.disclaimer(),
        }
        DiagnosisService.save_history(user_id, benh_nhan_id, text, detected, output)
        return output

    @staticmethod
    def save_history(
        user_id: int | None,
        benh_nhan_id: int | None,
        text: str,
        symptoms: list[dict[str, Any]],
        result: dict[str, Any],
    ) -> None:
        if not (user_id or benh_nhan_id) or not UtilitySchemaService.ensure():
            return
        db.execute(
            """
            INSERT INTO ai_chan_doan_log
            (benh_nhan_id, nguoi_dung_id, trieu_chung_text, trieu_chung_json, ket_qua_json, muc_nguy_co)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                benh_nhan_id,
                user_id,
                text[:3000],
                json.dumps(symptoms, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
                result.get("risk_level"),
            ),
        )

    @staticmethod
    def history(benh_nhan_id: int | None, limit: int = 10) -> list[dict[str, Any]]:
        if not benh_nhan_id or not UtilitySchemaService.ensure():
            return []
        rows = db.query(
            """
            SELECT *
            FROM ai_chan_doan_log
            WHERE benh_nhan_id = %s
            ORDER BY ngay_tao DESC
            LIMIT %s
            """,
            (benh_nhan_id, limit),
        )
        for row in rows:
            row["ket_qua"] = _json_loads(row.get("ket_qua_json"))
            row["trieu_chung"] = _json_loads(row.get("trieu_chung_json"))
        return rows

    @staticmethod
    def disclaimer() -> str:
        return "Ket qua chi ho tro sang loc ban dau, khong thay the chan doan cua bac si."

    @staticmethod
    def _detect_symptoms(text: str, selected_ids: set[str], symptoms: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized_text = _normalize(text)
        detected: list[dict[str, Any]] = []
        for symptom in symptoms:
            symptom_id = str(symptom.get("id"))
            keywords = [symptom.get("label", ""), *symptom.get("keywords", [])]
            keyword_match = any(_contains_keyword(normalized_text, keyword) for keyword in keywords)
            if symptom_id in selected_ids or keyword_match:
                detected.append({
                    "id": symptom_id,
                    "label": symptom.get("label"),
                    "specialist_hint": symptom.get("specialist_hint"),
                })
        return detected

    @staticmethod
    def _risk_level(results: list[dict[str, Any]]) -> str:
        if not results:
            return "unknown"
        top = results[0]
        if top.get("red_flags") or top.get("confidence", 0) >= 75:
            return "high"
        if top.get("confidence", 0) >= 45:
            return "medium"
        return "low"

    @staticmethod
    def _general_advice(risk_level: str, results: list[dict[str, Any]]) -> str:
        if risk_level == "high":
            return "Nen lien he co so y te som, dac biet neu trieu chung nang len hoac xuat hien dau hieu nguy hiem."
        if risk_level == "medium":
            specialist = results[0].get("specialist") if results else "Noi tong quat"
            return f"Co the dat lich voi bac si {specialist} de duoc hoi benh va kham truc tiep."
        if risk_level == "low":
            return "Theo doi them, nghi ngoi va dat lich kham neu trieu chung keo dai tren 2-3 ngay."
        return "Can them thong tin trieu chung de phan tich tot hon."


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFD", str(value).lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = value.replace("đ", "d")
    return re.sub(r"\s+", " ", value)


def _contains_keyword(normalized_text: str, keyword: str) -> bool:
    normalized_keyword = _normalize(keyword).strip()
    return bool(normalized_keyword and normalized_keyword in normalized_text)


def _json_loads(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value or "null")
    except (TypeError, json.JSONDecodeError):
        return None

