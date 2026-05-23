"""
Chatbot Controller - API chatbot tư vấn sức khỏe
"""
from flask import Blueprint, request
from core.controller import BaseController
from app.services.chatbot_service import ChatbotService

chatbot_bp = Blueprint('chatbot', __name__)


@chatbot_bp.route('/message', methods=['POST'])
def gui_tin_nhan():
    """API xử lý tin nhắn chatbot"""
    data = request.get_json()
    message = data.get('message', '')

    if not message.strip():
        return BaseController.json_error('Vui lòng nhập tin nhắn')

    response = ChatbotService.xu_ly_tin_nhan(message)
    return BaseController.json_response(response)


@chatbot_bp.route('/suggestions')
def goi_y():
    """API lấy gợi ý câu hỏi nhanh"""
    suggestions = ChatbotService.lay_goi_y_nhanh()
    return BaseController.json_response({'suggestions': suggestions})
