"""
Chatbot Service - AI tư vấn sức khỏe (Rule-based + Symptom Matching)
"""
import re
from app.models.chuyen_khoa_model import ChuyenKhoaModel
from app.models.bac_si_model import BacSiModel
from app.services.benh_ly_data import BENH_LY_DB, TU_DONG_NGHIA


class ChatbotService:
    """Service chatbot tư vấn sức khỏe"""

    FAQ = {
        'giờ khám': 'Giờ khám bệnh: Thứ 2 - Thứ 7, Sáng: 8:00 - 11:30, Chiều: 13:30 - 17:00. Chủ nhật nghỉ.',
        'chi phí': 'Chi phí khám dao động từ 200.000đ - 500.000đ tùy chuyên khoa. Bạn có thể xem giá cụ thể khi chọn bác sĩ.',
        'quy trình': 'Quy trình đặt khám:\n1️⃣ Tìm và chọn bác sĩ\n2️⃣ Chọn ngày giờ khám\n3️⃣ Thanh toán QR và hoàn tất',
        'thanh toán': 'Hỗ trợ thanh toán qua QR Code MB Bank. Nhanh chóng và tiện lợi!',
        'hủy lịch': 'Bạn có thể hủy lịch khám trước 24 giờ qua mục "Lịch khám" trên hệ thống.',
        'bảo hiểm': 'Hiện tại hệ thống chưa hỗ trợ thanh toán bảo hiểm y tế trực tuyến. Vui lòng mang thẻ BHYT khi đến khám.',
        'đổi lịch': 'Bạn có thể sửa lịch khám trong mục "Lịch khám" → nhấn nút "Sửa lịch" (chỉ khi lịch chưa được xác nhận).',
        'liên hệ': 'Bạn có thể liên hệ hotline: 1900 1234 hoặc email: support@medpro.vn',
        'cách đặt': 'Để đặt lịch: vào "Tìm bác sĩ" → chọn bác sĩ → chọn ngày giờ → thanh toán QR → hoàn thành!',
        'tài khoản': 'Bạn có thể tạo tài khoản miễn phí bằng cách nhấn "Đăng ký" tại trang đăng nhập.',
        'khám online': 'Hiện tại MedPro hỗ trợ đặt lịch khám trực tiếp. Chức năng khám online đang được phát triển.',
    }

    SUC_KHOE_FAQ = {
        'uống thuốc': '💊 Lưu ý khi uống thuốc:\n• Uống đúng giờ, đúng liều\n• Không tự ý tăng/giảm liều\n• Đọc kỹ hướng dẫn sử dụng\n• Thông báo bác sĩ nếu có tác dụng phụ',
        'dinh dưỡng': '🥗 Chế độ dinh dưỡng lành mạnh:\n• Ăn nhiều rau xanh và trái cây\n• Hạn chế đồ chiên, đồ ngọt\n• Uống đủ 2L nước/ngày\n• Ăn đúng giờ, không bỏ bữa',
        'tập thể dục': '🏃 Lời khuyên tập thể dục:\n• Tập ít nhất 30 phút/ngày\n• Đi bộ, chạy bộ, bơi lội\n• Khởi động trước khi tập\n• Không tập quá sức',
        'ngủ': '😴 Giấc ngủ chất lượng:\n• Ngủ 7-8 tiếng/đêm\n• Đi ngủ cùng 1 giờ mỗi ngày\n• Tránh màn hình 1h trước khi ngủ\n• Phòng ngủ tối, mát, yên tĩnh',
        'sức khỏe tâm thần': '🧠 Chăm sóc sức khỏe tâm thần:\n• Nghỉ ngơi đầy đủ\n• Chia sẻ với người thân\n• Tập yoga, thiền định\n• Tìm bác sĩ nếu cần hỗ trợ',
        'cân nặng': '⚖️ Kiểm soát cân nặng:\n• BMI bình thường: 18.5 - 24.9\n• Ăn uống cân bằng\n• Tập thể dục đều đặn\n• Theo dõi cân nặng hàng tuần',
    }

    CHAO_HOI = ['xin chào', 'chào', 'hello', 'hi', 'hey', 'alo']
    CAM_ON = ['cảm ơn', 'thank', 'thanks']

    @staticmethod
    def _mo_rong_tu_khoa(msg):
        """Mở rộng message bằng từ đồng nghĩa để tăng khả năng match"""
        expanded = set()
        for goc, dong_nghia in TU_DONG_NGHIA.items():
            # Nếu msg chứa từ gốc → thêm các từ đồng nghĩa
            if goc in msg:
                expanded.add(goc)
                expanded.update(dong_nghia)
            # Nếu msg chứa từ đồng nghĩa → thêm từ gốc
            for dn in dong_nghia:
                if dn in msg:
                    expanded.add(goc)
                    expanded.add(dn)
        return expanded

    @staticmethod
    def _tim_benh(msg):
        """Tìm bệnh phù hợp từ tin nhắn, trả về list (benh, diem) sorted"""
        msg_lower = msg.lower().strip()
        expanded = ChatbotService._mo_rong_tu_khoa(msg_lower)
        all_terms = {msg_lower} | expanded

        results = []
        for benh in BENH_LY_DB:
            score = 0
            matched_kw = []
            for kw in benh["tu_khoa"]:
                # Exact: keyword xuất hiện nguyên vẹn trong message
                if kw in msg_lower:
                    score += 3
                    matched_kw.append(kw)
                    continue
                # Synonym match: keyword khớp CHÍNH XÁC với từ đồng nghĩa
                if kw in expanded:
                    score += 2
                    matched_kw.append(kw)
            if score > 0:
                results.append({"benh": benh, "score": score, "matched": list(set(matched_kw))})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    @staticmethod
    def xu_ly_tin_nhan(message):
        """Xử lý tin nhắn từ người dùng"""
        msg = message.strip().lower()

        # Chào hỏi
        if any(word in msg for word in ChatbotService.CHAO_HOI):
            return {
                'type': 'greeting',
                'message': 'Xin chào! 👋 Tôi là trợ lý sức khỏe MedPro.\n\nTôi có thể giúp bạn:\n• Tư vấn triệu chứng bệnh\n• Gợi ý chuyên khoa và bác sĩ\n• Hướng dẫn đặt lịch khám\n• Trả lời câu hỏi sức khỏe\n\nBạn đang gặp vấn đề gì?',
                'suggestions': ['Tôi bị đau đầu', 'Tôi bị đau bụng', 'Tôi bị đau họng', 'Chi phí khám']
            }

        # Cảm ơn
        if any(word in msg for word in ChatbotService.CAM_ON):
            return {
                'type': 'thanks',
                'message': 'Không có gì! 😊 Chúc bạn sức khỏe. Nếu cần hỗ trợ thêm, đừng ngại hỏi nhé!',
                'suggestions': ['Đặt lịch khám', 'Tìm bác sĩ']
            }

        # === TÌM BỆNH THEO TRIỆU CHỨNG (ƯU TIÊN CAO NHẤT) ===
        matches = ChatbotService._tim_benh(msg)
        if matches and matches[0]["score"] >= 2:
            return ChatbotService._build_symptom_response(matches)

        # Kiểm tra FAQ sức khỏe
        for key, answer in ChatbotService.SUC_KHOE_FAQ.items():
            if key in msg:
                return {
                    'type': 'health_faq',
                    'message': answer,
                    'suggestions': ['Đặt lịch khám', 'Hỏi triệu chứng khác', 'Tìm bác sĩ']
                }

        # Kiểm tra FAQ hệ thống
        for key, answer in ChatbotService.FAQ.items():
            if key in msg:
                return {
                    'type': 'faq',
                    'message': answer,
                    'suggestions': ['Đặt lịch ngay', 'Tìm bác sĩ', 'Hỏi thêm']
                }

        # Match yếu hơn (score < 2) vẫn hiện
        if matches:
            return ChatbotService._build_symptom_response(matches)

        # Tìm bác sĩ
        if 'bác sĩ' in msg or 'tìm bác sĩ' in msg or 'gợi ý' in msg:
            bac_si_list = BacSiModel.bac_si_noi_bat(5)
            response_msg = "👨‍⚕️ **Bác sĩ nổi bật:**\n\n"
            for bs in bac_si_list:
                response_msg += f"• {bs['ten_hien_thi']} - {bs['ten_chuyen_khoa']} ⭐{bs['danh_gia']}\n"
            return {
                'type': 'doctor_list',
                'message': response_msg,
                'bac_si': bac_si_list,
                'suggestions': ['Tìm theo chuyên khoa', 'Đặt lịch ngay']
            }

        # Đặt lịch
        if 'đặt lịch' in msg or 'đặt khám' in msg or 'book' in msg:
            return {
                'type': 'booking',
                'message': '📅 Để đặt lịch khám:\n\n1️⃣ Chọn bác sĩ phù hợp\n2️⃣ Chọn ngày giờ khám\n3️⃣ Thanh toán QR\n\n👉 Bấm nút bên dưới để bắt đầu!',
                'action': 'redirect',
                'url': '/tim-bac-si',
                'suggestions': ['Tìm bác sĩ', 'Xem chuyên khoa']
            }

        # Không hiểu
        return {
            'type': 'fallback',
            'message': '🤔 Tôi chưa hiểu rõ câu hỏi.\n\nBạn có thể thử:\n• Mô tả triệu chứng (VD: "đau bụng", "đau đầu chóng mặt")\n• Hỏi về dịch vụ (VD: "Giờ khám bệnh")\n• Hỏi sức khỏe (VD: "Chế độ dinh dưỡng")\n\nHoặc gọi hotline: **1900 1234**',
            'suggestions': ['Đau bụng', 'Đau đầu', 'Đau họng', 'Ho sốt', 'Đau lưng', 'Đau ngực', 'Mất ngủ', 'Khó thở']
        }

    @staticmethod
    def _build_symptom_response(matches):
        """Build response từ kết quả matching"""
        top = matches[0]
        benh = top["benh"]
        icon = "⚠️" if benh["muc_do"] == "cao" else "🔸" if benh["muc_do"] == "trung bình" else "🔹"

        msg = f"{icon} **Có thể bạn đang gặp: {benh['benh']}**\n\n"
        msg += f"🏥 Chuyên khoa: **{benh['khoa']}**\n"
        msg += f"📊 Mức độ: **{benh['muc_do'].upper()}**\n\n"
        msg += f"💡 {benh['loi_khuyen']}\n\n"

        if len(top["matched"]) > 1:
            msg += f"📌 Triệu chứng nhận diện: {', '.join(top['matched'][:5])}\n\n"

        if len(matches) > 1:
            msg += "🔍 **Bệnh khác có thể liên quan:**\n"
            for m in matches[1:4]:
                b = m["benh"]
                ic = "🔴" if b["muc_do"] == "cao" else "🟡" if b["muc_do"] == "trung bình" else "🟢"
                msg += f"{ic} {b['benh']} ({b['khoa']})\n"
            msg += "\n"

        bac_si_list = ChatbotService._goi_y_bac_si(benh['khoa'])
        if bac_si_list:
            msg += "👨‍⚕️ **Bác sĩ gợi ý:**\n"
            for bs in bac_si_list[:3]:
                msg += f"• {bs['ten_hien_thi']} - {bs.get('benh_vien','')} ({int(bs.get('gia_kham',0)):,}đ)\n"

        msg += "\n⚕️ _Lưu ý: Đây chỉ là tham khảo, không thay thế chẩn đoán bác sĩ._"

        return {
            'type': 'symptom',
            'message': msg,
            'chuyen_khoa': benh['khoa'],
            'bac_si': bac_si_list[:3] if bac_si_list else [],
            'suggestions': ['Đặt lịch ngay', 'Xem thêm bác sĩ', 'Hỏi triệu chứng khác']
        }

    @staticmethod
    def _goi_y_bac_si(ten_chuyen_khoa):
        """Gợi ý bác sĩ theo tên chuyên khoa"""
        try:
            result = BacSiModel.tim_bac_si(search=ten_chuyen_khoa, per_page=3)
            return result.get('danh_sach', result.get('items', []))
        except Exception:
            return []

    @staticmethod
    def lay_goi_y_nhanh():
        """Lấy danh sách câu hỏi gợi ý nhanh"""
        return [
            'Tôi bị đau bụng',
            'Tôi bị đau đầu',
            'Tôi bị đau họng',
            'Tôi bị ho sốt',
            'Đau lưng',
            'Đau ngực khó thở',
            'Mất ngủ',
            'Giờ khám bệnh',
            'Chi phí khám',
            'Cách đặt lịch khám',
        ]
