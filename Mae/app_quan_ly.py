from Mae import app, db, login_manager

from datetime import datetime, timedelta
import calendar

from flask import Flask, render_template, redirect, url_for, request, session, flash, Markup

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose
import flask_admin as admin
import flask_login as login

from flask_login import current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy.orm import sessionmaker, configure_mappers
from sqlalchemy import exc,asc,desc, and_, or_
from flask_sqlalchemy import Pagination

from flask_sqlalchemy import BaseQuery

from Mae.xu_ly.xu_ly_model import *
from Mae.xu_ly.xu_ly_form import *
from Mae.xu_ly.xu_ly import *


class MyAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('dang_nhap'))
        return super(MyAdminIndexView, self).render('admin/index.html')

class admin_view(ModelView):
    column_display_pk = True
    can_create = True
    can_delete = True
    can_export = False

@app.route('/', methods=['GET','POST'])
def index():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    dia_chi_frame = url_for('ql_don_hang')
    if request.form.get('Th_Ma_so'):
        man_hinh = request.form.get('Th_Ma_so')
        if man_hinh == "QL_Don_hang":
            dia_chi_frame = "/QL-don-hang"
        elif man_hinh == "QL_Kho":
            dia_chi_frame = url_for('ql_kho')
        elif man_hinh == "QL_Doanh_thu":
            dia_chi_frame = "/QL-doanh-thu"
        elif man_hinh == "Admin":
            dia_chi_frame = "/admin"    
        
    return render_template('Quan_ly/MH_Chinh.html', dia_chi_frame = dia_chi_frame)

@app.route('/cap-nhat-don-hang',methods=['GET','POST'])
def cap_nhat_tu_API():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    dia_chi = url_for('cap_nhat_tu_API')
    ten = "đơn hàng"
    thong_bao = ''
    if request.method == 'POST':
        for item in Lay_danh_sach_order():
            order = Lay_thong_tin_chi_tiet_order(item['salesOrder']['orderNumber'])
            cap_nhat_hoa_don_database(order)
        thong_bao = "Cập nhật hoàn tất lúc %s" % datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    return render_template('Quan_ly/QL_don_hang/Cap_nhat_don_hang.html',ten = ten, thong_bao = thong_bao, dia_chi = dia_chi)

@app.route('/QL-don-hang', methods =['GET','POST'])
def ql_don_hang():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    dia_chi = url_for('ql_don_hang_tao_don_moi')
    if request.form.get('Th_hoa_don'):
        dieu_khien = request.form.get('Th_hoa_don')
        if dieu_khien == 'DonHoan':
            dia_chi = url_for('ql_don_hang_hoan',page=1)
        elif dieu_khien == 'TraCuu':
            dia_chi = url_for('ql_don_hang_theo_ma',page=1)
        elif dieu_khien == 'TaoDonMoi':
            dia_chi = url_for('ql_don_hang_tao_don_moi')
        
        
        
    return render_template('Quan_ly/MH_QL_don_hang.html', dia_chi = dia_chi)

#------------------Tạo đơn mới

@app.route("/QL-don-hang/new", methods = ['GET','POST'])
def ql_don_hang_tao_don_moi():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form_hoa_don = Form_hoa_don()
    thong_bao = ''
    today = datetime.now()
    if form_hoa_don.validate_on_submit():
        ma_hd_kenh_ban = form_hoa_don.ma_don_hang.data
        kiem_tra = Hoa_don.query.filter(Hoa_don.ma_hoa_don_kenh_ban == ma_hd_kenh_ban).first()
        
        if kiem_tra:
            thong_bao = 'Mã đơn hàng đã tồn tại! Vui lòng kiểm tra lại thông tin!'
        else:
            ma_kh = form_hoa_don.tao_khach_hang()
            if form_hoa_don.ngay_tao.data == today.date():
                ma_hd = form_hoa_don.tao_hoa_don(today,ma_kh)
            else:
                ma_hd = form_hoa_don.tao_hoa_don(form_hoa_don.ngay_tao.data,ma_kh)
            return redirect(url_for('ql_don_hang_tao_don_moi_detail',ma_hd = ma_hd,page=1))
                   
   
    return render_template('Quan_ly/QL_don_hang/Tao_don_hang_moi.html',today = today, form_hoa_don = form_hoa_don, thong_bao = thong_bao)

