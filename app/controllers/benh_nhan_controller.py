"""
Bệnh Nhân Controller - Trang chủ, Tìm bác sĩ, Lịch khám, Hồ sơ cá nhân
"""
from flask import Blueprint, request, session, flash, redirect, url_for
from core.controller import BaseController
from core.middleware import login_required, role_required
from app.models.bac_si_model import BacSiModel
from app.models.danh_gia_model import DanhGiaBacSiModel
from app.models.benh_nhan_model import BenhNhanModel
from app.models.nguoi_dung_model import NguoiDungModel
from app.models.chuyen_khoa_model import ChuyenKhoaModel
from app.models.lich_kham_model import LichKhamModel
from app.models.thong_bao_model import ThongBaoModel
from core.database import db

benh_nhan_bp = Blueprint('benh_nhan', __name__)


@benh_nhan_bp.route('/')
def trang_chu():
    """Trang chủ"""
    # Chuyên khoa
    chuyen_khoa_list = ChuyenKhoaModel.lay_tat_ca_hoat_dong()

    # Bác sĩ nổi bật
    bac_si_list = BacSiModel.bac_si_noi_bat(6)

    # Thống kê
    thong_ke = {
        'so_bac_si': BacSiModel.count("trang_thai_duyet = 'da_duyet'"),
        'so_benh_nhan': db.count('benh_nhan'),
        'so_lich_kham': db.count('lich_kham'),
        'so_chuyen_khoa': len(chuyen_khoa_list)
    }

    return BaseController.render('trang_chu.html',
        chuyen_khoa_list=chuyen_khoa_list,
        bac_si_list=bac_si_list,
        thong_ke=thong_ke
    )


@benh_nhan_bp.route('/tim-bac-si')
def tim_bac_si():
    """Tìm bác sĩ với bộ lọc — hỗ trợ tìm theo triệu chứng"""
    # Lấy filters
    chuyen_khoa_id = request.args.get('chuyen_khoa', type=int)
    search = request.args.get('q', '').strip()
    benh_vien = request.args.get('benh_vien', '').strip()
    gia_tu = request.args.get('gia_tu', type=int)
    gia_den = request.args.get('gia_den', type=int)
    sap_xep = request.args.get('sap_xep', 'danh_gia')
    page = request.args.get('page', 1, type=int)

    # ── Phát hiện triệu chứng từ search query ──
    symptom_matches = []
    matched_specialties = []
    if search and not chuyen_khoa_id:
        from app.services.benh_ly_data import BENH_LY_DB, TU_DONG_NGHIA
        search_lower = search.lower().strip()

        # Tạo danh sách tất cả từ khóa mở rộng
        expanded_keywords = {}
        for root, synonyms in TU_DONG_NGHIA.items():
            for syn in synonyms:
                expanded_keywords[syn.lower()] = root.lower()
            expanded_keywords[root.lower()] = root.lower()

        matched_diseases = []
        seen_diseases = set()
        for benh in BENH_LY_DB:
            for keyword in benh['tu_khoa']:
                kw_lower = keyword.lower()
                # Kiểm tra keyword có trong search query hoặc ngược lại
                if kw_lower in search_lower or search_lower in kw_lower:
                    if benh['benh'] not in seen_diseases:
                        matched_diseases.append({
                            'benh': benh['benh'],
                            'khoa': benh['khoa'],
                            'loi_khuyen': benh['loi_khuyen'],
                            'muc_do': benh.get('muc_do', 'trung bình'),
                            'matched_keyword': keyword
                        })
                        seen_diseases.add(benh['benh'])
                    break

            # Cũng kiểm tra từ đồng nghĩa
            if benh['benh'] not in seen_diseases:
                for kw in benh['tu_khoa']:
                    root = expanded_keywords.get(kw.lower())
                    if root and (root in search_lower or search_lower in root):
                        matched_diseases.append({
                            'benh': benh['benh'],
                            'khoa': benh['khoa'],
                            'loi_khuyen': benh['loi_khuyen'],
                            'muc_do': benh.get('muc_do', 'trung bình'),
                            'matched_keyword': kw
                        })
                        seen_diseases.add(benh['benh'])
                        break

        if matched_diseases:
            # Lấy các chuyên khoa unique
            seen_khoa = set()
            for d in matched_diseases:
                khoa = d['khoa']
                if khoa not in seen_khoa:
                    matched_specialties.append(khoa)
                    seen_khoa.add(khoa)
            symptom_matches = matched_diseases[:5]  # Tối đa 5 bệnh gợi ý

    # Tìm bác sĩ
    result = BacSiModel.tim_bac_si(
        chuyen_khoa_id=chuyen_khoa_id,
        search=search,
        benh_vien=benh_vien,
        gia_tu=gia_tu,
        gia_den=gia_den,
        sap_xep=sap_xep,
        page=page,
        per_page=10,
        matched_specialties=matched_specialties if matched_specialties else None
    )

    # Danh sách chuyên khoa cho filter
    chuyen_khoa_list = ChuyenKhoaModel.lay_tat_ca_hoat_dong()

    return BaseController.render('tim_bac_si.html',
        result=result,
        chuyen_khoa_list=chuyen_khoa_list,
        symptom_matches=symptom_matches,
        matched_specialties=matched_specialties,
        filters={
            'chuyen_khoa_id': chuyen_khoa_id,
            'search': search,
            'benh_vien': benh_vien,
            'gia_tu': gia_tu,
            'gia_den': gia_den,
            'sap_xep': sap_xep
        }
    )


