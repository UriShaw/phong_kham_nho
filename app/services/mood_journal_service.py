"""
AI Mood Journal Service - Nhat ky tam trang thong minh.
Benh nhan ghi nhat ky tam trang, AI phan tich cam xuc va goi y.
"""
from __future__ import annotations

import logging
import random
from datetime import date, datetime, timedelta
from typing import Any

from core.database import db
from app.services.utility_schema_service import UtilitySchemaService


logger = logging.getLogger(__name__)


# AI Emotion analysis keywords (Vietnamese)
_POSITIVE_KEYWORDS = [
    'vui', 'hạnh phúc', 'tuyệt vời', 'tốt', 'khỏe', 'phấn khởi', 'hứng khởi',
    'yêu', 'thương', 'biết ơn', 'cảm ơn', 'thoải mái', 'thư giãn', 'bình yên',
    'tự tin', 'hy vọng', 'lạc quan', 'năng lượng', 'sáng tạo', 'hoàn thành',
    'thành công', 'hào hứng', 'cười', 'ấm áp', 'hòa nhã', 'tích cực',
]
_NEGATIVE_KEYWORDS = [
    'buồn', 'chán', 'mệt', 'lo lắng', 'sợ', 'giận', 'stress', 'căng thẳng',
    'trầm cảm', 'cô đơn', 'thất vọng', 'tức', 'đau', 'khóc', 'bất lực',
    'kiệt sức', 'áp lực', 'nản', 'tuyệt vọng', 'hoang mang', 'bồn chồn',
    'mất ngủ', 'lo âu', 'suy sụp', 'chán nản', 'tiêu cực',
]
_NEUTRAL_KEYWORDS = [
    'bình thường', 'ổn', 'được', 'tạm', 'không có gì', 'ok',
]

# Wellness tips by mood level
_WELLNESS_TIPS = {
    'excellent': [
        '🌟 Tuyệt vời! Hãy chia sẻ năng lượng tích cực này với người xung quanh.',
        '🎯 Tâm trạng tốt là thời điểm tuyệt vời để đặt mục tiêu mới.',
        '📝 Hãy ghi nhận khoảnh khắc này - nó sẽ là động lực cho những ngày khó khăn.',
        '🧘 Thiền 5 phút để duy trì trạng thái cân bằng này.',
    ],
    'good': [
        '🌿 Hãy dành 15 phút đi dạo ngoài trời để tận hưởng thêm.',
        '💧 Uống đủ nước giúp duy trì năng lượng và tâm trạng tốt.',
        '🎵 Nghe playlist yêu thích để kéo dài cảm giác tích cực.',
        '📚 Đọc một vài trang sách truyền cảm hứng.',
    ],
    'neutral': [
        '🌤️ Hãy thử một hoạt động mới để khuấy động ngày hôm nay.',
        '🥗 Một bữa ăn lành mạnh có thể cải thiện tâm trạng đáng kể.',
        '🤝 Gọi điện cho người thân hoặc bạn bè để kết nối.',
        '🏃 Vận động nhẹ 20 phút giúp tăng endorphin tự nhiên.',
    ],
    'low': [
        '💛 Hãy nhớ rằng mọi cảm xúc đều tạm thời và có giá trị.',
        '🛁 Tắm nước ấm và nghỉ ngơi đầy đủ sẽ giúp bạn hồi phục.',
        '🌱 Thử viết ra 3 điều nhỏ bạn biết ơn hôm nay.',
        '☕ Pha một tách trà ấm và dành thời gian cho bản thân.',
    ],
    'critical': [
        '🆘 Nếu bạn cảm thấy quá tải, hãy liên hệ đường dây hỗ trợ tâm lý: 1800 599 920.',
        '🩺 Hãy đặt lịch khám với chuyên gia tâm lý qua MedPro.',
        '💚 Bạn không đơn độc. Hãy chia sẻ với người thân hoặc bác sĩ.',
        '🧠 Sức khỏe tinh thần quan trọng không kém sức khỏe thể chất.',
    ],
}

# Emoji mood map
MOOD_EMOJIS = {
    5: '😄', 4: '🙂', 3: '😐', 2: '😔', 1: '😢',
}
MOOD_LABELS = {
    5: 'Rất vui', 4: 'Vui', 3: 'Bình thường', 2: 'Buồn', 1: 'Rất buồn',
}
MOOD_COLORS = {
    5: '#059669', 4: '#10b981', 3: '#f59e0b', 2: '#f97316', 1: '#ef4444',
}