@app.route('/QL-don-hang/new/hd_<int:ma_hd>/<int:page>',methods = ['GET','POST'])
def ql_don_hang_tao_don_moi_detail(ma_hd,page=1):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    
    form = Form_tim_kiem_nhap_hang()
    hoa_don = Hoa_don.query.filter(Hoa_don.ma_hoa_don == ma_hd).first()
    don_hang = Don_hang.query.filter(Don_hang.ma_hoa_don == ma_hd).all()
    page_filter = San_pham.query.paginate(page,10,False)
    thong_bao = ''
    
    if form.validate_on_submit() and form.noi_dung.data != '':
        ten_sp = form.noi_dung.data.strip().lower()
        if ten_sp.isdigit():
            page_filter = San_pham.query.filter_by(ma_san_pham = int(ten_sp)).paginate(page,10,False)
        else:
            chuoi_truy_van = '%'+ten_sp.lower()+'%'
            page_filter = San_pham.query.filter(San_pham.ten_san_pham.like(chuoi_truy_van)).paginate(page,10,False)
        if len(page_filter.items) == 0:
            thong_bao = 'Không tìm thấy sản phẩm!'
        
        
    
    return render_template('Quan_ly/QL_don_hang/Chi_tiet_don_hang.html', don_hang = don_hang, thong_bao = thong_bao, page_filter = page_filter, form = form, hoa_don = hoa_don)

@app.route('/QL-don-hang/new/hd_<int:ma_hd>/them_sp_<int:ma_sp>',methods=['GET','POST'])
def ql_don_hang_them_vao_don_hang(ma_hd, ma_sp):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    if not ma_hd:
        return redirect(url_for('ql_don_hang_tao_don_moi'))
    don_hang = Don_hang()
    san_pham = San_pham.query.filter_by(ma_san_pham = ma_sp).first()
    don_hang.ma_hoa_don = ma_hd
    don_hang.ma_san_pham = ma_sp
    don_hang.ten_san_pham = san_pham.ten_san_pham
    don_hang.so_luong = 1
    don_hang.gia_ban = san_pham.gia_ban
    don_hang.gia_nhap = san_pham.gia_nhap
    don_hang.loi_nhuan = san_pham.gia_ban - san_pham.gia_nhap
    db.session.add(don_hang)
    db.session.commit()
    return redirect(url_for('ql_don_hang_tao_don_moi_detail', ma_hd=ma_hd,page=1))

@app.route('/QL-don-hang/new/hd_<int:ma_hd>/xoa_sp_<int:ma_sp>',methods=['GET','POST'])
def ql_don_hang_xoa_khoi_don_hang(ma_hd, ma_sp):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    if not ma_hd:
        return redirect(url_for('ql_don_hang_tao_don_moi'))
    don_hang = Don_hang.query.filter(and_(Don_hang.ma_hoa_don == ma_hd,Don_hang.ma_san_pham == ma_sp)).first()
    db.session.delete(don_hang)
    db.session.commit()
    return redirect(url_for('ql_don_hang_tao_don_moi_detail', ma_hd=ma_hd,page=1))

@app.route('/QL-don-hang/new/hd_<int:ma_hd>/xoa_sp_2_<int:ma_sp>',methods=['GET','POST'])
def ql_don_hang_xoa_khoi_don_hang_2(ma_hd, ma_sp):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    if not ma_hd:
        return redirect(url_for('ql_don_hang_tao_don_moi'))
    don_hang = Don_hang.query.filter(and_(Don_hang.ma_hoa_don == ma_hd,Don_hang.ma_san_pham == ma_sp)).first()
    db.session.delete(don_hang)
    db.session.commit()
    return redirect(url_for('ql_don_hang_confirm', ma_hd=ma_hd))

@app.route('/QL-don-hang/new/hd_<int:ma_hd>/cap_nhat_sp_<int:ma_sp>',methods=['GET','POST'])
def ql_don_hang_cap_nhat_don_hang(ma_hd, ma_sp):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    if not ma_hd:
        return redirect(url_for('ql_don_hang_tao_don_moi'))
    form_don_hang = Form_xac_nhan_don_hang()
    don_hang = Don_hang.query.filter(and_(Don_hang.ma_hoa_don == ma_hd,Don_hang.ma_san_pham == ma_sp)).first()
    if form_don_hang.is_submitted():
        don_hang.so_luong = form_don_hang.so_luong.data
        don_hang.gia_ban = form_don_hang.gia_ban.data
        don_hang.gia_nhap = form_don_hang.gia_nhap.data
        don_hang.loi_nhuan = int(form_don_hang.gia_ban.data) - int(form_don_hang.gia_nhap.data)
        db.session.add(don_hang)
        db.session.commit()
        return redirect(url_for('ql_don_hang_confirm', ma_hd=ma_hd))
    else:
        return "<h1>Lỗi Cập nhật</h1>"