@benh_nhan_bp.route('/bac-si/<int:bac_si_id>')
def chi_tiet_bac_si(bac_si_id):
    """Xem chi tiết bác sĩ"""
    bac_si = BacSiModel.lay_chi_tiet(bac_si_id)
    if not bac_si:
        return BaseController.render('404.html'), 404

    reviews = DanhGiaBacSiModel.lay_theo_bac_si(bac_si_id, limit=20)
    benh_nhan_id = session.get('benh_nhan_id')
    my_review = DanhGiaBacSiModel.da_danh_gia(bac_si_id, benh_nhan_id) if benh_nhan_id else None

    return BaseController.render('chi_tiet_bac_si.html',
        bac_si=bac_si, reviews=reviews, my_review=my_review)


@benh_nhan_bp.route('/api/danh-gia', methods=['POST'])
@login_required
def them_danh_gia():
    """Thêm đánh giá bác sĩ"""
    data = request.get_json() or request.form
    bac_si_id = int(data.get('bac_si_id', 0))
    diem = int(data.get('diem', 5))
    noi_dung = str(data.get('noi_dung', '')).strip()
    benh_nhan_id = session.get('benh_nhan_id')
    if not benh_nhan_id or not bac_si_id:
        return BaseController.json_response({'success': False, 'message': 'Thiếu thông tin'}), 400
    if diem < 1 or diem > 5:
        return BaseController.json_response({'success': False, 'message': 'Điểm từ 1-5'}), 400
    existing = DanhGiaBacSiModel.da_danh_gia(bac_si_id, benh_nhan_id)
    if existing:
        return BaseController.json_response({'success': False, 'message': 'Bạn đã đánh giá rồi'}), 400
    try:
        DanhGiaBacSiModel.them(bac_si_id, benh_nhan_id, diem, noi_dung)
        return BaseController.json_response({'success': True, 'message': 'Đánh giá thành công!'})
    except Exception as e:
        return BaseController.json_response({'success': False, 'message': str(e)}), 500


@benh_nhan_bp.route('/api/danh-gia/<int:danh_gia_id>', methods=['PUT'])
@login_required
def sua_danh_gia(danh_gia_id):
    """Sửa đánh giá"""
    data = request.get_json() or request.form
    diem = int(data.get('diem', 5))
    noi_dung = str(data.get('noi_dung', '')).strip()
    dg = DanhGiaBacSiModel.lay_theo_id(danh_gia_id)
    if not dg or dg['benh_nhan_id'] != session.get('benh_nhan_id'):
        return BaseController.json_response({'success': False, 'message': 'Không có quyền'}), 403
    DanhGiaBacSiModel.sua(danh_gia_id, diem, noi_dung)
    return BaseController.json_response({'success': True, 'message': 'Đã cập nhật!'})


