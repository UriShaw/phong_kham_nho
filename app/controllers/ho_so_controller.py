"""
Hồ Sơ Controller - Hồ sơ bệnh án, sức khỏe, đơn thuốc, gia đình
Bệnh nhân: CRUD hồ sơ cá nhân + xem lịch sử khám
"""
from flask import Blueprint, request, session, flash, redirect, url_for
from core.controller import BaseController
from core.middleware import login_required
from app.models.benh_nhan_model import BenhNhanModel
from app.models.nguoi_dung_model import NguoiDungModel
from app.models.ho_so_model import HoSoModel
from app.models.don_thuoc_model import DonThuocModel
from app.services.health_score_service import HealthScoreService
from core.database import db

ho_so_bp = Blueprint('ho_so', __name__)


@ho_so_bp.route('/')
@login_required
def ho_so():
    """Trang hồ sơ sức khỏe tổng hợp"""
    benh_nhan_id = session.get('benh_nhan_id')
    user_id = session.get('user_id')

    # Thông tin bệnh nhân (kèm nguoi_dung)
    benh_nhan = None
    if benh_nhan_id:
        benh_nhan = db.get_one("""
            SELECT bn.*, nd.ho_ten, nd.email, nd.so_dien_thoai, nd.avatar
            FROM benh_nhan bn
            JOIN nguoi_dung nd ON bn.nguoi_dung_id = nd.id
            WHERE bn.id = %s
        """, (benh_nhan_id,))

    # Timeline lịch sử khám
    timeline = HoSoModel.timeline_benh_nhan(benh_nhan_id) if benh_nhan_id else []

    # Đơn thuốc kèm chi tiết
    don_thuoc_list = []
    if benh_nhan_id:
        raw_list = DonThuocModel.lay_tat_ca_theo_benh_nhan(benh_nhan_id)
        for don in raw_list:
            don['chi_tiet'] = DonThuocModel.lay_chi_tiet_cua_don(don['id'])
        don_thuoc_list = raw_list

    # Health Score
    health_score = HealthScoreService.tinh_diem(benh_nhan) if benh_nhan else {'diem': 0, 'nhan_xet': 'Chưa có dữ liệu'}

    # Gia đình
    gia_dinh = []
    if benh_nhan and benh_nhan.get('nhom_gia_dinh_id'):
        gia_dinh = BenhNhanModel.lay_gia_dinh(benh_nhan['nhom_gia_dinh_id'])

    return BaseController.render('ho_so.html',
        benh_nhan=benh_nhan,
        timeline=timeline,
        don_thuoc_list=don_thuoc_list,
        health_score=health_score,
        gia_dinh=gia_dinh
    )


@ho_so_bp.route('/cap-nhat', methods=['POST'])
@login_required
def cap_nhat():
    """Cập nhật thông tin cá nhân + sức khỏe"""
    benh_nhan_id = session.get('benh_nhan_id')
    user_id = session.get('user_id')

    if not benh_nhan_id:
        flash('Không tìm thấy hồ sơ.', 'danger')
        return redirect(url_for('ho_so.ho_so'))

    # Cập nhật bảng nguoi_dung
    nd_data = {}
    if request.form.get('ho_ten'):
        nd_data['ho_ten'] = request.form['ho_ten'].strip()
        session['ho_ten'] = nd_data['ho_ten']
    if request.form.get('so_dien_thoai'):
        nd_data['so_dien_thoai'] = request.form['so_dien_thoai'].strip()

    # Cập nhật email/gmail
    new_email = request.form.get('email', '').strip().lower()
    if new_email:
        existing = db.get_one(
            "SELECT id FROM nguoi_dung WHERE email = %s AND id != %s",
            (new_email, user_id)
        )
        if existing:
            flash('Email đã được sử dụng bởi tài khoản khác.', 'danger')
            return redirect(url_for('ho_so.ho_so'))
        nd_data['email'] = new_email
        session['email'] = new_email

    if nd_data:
        NguoiDungModel.update(user_id, nd_data)

    # Cập nhật bảng benh_nhan
    bn_data = {}
    for field in ('ngay_sinh', 'gioi_tinh', 'dia_chi', 'nhom_mau',
                  'tien_su_benh', 'di_ung', 'bao_hiem_y_te',
                  'nguoi_lien_he', 'sdt_lien_he', 'huyet_ap'):
        val = request.form.get(field)
        if val is not None:
            bn_data[field] = val.strip() if val else None

    for field in ('chieu_cao', 'can_nang', 'nhip_tim'):
        val = request.form.get(field)
        if val:
            try:
                bn_data[field] = float(val)
            except ValueError:
                pass

    if bn_data:
        BenhNhanModel.update(benh_nhan_id, bn_data)

    flash('Cập nhật hồ sơ thành công! ✅', 'success')
    return redirect(url_for('ho_so.ho_so'))


