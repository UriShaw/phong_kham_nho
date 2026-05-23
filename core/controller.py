"""
Base Controller - Lớp cơ sở cho controllers
Cung cấp helpers render template, JSON response
"""
from flask import render_template, jsonify, redirect, url_for, flash, request


class BaseController:
    """Lớp controller cơ sở"""

    @staticmethod
    def render(template, **kwargs):
        """Render template với dữ liệu"""
        return render_template(template, **kwargs)

    @staticmethod
    def json_response(data=None, message="Thành công", status=200, success=True):
        """Trả về JSON response chuẩn"""
        response = {
            'success': success,
            'message': message,
        }
        if data is not None:
            response['data'] = data
        return jsonify(response), status

    @staticmethod
    def json_error(message="Có lỗi xảy ra", status=400, errors=None):
        """Trả về JSON error"""
        response = {
            'success': False,
            'message': message,
        }
        if errors:
            response['errors'] = errors
        return jsonify(response), status

    @staticmethod
    def redirect_to(endpoint, **kwargs):
        """Chuyển hướng đến route"""
        return redirect(url_for(endpoint, **kwargs))

    @staticmethod
    def flash_message(message, category='info'):
        """Thông báo flash"""
        flash(message, category)

    @staticmethod
    def get_page():
        """Lấy số trang từ query string"""
        try:
            return max(1, int(request.args.get('page', 1)))
        except (ValueError, TypeError):
            return 1

    @staticmethod
    def get_search():
        """Lấy từ khóa tìm kiếm"""
        return request.args.get('q', '').strip()