@benh_nhan_bp.route('/api/danh-gia/<int:danh_gia_id>', methods=['DELETE'])
@login_required
def xoa_danh_gia(danh_gia_id):
    """Xóa đánh giá"""
    dg = DanhGiaBacSiModel.lay_theo_id(danh_gia_id)
    if not dg or dg['benh_nhan_id'] != session.get('benh_nhan_id'):
        return BaseController.json_response({'success': False, 'message': 'Không có quyền'}), 403
    DanhGiaBacSiModel.xoa(danh_gia_id)
    return BaseController.json_response({'success': True, 'message': 'Đã xóa!'})


@benh_nhan_bp.route('/thong-bao')
@login_required
def thong_bao():
    """Xem thông báo"""
    user_id = session.get('user_id')
    thong_bao_list = ThongBaoModel.lay_cua_nguoi_dung(user_id)
    return BaseController.render('thong_bao.html', thong_bao_list=thong_bao_list)


@benh_nhan_bp.route('/api/thong-bao/count')
@login_required
def dem_thong_bao():
    """API đếm thông báo chưa đọc"""
    user_id = session.get('user_id')
    count = ThongBaoModel.dem_chua_doc(user_id)
    return BaseController.json_response({'count': count})


# ═══════════════════════════════════════════════════════════════════
# HỒ SƠ CÁ NHÂN BỆNH NHÂN  (Read / Update)
# ═══════════════════════════════════════════════════════════════════

@benh_nhan_bp.route('/ho-so')
@login_required
def ho_so_ca_nhan():
    """Redirect sang trang hồ sơ tổng hợp."""
    return redirect(url_for('ho_so.ho_so'))


@benh_nhan_bp.route('/ho-so/cap-nhat', methods=['POST'])
@login_required
def cap_nhat_ho_so():
    """Cập nhật hồ sơ cá nhân bệnh nhân."""
    benh_nhan_id = session.get('benh_nhan_id')
    user_id = session.get('user_id')

    if not benh_nhan_id:
        flash('Không tìm thấy hồ sơ bệnh nhân.', 'danger')
        return redirect(url_for('benh_nhan.trang_chu'))

    # Cập nhật bảng nguoi_dung
    nd_data = {}
    if request.form.get('ho_ten'):
        nd_data['ho_ten'] = request.form['ho_ten'].strip()
        session['ho_ten'] = nd_data['ho_ten']
    if request.form.get('so_dien_thoai'):
        nd_data['so_dien_thoai'] = request.form['so_dien_thoai'].strip()

    # Cập nhật email
    new_email = request.form.get('email', '').strip().lower()
    if new_email:
        from core.database import db
        existing = db.get_one(
            "SELECT id FROM nguoi_dung WHERE email = %s AND id != %s",
            (new_email, user_id)
        )
        if existing:
            flash('Email đã được sử dụng bởi tài khoản khác.', 'danger')
            return redirect(url_for('benh_nhan.ho_so_ca_nhan'))
        nd_data['email'] = new_email
        session['email'] = new_email

    if nd_data:
        NguoiDungModel.update(user_id, nd_data)

    # Cập nhật bảng benh_nhan
    bn_data = {}
    for field in ('ngay_sinh', 'gioi_tinh', 'dia_chi', 'nhom_mau',
                  'tien_su_benh', 'di_ung', 'bao_hiem_y_te',
                  'nguoi_lien_he', 'sdt_lien_he'):
        val = request.form.get(field)
        if val is not None:
            bn_data[field] = val.strip() if val else None

    # Số liệu sức khỏe
    for field in ('chieu_cao', 'can_nang', 'nhip_tim'):
        val = request.form.get(field)
        if val:
            try:
                bn_data[field] = float(val)
            except ValueError:
                pass
    if request.form.get('huyet_ap'):
        bn_data['huyet_ap'] = request.form['huyet_ap'].strip()

    if bn_data:
        BenhNhanModel.update(benh_nhan_id, bn_data)

    flash('Đã cập nhật hồ sơ thành công!', 'success')
    return redirect(url_for('benh_nhan.ho_so_ca_nhan'))
