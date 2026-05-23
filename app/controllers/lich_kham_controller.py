"""
Lịch Khám Controller - Đặt lịch, xem lịch, hủy lịch
"""
from flask import Blueprint, request, session, redirect, url_for, flash
from core.controller import BaseController
from core.middleware import login_required, generate_csrf_token
from app.services.booking_service import BookingService
from app.models.lich_kham_model import LichKhamModel
from app.models.bac_si_model import BacSiModel
from app.models.danh_gia_model import DanhGiaBacSiModel

lich_kham_bp = Blueprint('lich_kham', __name__)


@lich_kham_bp.route('/dat-lich/<int:bac_si_id>', methods=['GET', 'POST'])
@login_required
def dat_lich(bac_si_id):
    """Đặt lịch khám - Bước 2: Chọn ngày giờ"""
    bac_si = BacSiModel.lay_chi_tiet(bac_si_id)
    if not bac_si:
        flash('Không tìm thấy bác sĩ.', 'danger')
        return redirect(url_for('benh_nhan.tim_bac_si'))

    if request.method == 'POST':
        benh_nhan_id = session.get('benh_nhan_id')
        if not benh_nhan_id:
            flash('Vui lòng hoàn thiện hồ sơ bệnh nhân.', 'warning')
            return redirect(url_for('ho_so.ho_so'))

        ngay_kham = request.form.get('ngay_kham')
        gio_kham = request.form.get('gio_kham')
        ly_do = request.form.get('ly_do', '')

        if not ngay_kham or not gio_kham:
            flash('Vui lòng chọn ngày và giờ khám.', 'danger')
            return redirect(url_for('lich_kham.dat_lich', bac_si_id=bac_si_id))

        success, message, data = BookingService.dat_lich(
            benh_nhan_id=benh_nhan_id,
            bac_si_id=bac_si_id,
            ngay_kham=ngay_kham,
            gio_kham=gio_kham,
            ly_do=ly_do
        )

        if success:
            flash('Đặt lịch thành công! 🎉', 'success')
            return redirect(url_for('thanh_toan.thanh_toan', lich_id=data['lich_kham_id']))
        else:
            flash(message, 'danger')

    return BaseController.render('dat_lich.html',
        bac_si=bac_si
    )


@lich_kham_bp.route('/api/slots/<int:bac_si_id>/<ngay_kham>')
@login_required
def api_slots(bac_si_id, ngay_kham):
    """API lấy khung giờ trống"""
    slots = BookingService.lay_slots(bac_si_id, ngay_kham)
    return BaseController.json_response({'slots': slots})


@lich_kham_bp.route('/')
@login_required
def danh_sach():
    """Danh sách lịch khám của bệnh nhân"""
    benh_nhan_id = session.get('benh_nhan_id')
    trang_thai = request.args.get('trang_thai')

    lich_list = LichKhamModel.lich_cua_benh_nhan(benh_nhan_id, trang_thai)

    # Lấy danh sách bác sĩ đã đánh giá
    reviewed = {}
    if benh_nhan_id:
        from core.database import db
        rows = db.query(
            "SELECT bac_si_id, id, diem, noi_dung FROM danh_gia_bac_si WHERE benh_nhan_id = %s",
            (benh_nhan_id,)
        )
        for r in rows:
            reviewed[r['bac_si_id']] = r

    return BaseController.render('lich_kham.html', lich_list=lich_list, reviewed=reviewed)


@lich_kham_bp.route('/<int:lich_id>')
@login_required
def chi_tiet(lich_id):
    """Chi tiết lịch khám"""
    lich = LichKhamModel.chi_tiet_lich(lich_id)
    if not lich:
        return BaseController.render('404.html'), 404

    return BaseController.render('chi_tiet_lich.html', lich=lich)


@lich_kham_bp.route('/huy/<int:lich_id>', methods=['POST'])
@login_required
def huy_lich(lich_id):
    """Hủy lịch khám"""
    benh_nhan_id = session.get('benh_nhan_id')
    success, message = BookingService.huy_lich(lich_id, benh_nhan_id)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('lich_kham.danh_sach'))


@lich_kham_bp.route('/cap-nhat/<int:lich_id>', methods=['POST'])
@login_required
def cap_nhat_lich(lich_id):
    """Cập nhật ngày/giờ lịch khám (chỉ khi chờ xác nhận)"""
    benh_nhan_id = session.get('benh_nhan_id')
    lich = LichKhamModel.chi_tiet_lich(lich_id)

    if not lich:
        flash('Không tìm thấy lịch khám.', 'danger')
        return redirect(url_for('lich_kham.danh_sach'))

    if lich.get('benh_nhan_id') != benh_nhan_id:
        flash('Bạn không có quyền sửa lịch này.', 'danger')
        return redirect(url_for('lich_kham.danh_sach'))

    if lich['trang_thai'] not in ('cho_xac_nhan', 'cho_thanh_toan'):
        flash('Chỉ có thể sửa lịch đang chờ xác nhận.', 'warning')
        return redirect(url_for('lich_kham.danh_sach'))

    ngay_moi = request.form.get('ngay_kham')
    gio_moi = request.form.get('gio_kham')
    ly_do_moi = request.form.get('ly_do', lich.get('ly_do', ''))

    if not ngay_moi or not gio_moi:
        flash('Vui lòng chọn ngày và giờ mới.', 'danger')
        return redirect(url_for('lich_kham.danh_sach'))

    # Kiểm tra trùng lịch
    from core.database import db
    trung = db.get_one("""
        SELECT id FROM lich_kham
        WHERE bac_si_id = %s AND ngay_kham = %s AND gio_kham = %s
        AND id != %s AND trang_thai NOT IN ('da_huy', 'hoan_thanh')
    """, (lich['bac_si_id'], ngay_moi, gio_moi, lich_id))

    if trung:
        flash('Khung giờ này đã có người đặt. Vui lòng chọn giờ khác.', 'danger')
        return redirect(url_for('lich_kham.danh_sach'))

    LichKhamModel.update(lich_id, {
        'ngay_kham': ngay_moi,
        'gio_kham': gio_moi,
        'ly_do': ly_do_moi,
    })
    flash('Đã cập nhật lịch hẹn thành công! ✅', 'success')
    return redirect(url_for('lich_kham.danh_sach'))


@lich_kham_bp.route('/api/trang-thai', methods=['POST'])
@login_required
def api_trang_thai():
    """API kiểm tra trạng thái lịch khám (realtime polling)"""
    data = request.get_json()
    lich_ids = data.get('ids', [])
    result = LichKhamModel.kiem_tra_trang_thai(lich_ids)
    return BaseController.json_response({'statuses': result})