@app.route('/QL-don-hang/new/hd_<int:ma_hd>/confirm',methods=['GET','POST'])
def ql_don_hang_confirm(ma_hd):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form_hoa_don = Form_hoa_don()
    form_don_hang = Form_xac_nhan_don_hang()
    hoa_don = Hoa_don.query.filter(Hoa_don.ma_hoa_don == ma_hd).first()
    khach_hang = Khach_hang.query.filter(Khach_hang.ma_khach_hang == hoa_don.ma_khach_hang).first()
    don_hang = Don_hang.query.filter(Don_hang.ma_hoa_don == ma_hd).all()
    tong_tien = 0
    tong_loi_nhuan = 0
    for item in don_hang:
        tong_tien += item.gia_ban * item.so_luong
        tong_loi_nhuan += (item.gia_ban-item.gia_nhap)*item.so_luong
    tong_loi_nhuan -= hoa_don.giam_gia

    return render_template('Quan_ly/QL_don_hang/Xac_nhan_don_hang.html', tong_loi_nhuan = tong_loi_nhuan, tong_tien = tong_tien, form_don_hang = form_don_hang, form_hoa_don = form_hoa_don, khach_hang = khach_hang, hoa_don = hoa_don, don_hang = don_hang)

@app.route('/QL-don-hang/fix/hd_<int:ma_hd>',methods=['GET','POST'])
def ql_don_hang_confirm_detail(ma_hd):
    hoa_don = Hoa_don.query.filter(Hoa_don.ma_hoa_don == ma_hd).first()
    # khach_hang = Khach_hang.query.filter(Khach_hang.ma_khach_hang == hoa_don.ma_khach_hang).first()
    form = Form_hoa_don()
    # hoa_don.ma_hoa_don_kenh_ban = form.ma_don_hang.data
    # hoa_don.kenh_ban = form.kenh_ban.data
    # khach_hang.dia_chi = form.dia_chi.data
    # khach_hang.dien_thoai = form.so_dien_thoai.data
    # hoa_don.nha_van_chuyen = form.nha_van_chuyen.data
    hoa_don.giam_gia = form.giam_gia.data
    # hoa_don.ma_van_don = form.ma_van_don.data
    # hoa_don.ghi_chu = form.ghi_chu.data
    db.session.add(hoa_don)
    db.session.commit()
    return redirect(url_for('ql_don_hang_confirm',ma_hd=ma_hd))

@app.route('/QL-kho/cap-nhat-kho-hang/hd_<int:hd_id>', methods =['GET','POST'])
def ql_kho_xuat_hang(hd_id):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    
    hd = Hoa_don.query.filter(Hoa_don.ma_hoa_don == hd_id).first()
    kh = Khach_hang.query.filter(Khach_hang.ma_khach_hang == hd.ma_khach_hang).first()
    don_hang = Don_hang.query.filter(Don_hang.ma_hoa_don == hd_id).all()
    tong_tien = 0
    for item in don_hang:
        sp = San_pham.query.filter(San_pham.ma_san_pham == item.ma_san_pham).first()
        sp.so_luong_ton -= item.so_luong
        tong_tien += item.so_luong * item.gia_ban
        db.session.add(sp)
        db.session.commit()
    hd.tong_tien = tong_tien    
    hd.da_cap_nhat_kho = 1
    db.session.add(hd)
    db.session.commit()
    return redirect(url_for('in_hoa_don', hd_id = hd_id))

@app.route("/Ql-don-hang/in-hoa-don/hd_<int:hd_id>", methods =['GET','POST'])
def in_hoa_don(hd_id):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    hoa_don = Hoa_don.query.filter(Hoa_don.ma_hoa_don == hd_id).first()
    don_hang = Don_hang.query.filter(Don_hang.ma_hoa_don == hd_id).all()
    khach_hang = Khach_hang.query.filter(Khach_hang.ma_khach_hang == hoa_don.ma_khach_hang).first()
    tong_tien = 0
    
    for item in don_hang:
        tong_tien += item.gia_ban * item.so_luong
    tong_tien_don = tong_tien + hoa_don.phi_van_chuyen
    
    return render_template('Quan_ly/QL_don_hang/Hoa_don.html', tong_tien_don = tong_tien_don, khach_hang = khach_hang, hoa_don = hoa_don, don_hang = don_hang, tong_tien = tong_tien)


#------------------END TẠO ĐƠN MỚI