@ho_so_bp.route('/chi-tiet/<int:ho_so_id>')
@login_required
def chi_tiet_ho_so(ho_so_id):
    """Xem chi tiết một hồ sơ bệnh án"""
    benh_nhan_id = session.get('benh_nhan_id')
    bac_si_id = session.get('bac_si_id')
    vai_tro = session.get('vai_tro')

    # Build query based on role
    ho_so_ba = db.get_one("""
        SELECT hs.*, lk.ngay_kham, lk.gio_kham, lk.ly_do, lk.trieu_chung, lk.phong_kham,
               nd.ho_ten AS ten_bac_si, bs.hoc_vi, ck.ten_chuyen_khoa,
               CONCAT(bs.hoc_vi, ' ', nd.ho_ten) AS ten_hien_thi_bs,
               nd_bn.ho_ten AS ten_benh_nhan, bn.ma_benh_nhan,
               bn.gioi_tinh, bn.ngay_sinh, nd_bn.email AS email_bn,
               nd_bn.so_dien_thoai AS sdt_bn,
               bn.nhom_mau, bn.tien_su_benh, bn.di_ung,
               TIMESTAMPDIFF(YEAR, bn.ngay_sinh, CURDATE()) AS tuoi_bn
        FROM ho_so_benh_an hs
        JOIN lich_kham lk ON hs.lich_kham_id = lk.id
        JOIN bac_si bs ON hs.bac_si_id = bs.id
        JOIN nguoi_dung nd ON bs.nguoi_dung_id = nd.id
        JOIN chuyen_khoa ck ON bs.chuyen_khoa_id = ck.id
        JOIN benh_nhan bn ON hs.benh_nhan_id = bn.id
        JOIN nguoi_dung nd_bn ON bn.nguoi_dung_id = nd_bn.id
        WHERE hs.id = %s
    """, (ho_so_id,))

    if not ho_so_ba:
        flash('Không tìm thấy hồ sơ bệnh án.', 'warning')
        return redirect(url_for('ho_so.ho_so'))

    # Kiểm tra quyền truy cập
    if vai_tro == 'benh_nhan' and ho_so_ba['benh_nhan_id'] != benh_nhan_id:
        flash('Bạn không có quyền xem hồ sơ này.', 'danger')
        return redirect(url_for('ho_so.ho_so'))
    if vai_tro == 'bac_si' and ho_so_ba['bac_si_id'] != bac_si_id:
        flash('Bạn không có quyền xem hồ sơ này.', 'danger')
        return redirect(url_for('bac_si.dashboard'))

    # Đơn thuốc
    don_thuoc = DonThuocModel.lay_theo_ho_so(ho_so_id)

    return BaseController.render('chi_tiet_ho_so.html',
        ho_so=ho_so_ba,
        don_thuoc=don_thuoc,
        is_doctor=(vai_tro == 'bac_si')
    )


# ═══════════════════════════════════════════════════════════════════
# CHỈNH SỬA HỒ SƠ BỆNH ÁN (dành cho bác sĩ)
# ═══════════════════════════════════════════════════════════════════

