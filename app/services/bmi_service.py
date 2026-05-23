"""
Nghiep vu BMI nang cao: tinh chi so, phan loai, goi y an uong,
tap luyen va thong so de frontend ve mo hinh 3D.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.health_data_repository import HealthDataRepository


@dataclass
class BmiInput:
    chieu_cao: float
    can_nang: float
    tuoi: int = 25
    gioi_tinh: str = "Nam"


class BmiService:
    """Tinh BMI va sinh khuyen nghi ca nhan hoa."""

    @staticmethod
    def calculate(payload: dict[str, Any]) -> dict[str, Any]:
        bmi_input = BmiService._parse_payload(payload)
        height_m = bmi_input.chieu_cao / 100
        bmi = bmi_input.can_nang / (height_m ** 2)
        category = BmiService._category(bmi)
        ideal_bmi = 22 if BmiService._is_male(bmi_input.gioi_tinh) else 21
        ideal_weight = ideal_bmi * (height_m ** 2)
        bmr = BmiService._bmr(bmi_input)
        goal = category["goal"]

        foods = HealthDataRepository.foods_for_goal(goal, limit=10)
        if not foods and goal == "medical_weight_loss":
            foods = HealthDataRepository.foods_for_goal("lose_weight", limit=10)
        exercises = HealthDataRepository.exercises_for_goal(goal, limit=8)
        if not exercises and goal == "medical_weight_loss":
            exercises = HealthDataRepository.exercises_for_goal("lose_weight", limit=8)
        weekly_plan = HealthDataRepository.weekly_plan(category["key"])
        if not weekly_plan or not weekly_plan.get("title"):
            weekly_plan = HealthDataRepository.weekly_plan("obese_1") or {"title": "Gợi ý dinh dưỡng"}

        calorie_target = BmiService._calorie_target(bmr, goal)
        macro = BmiService._macro_suggestion(calorie_target, goal)

        return {
            "bmi": round(bmi, 1),
            "phan_loai": category["label"],
            "category_key": category["key"],
            "mau": category["color"],
            "loi_khuyen": category["advice"],
            "goal": goal,
            "goal_label": category["goal_label"],
            "cn_ly_tuong": round(ideal_weight, 1),
            "chenh_lech": round(bmi_input.can_nang - ideal_weight, 1),
            "bmr": round(bmr),
            "calo_ngay": calorie_target,
            "nuoc_can": int(bmi_input.can_nang * 35),
            "macro": macro,
            "foods": foods,
            "exercises": exercises,
            "weekly_plan": weekly_plan,
            "body_model": BmiService._body_model(bmi, bmi_input.gioi_tinh),
            "disclaimer": (
                "Gợi ý chỉ mang tính tham khảo. Nếu có bệnh nền, đang mang thai "
                "hoặc BMI quá thấp/cao, hãy gặp bác sĩ hoặc chuyên gia dinh dưỡng."
            ),
        }

    @staticmethod
    def _parse_payload(payload: dict[str, Any]) -> BmiInput:
        try:
            chieu_cao = float(payload.get("chieu_cao", 0))
            can_nang = float(payload.get("can_nang", 0))
            tuoi = int(payload.get("tuoi") or 25)
            gioi_tinh = str(payload.get("gioi_tinh") or "Nam")
        except (TypeError, ValueError) as exc:
            raise ValueError("Du lieu BMI khong hop le.") from exc

        if not 50 <= chieu_cao <= 250:
            raise ValueError("Chieu cao phai nam trong khoang 50-250 cm.")
        if not 10 <= can_nang <= 300:
            raise ValueError("Can nang phai nam trong khoang 10-300 kg.")
        if not 1 <= tuoi <= 120:
            raise ValueError("Tuoi phai nam trong khoang 1-120.")
        return BmiInput(chieu_cao=chieu_cao, can_nang=can_nang, tuoi=tuoi, gioi_tinh=gioi_tinh)

    @staticmethod
    def _category(bmi: float) -> dict[str, str]:
        if bmi < 16:
            return {
                "key": "severe_underweight",
                "label": "Gầy nghiêm trọng",
                "goal": "gain_weight",
                "goal_label": "Tăng cân có kiểm soát",
                "color": "#dc2626",
                "advice": "BMI rất thấp. Nên đặt lịch khám dinh dưỡng và tăng năng lượng từ thực phẩm giàu đạm.",
            }
        if bmi < 18.5:
            return {
                "key": "underweight",
                "label": "Thiếu cân",
                "goal": "gain_weight",
                "goal_label": "Tăng cân và tăng cơ",
                "color": "#d97706",
                "advice": "Cần tăng khẩu phần, ưu tiên đạm, tinh bột tốt và tập sức mạnh nhẹ.",
            }
        if bmi < 23:
            return {
                "key": "normal",
                "label": "Bình thường",
                "goal": "maintain",
                "goal_label": "Duy trì thể trạng",
                "color": "#16a34a",
                "advice": "Đang trong vùng BMI tốt. Duy trì ăn cân bằng và vận động đều.",
            }
        if bmi < 25:
            return {
                "key": "overweight",
                "label": "Thừa cân",
                "goal": "lose_weight",
                "goal_label": "Giảm mỡ nhẹ",
                "color": "#ea580c",
                "advice": "Nên tạo thâm hụt calo nhẹ, tăng rau xanh, đạm nạc và cardio cường độ vừa.",
            }
        if bmi < 30:
            return {
                "key": "obese_1",
                "label": "Béo phì độ I",
                "goal": "lose_weight",
                "goal_label": "Giảm cân an toàn",
                "color": "#dc2626",
                "advice": "Cần kế hoạch giảm cân có theo dõi. Ưu tiên đi bộ, gym nhẹ và kiểm soát đường.",
            }
        return {
            "key": "obese_2",
            "label": "Béo phì độ II trở lên",
            "goal": "medical_weight_loss",
            "goal_label": "Giảm cân có giám sát y tế",
            "color": "#991b1b",
            "advice": "Nên tham vấn bác sĩ dinh dưỡng/nội tiết để lập phác đồ giảm cân phù hợp.",
        }

    @staticmethod
    def _is_male(gender: str) -> bool:
        return gender.strip().lower() in {"nam", "male", "m"}

    @staticmethod
    def _bmr(data: BmiInput) -> float:
        if BmiService._is_male(data.gioi_tinh):
            return 88.362 + (13.397 * data.can_nang) + (4.799 * data.chieu_cao) - (5.677 * data.tuoi)
        return 447.593 + (9.247 * data.can_nang) + (3.098 * data.chieu_cao) - (4.330 * data.tuoi)

    @staticmethod
    def _calorie_target(bmr: float, goal: str) -> int:
        maintenance = bmr * 1.5
        if goal == "gain_weight":
            return round(maintenance + 350)
        if goal == "lose_weight":
            return round(max(1200, maintenance - 400))
        if goal == "medical_weight_loss":
            return round(max(1200, maintenance - 500))
        return round(maintenance)

    @staticmethod
    def _macro_suggestion(calories: int, goal: str) -> dict[str, int]:
        if goal == "gain_weight":
            protein_pct, carb_pct, fat_pct = 0.22, 0.50, 0.28
        elif goal in {"lose_weight", "medical_weight_loss"}:
            protein_pct, carb_pct, fat_pct = 0.32, 0.38, 0.30
        else:
            protein_pct, carb_pct, fat_pct = 0.25, 0.45, 0.30
        return {
            "protein_g": round(calories * protein_pct / 4),
            "carb_g": round(calories * carb_pct / 4),
            "fat_g": round(calories * fat_pct / 9),
        }

    @staticmethod
    def _body_model(bmi: float, gender: str) -> dict[str, float | str]:
        # Frontend Three.js dung cac he so nay de scale torso/waist/limbs.
        normalized = max(-1.0, min(1.6, (bmi - 22) / 12))
        waist = 1 + max(-0.18, normalized * 0.34)
        torso = 1 + max(-0.12, normalized * 0.22)
        limb = 1 + max(-0.08, normalized * 0.10)
        shoulder = 1.08 if BmiService._is_male(gender) else 0.98
        return {
            "waist_scale": round(waist, 2),
            "torso_scale": round(torso, 2),
            "limb_scale": round(limb, 2),
            "shoulder_scale": round(shoulder, 2),
            "color": "#38bdf8" if bmi < 18.5 else "#34d399" if bmi < 23 else "#f59e0b" if bmi < 25 else "#f97316",
        }