@app.route("/QL-don-hang/hoan/<int:page>", methods = ['GET','POST'])
def ql_don_hang_hoan(page):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form = Form_don_hang_hoan()
    page_filter = Hoa_don.query.join(Khach_hang).order_by(desc(Hoa_don.ngay_tao_hoa_don)).paginate(page,10,False)
    chuoi_thong_bao = ''
    if form.validate_on_submit():
        tim_kiem = form.ma_hoa_don.data.strip()
        
        page_filter = Hoa_don.query.join(Khach_hang).filter(Hoa_don.ma_hoa_don == tim_kiem).order_by(desc(Hoa_don.ngay_tao_hoa_don)).paginate(page,5,False)
        
        if len(page_filter.items) == 0:
            chuoi_thong_bao = 'Không tìm thấy mã hóa đơn ' + tim_kiem
    
    return render_template('/Quan_ly/QL_don_hang/QL_don_hang_theo_ma_hd.html',form = form, chuoi_thong_bao = chuoi_thong_bao, page_filter = page_filter)


@app.route("/QL-don-hang/theo-ma-hd/<int:page>", methods = ['GET','POST'])
def ql_don_hang_theo_ma(page):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form = Form_don_hang_hoan()
    page_filter = Hoa_don.query.join(Khach_hang).order_by(desc(Hoa_don.ngay_tao_hoa_don)).paginate(page,5,False)
    chuoi_thong_bao = ''
    if form.validate_on_submit():
        tim_kiem = form.ma_hoa_don.data.strip()
        
        page_filter = Hoa_don.query.join(Khach_hang).filter(Hoa_don.ma_hoa_don_kenh_ban == tim_kiem).order_by(desc(Hoa_don.ngay_tao_hoa_don)).paginate(page,5,False)
        
        if len(page_filter.items) == 0:
            chuoi_thong_bao = 'Không tìm thấy mã hóa đơn ' + tim_kiem
    dict_kh = {}
    if len(page_filter.items) > 0:
        for item in page_filter.items:
            kh = Khach_hang.query.filter(Khach_hang.ma_khach_hang == item.ma_khach_hang).first()
            dict_kh[item.ma_hoa_don] = kh.dien_thoai
                  
    return render_template('Quan_ly/QL_don_hang/QL_don_hang_theo_ma_hd.html', dict_kh = dict_kh, chuoi_thong_bao = chuoi_thong_bao, page_filter = page_filter, form = form)

@app.route('/QL-don-hang/chi-tiet/hd_<int:hd_id>', methods=['GET','POST'])
def chi_tiet_order(hd_id):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    hoa_don = Hoa_don.query.filter(Hoa_don.ma_hoa_don == hd_id).first()
    khach_hang = Khach_hang.query.filter(Khach_hang.ma_khach_hang == hoa_don.ma_khach_hang).first()
    don_hang = Don_hang.query.filter(Don_hang.ma_hoa_don == hd_id).all()
    tong_tien = 0
    for item in don_hang:
        tong_tien += item.so_luong * item.gia_ban
    return render_template('Quan_ly/QL_don_hang/QL_don_hang_chi_tiet.html', tong_tien = tong_tien, don_hang = don_hang, khach_hang = khach_hang, hoa_don = hoa_don)

@app.route('/QL-don-hang/hoan/cho-vao-kho/hd_<int:hd_id>',methods=['GET','POST'])
def don_hoan_cap_nhat_kho(hd_id):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    hoa_don = Hoa_don.query.filter(Hoa_don.ma_hoa_don == hd_id).first()
    don_hang = Don_hang.query.filter(Don_hang.ma_hoa_don == hd_id).all()
    for item in don_hang:
        sp = San_pham.query.filter(San_pham.ma_san_pham == item.ma_san_pham).first()
        sp.so_luong_ton += item.so_luong
        db.session.add(sp)
        db.session.commit()
    hoa_don.trang_thai = 13
    hoa_don.ghi_chu += '[ĐƠN HOÀN] ' + datetime.now().strftime("%d-%m-%Y %H:%S")
    db.session.add(hoa_don)
    db.session.commit()

    return redirect(url_for('chi_tiet_order',hd_id = hd_id))


@app.route('/QL-don-hang/xoa/<int:hd_id>', methods=['GET','POST'])
def ql_don_hang_xoa(hd_id):
    hoa_don = Hoa_don.query.filter(Hoa_don.ma_hoa_don == hd_id).first()
    don_hang = Don_hang.query.filter(Don_hang.ma_hoa_don == hd_id).all()
    for item in don_hang:
        db.session.delete(item)
        db.session.commit()
    db.session.delete(hoa_don)
    db.session.commit()

    return redirect(url_for('ql_don_hang_theo_ma',page=1))