@ho_so_bp.route('/sua/<int:ho_so_id>', methods=['POST'])
@login_required
def sua_ho_so(ho_so_id):
    """Bác sĩ sửa hồ sơ bệnh án"""
    bac_si_id = session.get('bac_si_id')
    if not bac_si_id:
        flash('Chỉ bác sĩ mới có quyền sửa.', 'danger')
        return redirect(url_for('ho_so.ho_so'))

    ho_so = HoSoModel.get_by_id(ho_so_id)
    if not ho_so or ho_so['bac_si_id'] != bac_si_id:
        flash('Không có quyền sửa hồ sơ này.', 'danger')
        return redirect(url_for('bac_si.dashboard'))

    data = {}
    for field in ('chan_doan', 'ghi_chu_lam_sang', 'huyet_ap', 'hen_tai_kham'):
        val = request.form.get(field)
        if val is not None:
            data[field] = val.strip()
    for field in ('nhip_tim', 'can_nang', 'nhiet_do'):
        val = request.form.get(field)
        if val:
            try:
                data[field] = float(val)
            except ValueError:
                pass

    HoSoModel.cap_nhat_ho_so(ho_so_id, data)
    flash('Đã cập nhật hồ sơ bệnh án! ✅', 'success')
    return redirect(url_for('ho_so.chi_tiet_ho_so', ho_so_id=ho_so_id))


@ho_so_bp.route('/xoa/<int:ho_so_id>', methods=['POST'])
@login_required
def xoa_ho_so(ho_so_id):
    """Bác sĩ xóa hồ sơ bệnh án"""
    bac_si_id = session.get('bac_si_id')
    if not bac_si_id:
        return BaseController.json_error('Chỉ bác sĩ mới có quyền xóa.', status=403)

    ho_so = HoSoModel.get_by_id(ho_so_id)
    if not ho_so or ho_so['bac_si_id'] != bac_si_id:
        return BaseController.json_error('Không có quyền xóa hồ sơ này.', status=403)

    HoSoModel.xoa_ho_so(ho_so_id)
    flash('Đã xóa hồ sơ bệnh án.', 'success')
    return redirect(url_for('bac_si.benh_nhan_cua_toi'))


# ═══════════════════════════════════════════════════════════════════
# API XEM ĐƠN THUỐC
# ═══════════════════════════════════════════════════════════════════

@ho_so_bp.route('/don-thuoc/<int:ho_so_id>')
@login_required
def xem_don_thuoc(ho_so_id):
    """API xem đơn thuốc theo hồ sơ"""
    benh_nhan_id = session.get('benh_nhan_id')
    bac_si_id = session.get('bac_si_id')
    don_thuoc = DonThuocModel.lay_theo_ho_so(ho_so_id)
    if not don_thuoc:
        return BaseController.json_error('Không tìm thấy đơn thuốc.', status=404)
    # Verify ownership (patient or doctor)
    if don_thuoc.get('benh_nhan_id') != benh_nhan_id and don_thuoc.get('bac_si_id') != bac_si_id:
        return BaseController.json_error('Không có quyền xem.', status=403)
    return BaseController.json_response(don_thuoc)


# ═══════════════════════════════════════════════════════════════════
# IN HỒ SƠ (trang in)
# ═══════════════════════════════════════════════════════════════════

@ho_so_bp.route('/in/<int:ho_so_id>')
@login_required
def in_ho_so(ho_so_id):
    """Trang in hồ sơ bệnh án"""
    ho_so_ba = HoSoModel.lay_chi_tiet_day_du(ho_so_id)
    if not ho_so_ba:
        flash('Không tìm thấy hồ sơ.', 'warning')
        return redirect(url_for('ho_so.ho_so'))

    # Verify access
    benh_nhan_id = session.get('benh_nhan_id')
    bac_si_id = session.get('bac_si_id')
    if ho_so_ba['benh_nhan_id'] != benh_nhan_id and ho_so_ba.get('bac_si_id') != bac_si_id:
        flash('Không có quyền in hồ sơ này.', 'danger')
        return redirect(url_for('ho_so.ho_so'))

    don_thuoc = DonThuocModel.lay_theo_ho_so(ho_so_id)
    return BaseController.render('in_ho_so.html', ho_so=ho_so_ba, don_thuoc=don_thuoc)
