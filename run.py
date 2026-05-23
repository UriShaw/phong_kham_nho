"""
App Entry Point - Khởi tạo Flask application
Hệ thống Quản Lý Dịch Vụ Chăm Sóc Sức Khỏe MedPro
"""
import os
import webbrowser
import threading
import json
import logging
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from flask import Flask, session, g, request
from flask.json.provider import DefaultJSONProvider
from config import Config
from core.middleware import generate_csrf_token


class MedProJSONProvider(DefaultJSONProvider):
    """Custom JSON provider xử lý timedelta, date, Decimal từ MySQL."""

    def default(self, o):
        if isinstance(o, timedelta):
            total = int(o.total_seconds())
            h, rem = divmod(total, 3600)
            m, s = divmod(rem, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, time):
            return o.isoformat()
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def create_app():
    """Factory tạo Flask app"""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(asctime)s %(name)s: %(message)s'
    )

    app = Flask(
        __name__,
        template_folder='app/views',
        static_folder='public/static',
        static_url_path='/static'
    )

    # Custom JSON provider — xử lý timedelta, date, Decimal từ MySQL
    app.json_provider_class = MedProJSONProvider
    app.json = MedProJSONProvider(app)

    # Cấu hình
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=Config.PERMANENT_SESSION_LIFETIME)

    # Tạo thư mục upload
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    # Context processor - truyền biến global vào templates
    @app.context_processor
    def inject_globals():
        """Truyền biến toàn cục vào mọi template"""
        from app.models.thong_bao_model import ThongBaoModel
        thong_bao_count = 0
        if 'user_id' in session:
            try:
                thong_bao_count = ThongBaoModel.dem_chua_doc(session['user_id'])
            except Exception:
                pass

        return {
            'current_user': {
                'id': session.get('user_id'),
                'ho_ten': session.get('ho_ten', ''),
                'email': session.get('email', ''),
                'vai_tro': session.get('vai_tro', ''),
                'avatar': session.get('avatar', ''),
            } if 'user_id' in session else None,
            'csrf_token': generate_csrf_token,
            'thong_bao_count': thong_bao_count,
        }

    # Đăng ký routes
    from core.router import register_routes
    register_routes(app)

    # Utility schema initialization (mood journal, health logs, etc.)

    # CSRF Validation cho POST requests
    from core.middleware import validate_csrf_token
    @app.before_request
    def csrf_protect():
        if request.method in ('POST', 'PUT', 'DELETE'):
            # Bỏ qua CSRF cho API JSON endpoints và file upload APIs
            if request.is_json or '/api/' in request.path or request.path.startswith('/tien-ich/api/'):
                return
            validate_csrf_token()

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return app.jinja_env.get_template('404.html').render(), 404

    @app.errorhandler(403)
    def forbidden(e):
        return app.jinja_env.get_template('403.html').render(), 403

    @app.errorhandler(500)
    def server_error(e):
        return '<h1>500 - Lỗi máy chủ</h1><p>Vui lòng thử lại sau.</p>', 500

    print("[MedPro] He thong Quan Ly Dich Vu Cham Soc Suc Khoe")
    print("[INFO] Truy cap: http://localhost:5000")

    return app


# Khởi chạy ứng dụng
if __name__ == '__main__':
    app = create_app()

    # Tự động mở trình duyệt (chỉ 1 lần, trong process chính)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        threading.Timer(1.5, lambda: webbrowser.open('http://localhost:5000')).start()

    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)