#------------Kho
@app.route('/QL-kho/san-pham/moi',methods=['GET','POST'])
def ql_kho_san_pham_moi():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    thong_bao = ''
    form = Form_tao_san_pham()
    form.ten_loai.choices = tao_danh_sach_category()
    if form.validate_on_submit():
        ten_sp = form.ten_san_pham.data.strip()
        sp = San_pham.query.filter(San_pham.ten_san_pham == ten_sp.lower()).first()
        if sp:
            thong_bao = 'Sản phẩm đã tồn tại. Mã sp: ' + str(sp.ma_san_pham)
        else:
            ma_sp = form.ghi_vao_db()
            thong_bao = 'Ghi thành công! Mã sp: ' + str(ma_sp)

    return render_template('Quan_ly/QL_kho_hang/Tao_san_pham_moi.html', thong_bao = thong_bao,form=form)

@app.route('/QL-kho', methods = ['GET','POST'])
def ql_kho():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    dia_chi = url_for('ql_kho_san_pham_moi')
    if request.method == 'POST':
        dieu_khien = request.form.get('Th_kho_hang')
        if dieu_khien == 'NhapHang':
            dia_chi = url_for('ql_kho_nhap_hang',page=1)
        elif dieu_khien == 'SoLuongTon':
            dia_chi = url_for('ql_so_luong_ton',page=1)
        elif dieu_khien == 'SanPhamMoi':
            dia_chi = url_for('ql_kho_san_pham_moi')

    return render_template('Quan_ly/QL_kho_hang/MH_QL_kho_hang.html', dia_chi = dia_chi)

@app.route('/QL-kho/nhap-hang/<int:page>', methods = ['GET','POST'])
def ql_kho_nhap_hang(page):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form = Form_tim_kiem_nhap_hang()
    page_filter = San_pham.query.paginate(page,5,False)
    thong_bao = ''
    if form.validate_on_submit():
        tim_kiem = form.noi_dung.data
        
        if tim_kiem.isdigit():
            page_filter = San_pham.query.filter(San_pham.ma_san_pham == int(tim_kiem)).paginate(page,10,False)
        else:
            chuoi_truy_van = '%'+tim_kiem.lower()+'%'
            page_filter = San_pham.query.filter(San_pham.ten_san_pham.like(chuoi_truy_van)).paginate(page,10,False)
        if len(page_filter.items) == 0:
            thong_bao = 'Không tìm thấy sản phẩm!'

    return render_template('Quan_ly/QL_kho_hang/Nhap_hang.html', form = form, page_filter = page_filter, thong_bao = thong_bao)

@app.route('/QL-kho/nhap/sp_<int:ma_sp>', methods = ['GET','POST'])
def ql_kho_nhap_chi_tiet(ma_sp):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form = Form_nhap_hang()
    san_pham = San_pham.query.filter(San_pham.ma_san_pham == ma_sp).first()
    chuoi_thong_bao = ''
    today = datetime.now()
    if form.validate_on_submit():
        so_luong_nhap = form.so_luong_nhap.data
        san_pham.so_luong_ton += so_luong_nhap
        san_pham.gia_nhap = form.gia_nhap.data
        san_pham.current_nhap_hang = today.strftime("%d-%m-%Y %H:%M:%S")
        db.session.add(san_pham)
        db.session.commit()
        chuoi_thong_bao = "Đã thêm " + str(so_luong_nhap) + " "+ san_pham.ten_san_pham + " vào kho hàng"
    return render_template('Quan_ly/QL_kho_hang/Chi_tiet_nhap_hang.html', chuoi_thong_bao = chuoi_thong_bao, form = form, san_pham = san_pham)

@app.route('/QL-kho/cap-nhat-sp/sp_<int:ma_sp>', methods = ['GET','POST'])
def ql_cap_nhat_sp(ma_sp):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form = Form_cap_nhat_san_pham()
    san_pham = San_pham.query.filter(San_pham.ma_san_pham == ma_sp).first()
    loai = Loai_san_pham.query.filter(Loai_san_pham.ma_loai == san_pham.ma_loai).first()
    
    form.ten_loai.choices = tao_danh_sach_category()
    

    chuoi_thong_bao = ''
    today = datetime.now()
    if form.validate_on_submit():
        gia_ban_moi = form.gia_ban.data
        san_pham.gia_ban = gia_ban_moi
        san_pham.current_edit_price = today.strftime("%d-%m-%Y %H:%M:%S")
        san_pham.gia_nhap = form.gia_nhap.data

        db.session.add(san_pham)
        db.session.commit()
        chuoi_thong_bao = "Cập nhật thành công!"
    
    return render_template('Quan_ly/QL_kho_hang/Cap_nhat_san_pham.html', form = form, san_pham  = san_pham, chuoi_thong_bao = chuoi_thong_bao)