class MoodJournalService:
    """Quan ly nhat ky tam trang va phan tich AI."""

    @staticmethod
    def list_entries(benh_nhan_id: int | None, days: int = 30) -> list[dict[str, Any]]:
        """Lay danh sach nhat ky tam trang."""
        if not benh_nhan_id or not UtilitySchemaService.ensure():
            return []
        return db.query(
            """
            SELECT * FROM nhat_ky_tam_trang
            WHERE benh_nhan_id = %s AND ngay >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY ngay DESC
            """,
            (benh_nhan_id, days),
        )

    @staticmethod
    def get_today(benh_nhan_id: int | None) -> dict | None:
        """Lay entry hom nay."""
        if not benh_nhan_id or not UtilitySchemaService.ensure():
            return None
        return db.get_one(
            "SELECT * FROM nhat_ky_tam_trang WHERE benh_nhan_id = %s AND ngay = CURDATE()",
            (benh_nhan_id,),
        )

    @staticmethod
    def save_entry(benh_nhan_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """Luu hoac cap nhat entry nhat ky hom nay."""
        if not UtilitySchemaService.ensure():
            raise RuntimeError("Chua ket noi duoc database.")

        muc_tam_trang = int(payload.get('muc_tam_trang', 3))
        if muc_tam_trang < 1 or muc_tam_trang > 5:
            raise ValueError("Muc tam trang phai tu 1 den 5.")

        noi_dung = str(payload.get('noi_dung', '')).strip()[:2000]
        hoat_dong = str(payload.get('hoat_dong', '')).strip()[:500]
        giac_ngu_diem = int(payload.get('giac_ngu_diem', 3))
        nang_luong_diem = int(payload.get('nang_luong_diem', 3))

        # AI Analysis
        ai_analysis = MoodJournalService._analyze_mood(muc_tam_trang, noi_dung)

        existing = db.get_one(
            "SELECT id FROM nhat_ky_tam_trang WHERE benh_nhan_id = %s AND ngay = CURDATE()",
            (benh_nhan_id,),
        )

        if existing:
            db.execute(
                """
                UPDATE nhat_ky_tam_trang
                SET muc_tam_trang = %s, noi_dung = %s, hoat_dong = %s,
                    giac_ngu_diem = %s, nang_luong_diem = %s,
                    ai_phan_tich = %s, ai_goi_y = %s
                WHERE id = %s
                """,
                (
                    muc_tam_trang, noi_dung, hoat_dong,
                    giac_ngu_diem, nang_luong_diem,
                    ai_analysis['sentiment'], ai_analysis['tip'],
                    existing['id'],
                ),
            )
            entry_id = existing['id']
        else:
            entry_id = db.execute(
                """
                INSERT INTO nhat_ky_tam_trang
                (benh_nhan_id, ngay, muc_tam_trang, noi_dung, hoat_dong,
                 giac_ngu_diem, nang_luong_diem, ai_phan_tich, ai_goi_y)
                VALUES (%s, CURDATE(), %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    benh_nhan_id, muc_tam_trang, noi_dung, hoat_dong,
                    giac_ngu_diem, nang_luong_diem,
                    ai_analysis['sentiment'], ai_analysis['tip'],
                ),
            )

        return {
            'id': entry_id,
            'ai_analysis': ai_analysis,
            'mood_emoji': MOOD_EMOJIS.get(muc_tam_trang, '😐'),
            'mood_label': MOOD_LABELS.get(muc_tam_trang, 'Bình thường'),
        }

    @staticmethod
    def delete_entry(entry_id: int, benh_nhan_id: int | None) -> None:
        if not benh_nhan_id or not UtilitySchemaService.ensure():
            return
        db.execute(
            "DELETE FROM nhat_ky_tam_trang WHERE id = %s AND benh_nhan_id = %s",
            (entry_id, benh_nhan_id),
        )

    @staticmethod
    def get_stats(benh_nhan_id: int | None, days: int = 30) -> dict[str, Any]:
        """Thong ke tam trang."""
        if not benh_nhan_id or not UtilitySchemaService.ensure():
            return {
                'avg_mood': 0, 'total_entries': 0, 'streak': 0,
                'mood_distribution': {}, 'trend': 'stable',
                'chart_labels': [], 'chart_values': [],
            }

        entries = db.query(
            """
            SELECT ngay, muc_tam_trang FROM nhat_ky_tam_trang
            WHERE benh_nhan_id = %s AND ngay >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY ngay ASC
            """,
            (benh_nhan_id, days),
        )

        if not entries:
            return {
                'avg_mood': 0, 'total_entries': 0, 'streak': 0,
                'mood_distribution': {}, 'trend': 'stable',
                'chart_labels': [], 'chart_values': [],
            }

        moods = [e['muc_tam_trang'] for e in entries]
        avg = sum(moods) / len(moods) if moods else 0

        # Distribution
        dist = {}
        for m in moods:
            label = MOOD_LABELS.get(m, '?')
            dist[label] = dist.get(label, 0) + 1

        # Streak (consecutive days)
        streak = 0
        today = date.today()
        for i in range(days):
            check_date = today - timedelta(days=i)
            found = any(
                (e['ngay'].isoformat() if hasattr(e['ngay'], 'isoformat') else str(e['ngay'])) == check_date.isoformat()
                for e in entries
            )
            if found:
                streak += 1
            else:
                break

        # Trend
        if len(moods) >= 3:
            recent = moods[-3:]
            older = moods[:3]
            r_avg = sum(recent) / len(recent)
            o_avg = sum(older) / len(older)
            if r_avg > o_avg + 0.3:
                trend = 'improving'
            elif r_avg < o_avg - 0.3:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'

        chart_labels = []
        chart_values = []
        for e in entries:
            d = e['ngay']
            label = d.strftime('%d/%m') if hasattr(d, 'strftime') else str(d)[-5:]
            chart_labels.append(label)
            chart_values.append(e['muc_tam_trang'])

        return {
            'avg_mood': round(avg, 1),
            'total_entries': len(entries),
            'streak': streak,
            'mood_distribution': dist,
            'trend': trend,
            'chart_labels': chart_labels,
            'chart_values': chart_values,
        }

    @staticmethod
    def _analyze_mood(level: int, text: str) -> dict[str, str]:
        """Phan tich cam xuc tu text va muc tam trang."""
        text_lower = text.lower()

        pos_count = sum(1 for kw in _POSITIVE_KEYWORDS if kw in text_lower)
        neg_count = sum(1 for kw in _NEGATIVE_KEYWORDS if kw in text_lower)

        if level >= 4 and pos_count > neg_count:
            sentiment = 'Tích cực ✨'
            tips = _WELLNESS_TIPS['excellent'] if level == 5 else _WELLNESS_TIPS['good']
        elif level >= 3:
            sentiment = 'Ổn định 🌤️'
            tips = _WELLNESS_TIPS['neutral']
        elif level == 2:
            sentiment = 'Cần chú ý 💛'
            tips = _WELLNESS_TIPS['low']
        else:
            sentiment = 'Cần hỗ trợ 🆘'
            tips = _WELLNESS_TIPS['critical']

        # Extra sentiment from text
        if neg_count > pos_count + 2:
            sentiment = 'Cần hỗ trợ 🆘'
            tips = _WELLNESS_TIPS['critical']
        elif neg_count > pos_count:
            sentiment = 'Cần chú ý 💛'
            tips = _WELLNESS_TIPS['low']

        tip = random.choice(tips) if tips else 'Hãy chăm sóc bản thân nhé! 💚'

        return {'sentiment': sentiment, 'tip': tip}

    @staticmethod
    def admin_list_all(limit: int = 25) -> list[dict[str, Any]]:
        """Admin xem tat ca nhat ky (overview)."""
        if not UtilitySchemaService.ensure():
            return []
        return db.query(
            """
            SELECT nk.*, nd.ho_ten, nd.email
            FROM nhat_ky_tam_trang nk
            JOIN benh_nhan bn ON nk.benh_nhan_id = bn.id
            JOIN nguoi_dung nd ON bn.nguoi_dung_id = nd.id
            ORDER BY nk.ngay DESC, nk.id DESC
            LIMIT %s
            """,
            (limit,),
        )

    @staticmethod
    def admin_stats() -> dict[str, Any]:
        """Thong ke toan he thong cho admin."""
        if not UtilitySchemaService.ensure():
            return {'total': 0, 'today': 0, 'avg_mood': 0, 'active_users': 0}
        try:
            total = db.get_one("SELECT COUNT(*) AS c FROM nhat_ky_tam_trang")['c']
            today = db.get_one("SELECT COUNT(*) AS c FROM nhat_ky_tam_trang WHERE ngay = CURDATE()")['c']
            avg = db.get_one("SELECT AVG(muc_tam_trang) AS a FROM nhat_ky_tam_trang WHERE ngay >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)")
            avg_mood = round(float(avg['a']), 1) if avg and avg['a'] else 0
            active = db.get_one("SELECT COUNT(DISTINCT benh_nhan_id) AS c FROM nhat_ky_tam_trang WHERE ngay >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)")['c']
            return {'total': total, 'today': today, 'avg_mood': avg_mood, 'active_users': active}
        except Exception:
            return {'total': 0, 'today': 0, 'avg_mood': 0, 'active_users': 0}
