"""
Thanh Toán Controller - Thanh toán QR MB Bank
"""
from flask import Blueprint, request, session, redirect, url_for, flash
from core.controller import BaseController
from core.middleware import login_required
from app.services.payment_service import PaymentService

thanh_toan_bp = Blueprint('thanh_toan', __name__)


@thanh_toan_bp.route('/<int:lich_id>')
@login_required
def thanh_toan(lich_id):
    """Trang thanh toán QR"""
    payment_info = PaymentService.lay_thong_tin_thanh_toan(lich_id)
    if not payment_info:
        flash('Không tìm thấy thông tin thanh toán.', 'danger')
        return redirect(url_for('lich_kham.danh_sach'))

    return BaseController.render('thanh_toan.html', payment=payment_info)


@thanh_toan_bp.route('/xac-nhan/<int:lich_id>', methods=['POST'])
@login_required
def xac_nhan(lich_id):
    """Xác nhận đã chuyển khoản"""
    benh_nhan_id = session.get('benh_nhan_id')

    success, message = PaymentService.xac_nhan_da_chuyen(lich_id, benh_nhan_id)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if success:
            return BaseController.json_response(message=message)
        return BaseController.json_error(message=message)

    if success:
        flash(message, 'success')
        return redirect(url_for('lich_kham.danh_sach'))
    else:
        flash(message, 'danger')
        return redirect(url_for('thanh_toan.thanh_toan', lich_id=lich_id))