@app.route('/QL-kho/ton-kho/<int:page>', methods = ['GET', 'POST'])
def ql_so_luong_ton(page):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    # form_1 = Form_tim_kiem()
    form_1 = Form_tim_kiem()
    page_filter = San_pham.query.filter(San_pham.so_luong_ton<=0).paginate(page,5,False)
    if form_1.submit.data and form_1.validate_on_submit():
        tim_kiem = form_1.noi_dung.data
        if tim_kiem.isdigit():
            page_filter = San_pham.query.filter(San_pham.ma_san_pham == int(tim_kiem)).paginate(page,5,False)
        else:
            chuoi_truy_van = '%'+tim_kiem.lower()+'%'
            page_filter = San_pham.query.filter(San_pham.ten_san_pham.like(chuoi_truy_van)).paginate(page,5,False)
        if len(page_filter.items) == 0:
            thong_bao = 'Không tìm thấy sản phẩm!'
    
    return render_template('Quan_ly/QL_kho_hang/Ton_kho.html',form_1=form_1, page_filter = page_filter)



#----------------------DOANH THU

@app.route('/QL-doanh-thu', methods = ['GET','POST'])
def ql_doanh_thu():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    dia_chi = url_for('ql_doanh_thu_today')
    if request.method == 'POST':
        dieu_khien = request.form.get('Th_doanh_thu')
        if dieu_khien == 'ChiPhi':
            dia_chi = url_for('ql_doanh_thu_chi')
        elif dieu_khien == 'Today':
            dia_chi = url_for('ql_doanh_thu_today')
        elif dieu_khien == 'TheoNgay':
            dia_chi = url_for('ql_doanh_thu_theo_ngay')
        elif dieu_khien == 'TongKet':
            dia_chi = url_for('ql_doanh_thu_tong_ket')
        elif dieu_khien == 'Von':
            dia_chi = url_for('ql_doanh_thu_von')
    return render_template('Quan_ly/QL_doanh_thu/MH_QL_doanh_thu.html', dia_chi = dia_chi)

@app.route('/QL-doanh-thu/chi', methods =['GET','POST'])
def ql_doanh_thu_chi():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    today = datetime.now()
    ngay_dau_thang = datetime(today.year, today.month, 1)
    str_temp_1 = calendar.monthrange(today.year, today.month)
    ngay_cuoi_thang = datetime(today.year, today.month, str_temp_1[1])
    form_1 = Form_khoan_chi()
    form_2 = Form_xem_khoan_chi()
    
    
    chuoi_thong_bao = ''
    ds_chi = None
    if form_1.submit_1.data and form_1.validate_on_submit():
        khoan_chi = Thu_chi()
        khoan_chi.ten = form_1.ten.data
        khoan_chi.noi_dung = form_1.noi_dung.data
        khoan_chi.so_tien = form_1.so_tien.data
        khoan_chi.thoi_gian = today
        khoan_chi.loai = 1
        db.session.add(khoan_chi)
        db.session.commit()
        chuoi_thong_bao = 'Đã ghi thành công! ' + today.strftime('%d-%m-%Y %H:%M:%S')
    if form_2.submit_2.data and form_2.validate_on_submit():
        
        ds_chi = Thu_chi.query.filter(and_(Thu_chi.thoi_gian.between(form_2.tu_ngay.data,form_2.den_ngay.data)),Thu_chi.loai==1).all()
        
    return render_template('Quan_ly/QL_doanh_thu/Chi.html', ngay_dau_thang = ngay_dau_thang, ngay_cuoi_thang = ngay_cuoi_thang, ds_chi = ds_chi, form_2 = form_2, form_1 = form_1, chuoi_thong_bao = chuoi_thong_bao)

