"""
Kho tri thuc suc khoe dung chung cho cac tien ich.

File JSON duoc cache trong memory de API phan hoi nhanh va de sinh vien
co the mo rong du lieu ma khong phai sua logic Python.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class HealthDataRepository:
    """Doc va truy van data JSON cho BMI, bai tap va chan doan."""

    @staticmethod
    @lru_cache(maxsize=4)
    def _load_json(filename: str) -> dict[str, Any]:
        path = DATA_DIR / filename
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def nutrition_data(cls) -> dict[str, Any]:
        return cls._load_json("health_knowledge.json")

    @classmethod
    def diagnosis_data(cls) -> dict[str, Any]:
        return cls._load_json("symptom_disease_dataset.json")

    @classmethod
    def foods_for_goal(cls, goal: str, limit: int = 12) -> list[dict[str, Any]]:
        foods = cls.nutrition_data().get("foods", [])
        matched = [item for item in foods if goal in item.get("goal", [])]
        return matched[:limit]

    @classmethod
    def exercises_for_goal(cls, goal: str, limit: int = 10) -> list[dict[str, Any]]:
        exercises = cls.nutrition_data().get("exercises", [])
        matched = [item for item in exercises if goal in item.get("goal", [])]
        return matched[:limit]

    @classmethod
    def weekly_plan(cls, category_key: str) -> dict[str, Any]:
        plans = cls.nutrition_data().get("weekly_plans", {})
        return plans.get(category_key) or plans.get("maintain", {})

    @classmethod
    def stats(cls) -> dict[str, int]:
        nutrition = cls.nutrition_data()
        diagnosis = cls.diagnosis_data()
        return {
            "foods": len(nutrition.get("foods", [])),
            "exercises": len(nutrition.get("exercises", [])),
            "weekly_plans": len(nutrition.get("weekly_plans", {})),
            "symptoms": len(diagnosis.get("symptoms", [])),
            "diseases": len(diagnosis.get("diseases", [])),
        }

