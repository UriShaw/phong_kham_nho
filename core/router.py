"""
Router - Đăng ký tất cả blueprints/routes
"""


def register_routes(app):
    """Đăng ký tất cả controller routes vào Flask app"""

    # Import controllers
    from app.controllers.auth_controller import auth_bp
    from app.controllers.benh_nhan_controller import benh_nhan_bp
    from app.controllers.bac_si_controller import bac_si_bp
    from app.controllers.lich_kham_controller import lich_kham_bp
    from app.controllers.ho_so_controller import ho_so_bp
    from app.controllers.thanh_toan_controller import thanh_toan_bp
    from app.controllers.chatbot_controller import chatbot_bp
    from app.controllers.admin_controller import admin_bp
    from app.controllers.tien_ich_controller import tien_ich_bp

    # Đăng ký blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(benh_nhan_bp)
    app.register_blueprint(bac_si_bp, url_prefix='/bac-si')
    app.register_blueprint(lich_kham_bp, url_prefix='/lich-kham')
    app.register_blueprint(ho_so_bp, url_prefix='/ho-so')
    app.register_blueprint(thanh_toan_bp, url_prefix='/thanh-toan')
    app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(tien_ich_bp, url_prefix='/tien-ich')

    print("[OK] Dang ky routes thanh cong!")