@app.route('/QL-doanh-thu/ngay-hom-nay', methods = ['GET','POST'])
def ql_doanh_thu_today():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    today = datetime.now()
    prev_day = datetime(today.year,today.month,today.day)
    ds_hoa_don = Hoa_don.query.filter(Hoa_don.ngay_tao_hoa_don.between(prev_day, today)).all()
    dict_sp_trong_ngay = {}
    dict_loi_nhuan_trong_ngay = {}
    tong_loi_nhuan = 0
   
    for hoa_don in ds_hoa_don:
        
        don_hang = Don_hang.query.filter(Don_hang.ma_hoa_don == hoa_don.ma_hoa_don).all()
        for san_pham in don_hang:
            
            if san_pham.ma_san_pham not in dict_sp_trong_ngay:
                dict_sp_trong_ngay[san_pham.ma_san_pham] = san_pham.so_luong
                dict_loi_nhuan_trong_ngay[san_pham.ma_san_pham] = san_pham.loi_nhuan * san_pham.so_luong

            else:
                dict_sp_trong_ngay[san_pham.ma_san_pham] += san_pham.so_luong
                dict_loi_nhuan_trong_ngay[san_pham.ma_san_pham] += san_pham.loi_nhuan * san_pham.so_luong


    lst_sp_trong_ngay = []
    for item in dict_sp_trong_ngay:
        san_pham = San_pham.query.filter(San_pham.ma_san_pham == item).first()
        
        dict_temp = {}
        dict_temp['ma_sp'] = item
        dict_temp['ten_sp'] = san_pham.ten_san_pham
        dict_temp['so_luong'] = dict_sp_trong_ngay[item]
        dict_temp['gia_ban'] = san_pham.gia_ban
        dict_temp['loi_nhuan'] = dict_loi_nhuan_trong_ngay[item]
        lst_sp_trong_ngay.append(dict_temp)
    for item in dict_loi_nhuan_trong_ngay:
        tong_loi_nhuan += dict_loi_nhuan_trong_ngay[item]
    
    ngay = "Ngày " + str(today.day) + " Tháng " + str(today.month) + " năm " + str(today.year)
    return render_template('Quan_ly/QL_doanh_thu/Doanh_thu_theo_ngay.html', ngay = ngay, tong_loi_nhuan = tong_loi_nhuan, lst_sp_trong_ngay  = lst_sp_trong_ngay)
    
@app.route('/QL-doanh-thu/theo-ngay', methods = ['GET','POST'])
def ql_doanh_thu_theo_ngay():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form = Form_xem_khoan_chi()
    today = datetime.now()
    ngay_dau_thang = datetime(today.year, today.month, 1)
    str_temp_1 = calendar.monthrange(today.year, today.month)
    ngay_cuoi_thang = datetime(today.year, today.month, str_temp_1[1])
    
    danh_sach_cac_ngay = []
    hoa_don = Hoa_don.query.order_by(Hoa_don.ngay_tao_hoa_don.asc()).all()
    if form.validate_on_submit():
        hoa_don = Hoa_don.query.filter(Hoa_don.ngay_tao_hoa_don.between(form.tu_ngay.data,form.den_ngay.data)).order_by(Hoa_don.ngay_tao_hoa_don.asc()).all()
    for item in hoa_don:
        dict_temp = {}
        dict_temp['ngay_tao_hoa_don'] = item.ngay_tao_hoa_don.strftime("%d-%m-%Y")
        if dict_temp not in danh_sach_cac_ngay:
            danh_sach_cac_ngay.append(dict_temp)
    
    tong_doanh_thu = 0
    danh_sach_hoa_don = []
    for item in hoa_don:
        if item.trang_thai != 13:
            doanh_thu_1_hoa_don = 0
            dict_temp = {}
            don_hang = Don_hang.query.filter(Don_hang.ma_hoa_don == item.ma_hoa_don).all()
            
            for item_1 in don_hang:
                tong_doanh_thu += item_1.gia_ban * item_1.so_luong
                doanh_thu_1_hoa_don += item_1.gia_ban * item_1.so_luong
                
            dict_temp['ngay_tao_hoa_don'] = item.ngay_tao_hoa_don.strftime("%d-%m-%Y")
            dict_temp['doanh_thu'] = doanh_thu_1_hoa_don
            danh_sach_hoa_don.append(dict_temp)
    
    for ngay in danh_sach_cac_ngay:
        doanh_thu_theo_ngay = 0
        for bill in danh_sach_hoa_don:
            if bill['ngay_tao_hoa_don'] == ngay['ngay_tao_hoa_don']:
                doanh_thu_theo_ngay += bill['doanh_thu']
        ngay['tong_doanh_thu'] = doanh_thu_theo_ngay
    
    
    return render_template('Quan_ly/QL_doanh_thu/Doanh_thu_all.html', form=form, danh_sach_cac_ngay = danh_sach_cac_ngay)



@app.route('/QL-doanh-thu/tong-ket',methods=['GET','POST'])
def ql_doanh_thu_tong_ket():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form = Form_xem_khoan_chi()
    today = datetime.now()
    ngay_dau_thang = datetime(today.year, today.month, 1)
    str_temp_1 = calendar.monthrange(today.year, today.month)
    ngay_cuoi_thang = datetime(today.year, today.month, str_temp_1[1]) + timedelta(days=1)
    tieu_de = 'Tính từ ngày ' + ngay_dau_thang.strftime("%d-%m-%Y") + ' đến ngày ' + ngay_cuoi_thang.strftime("%d-%m-%Y")
    ds_chi = Thu_chi.query.filter(Thu_chi.thoi_gian.between(ngay_dau_thang, ngay_cuoi_thang)).all()
    ds_hoa_don = Hoa_don.query.filter(Hoa_don.ngay_tao_hoa_don.between(ngay_dau_thang,ngay_cuoi_thang)).all()
    ds_san_pham = San_pham.query.all()
    if form.validate_on_submit():
        ds_chi =Thu_chi.query.filter(Thu_chi.thoi_gian.between(form.tu_ngay.data,form.den_ngay.data)).all()
        ds_hoa_don = Hoa_don.query.filter(Hoa_don.ngay_tao_hoa_don.between(form.tu_ngay.data,form.den_ngay.data)).all()
        tieu_de = 'Tính từ ngày ' + form.tu_ngay.data.strftime("%d-%m-%Y") + ' đến ngày ' + form.den_ngay.data.strftime("%d-%m-%Y")
    tong_chi_phi = 0
    for item in ds_chi:
        if item.loai == 1:
            tong_chi_phi += item.so_tien
    so_don_hoan = 0
    tong_thu = 0
    von = 0
    for hoa_don in ds_hoa_don:
        if hoa_don.trang_thai != 13:
            don_hang = Don_hang.query.filter(Don_hang.ma_hoa_don == hoa_don.ma_hoa_don).all()
            for dh in don_hang:
                tong_thu += dh.gia_ban * dh.so_luong
            tong_thu -= hoa_don.giam_gia
        else:
            so_don_hoan += 1
    tong_tien_hang = 0
    for sp in ds_san_pham:
        tong_tien_hang += (sp.gia_nhap*sp.so_luong_ton)
    for item in ds_chi:
        if item.loai == 2:
            von = item.so_tien
            break
    tong_loi_nhuan = tong_thu-tong_chi_phi-(tong_tien_hang-von)
    return render_template('Quan_ly/QL_doanh_thu/Tong_ket.html',von=von,tong_tien_hang = tong_tien_hang,tong_thu = tong_thu, tong_chi_phi = tong_chi_phi, so_don_hoan = so_don_hoan, tong_loi_nhuan = tong_loi_nhuan, tieu_de = tieu_de,form = form)    

@app.route('/QL-doanh-thu/von',methods=['GET','POST'])
def ql_doanh_thu_von():
    today = datetime.now()
    form_1 = Form_khoan_chi()
    von_object = Thu_chi.query.filter(Thu_chi.loai == 2).first()
    if von_object == None:
        von_object = Thu_chi()
        von_object.ten = "Vốn bị động"
        von_object.noi_dung = "Vốn bị động"
        von_object.loai = 2
        von_object.thoi_gian = today
        von_object.so_tien = 0
        db.session.add(von_object)
        db.session.commit()
    if form_1.validate_on_submit():
        if von_object == None:
            von_object = Thu_chi()
            von_object.ten = "Vốn bị động"
            von_object.noi_dung = "Vốn bị động"
            von_object.loai = 2
            von_object.thoi_gian = today
            von_object.so_tien = form_1.so_tien.data
            db.session.add(von_object)
            db.session.commit()
        else:
            von_object.so_tien = form_1.so_tien.data
            db.session.add(von_object)
            db.session.commit()

    return render_template('Quan_ly/QL_doanh_thu/Von.html', form_1=form_1, von=von_object)

#----------------------END DOANH THU

@app.route('/private/update', methods =['GET','POST'])
def private_update():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    ds_hoa_don = Hoa_don.query.all()
    for item in ds_hoa_don:
        item.giam_gia = 0
        db.session.add(item)
        db.session.commit()
    return redirect(url_for('index'))

admin = Admin(app, name = "Admin", index_view=MyAdminIndexView(name="Admin"), template_mode='bootstrap3')
admin.add_view(admin_view(Loai_nguoi_dung, db.session, 'Loại người dùng'))
admin.add_view(admin_view(Nguoi_dung, db.session, 'Người dùng'))
admin.add_view(admin_view(Loai_san_pham, db.session, 'Loại sản phẩm'))
admin.add_view(admin_view(San_pham, db.session, 'Sản phẩm'))
admin.add_view(admin_view(Khach_hang, db.session,'Khách hàng'))
admin.add_view(admin_view(Hoa_don, db.session, 'Hoá đơn'))
admin.add_view(admin_view(Don_hang, db.session, 'Đơn hàng'))
admin.add_view(admin_view(Thu_chi, db.session, 'Thu chi'))