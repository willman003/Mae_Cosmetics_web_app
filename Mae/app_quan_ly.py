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

@app.route('/cap-nhat-san-pham',methods=['GET','POST'])
def cap_nhat_sp_tu_API():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    thong_bao = ''
    ten = "sản phẩm"
    dia_chi = url_for('cap_nhat_sp_tu_API')
    if request.method == 'POST':
        danh_sach_sp = dbSession.query(San_pham).all()
        for item in danh_sach_sp:
            sp = cap_nhat_san_pham(item)
            
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
            dia_chi = url_for('ql_don_hang_hoan')
        elif dieu_khien == 'TraCuu':
            dia_chi = url_for('ql_don_hang_theo_ma')
        elif dieu_khien == 'TaoDonMoi':
            dia_chi = url_for('ql_don_hang_tao_don_moi')
        
        
    return render_template('Quan_ly/MH_QL_don_hang.html', dia_chi = dia_chi)

#------------------Tạo đơn mới

@app.route("/QL-don-hang/new", methods = ['GET','POST'])
def ql_don_hang_tao_don_moi():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form_hoa_don = Form_hoa_don()
    
    if form_hoa_don.validate_on_submit():
        ma_kh = form_hoa_don.tao_khach_hang()
        ma_hd = form_hoa_don.tao_hoa_don(datetime.now(),ma_kh)
        return redirect(url_for('ql_don_hang_tao_don_moi_detail',ma_hd = ma_hd,page=1))
                   
   
    return render_template('Quan_ly/QL_don_hang/Tao_don_hang_moi.html',form_hoa_don = form_hoa_don)

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
    for item in don_hang:
        tong_tien += item.gia_ban * item.so_luong

    return render_template('Quan_ly/QL_don_hang/Xac_nhan_don_hang.html', tong_tien = tong_tien, form_don_hang = form_don_hang, form_hoa_don = form_hoa_don, khach_hang = khach_hang, hoa_don = hoa_don, don_hang = don_hang)

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
        tong_tien = item.so_luong * item.gia_ban
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

@app.route("/QL-don-hang/hoan", methods = ['GET','POST'])
def ql_don_hang_hoan():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form = Form_don_hang_hoan()
    hoa_don = None
    chuoi_thong_bao = ''
    if form.validate_on_submit():
        tim_kiem = form.ma_hoa_don.data.strip()
        
        hoa_don = Hoa_don.query.join(Khach_hang).filter(Hoa_don.ma_hoa_don == tim_kiem).first()
        
        if hoa_don != None:
            chuoi_thong_bao = 'Không tìm thấy mã hóa đơn ' + tim_kiem 
    
    return render_template('/Quan_ly/QL_don_hang/QL_don_hang_theo_ma_hd.html',form = form, chuoi_thong_bao = chuoi_thong_bao, hoa_don = hoa_don)


@app.route("/QL-don-hang/theo-ma-hd", methods = ['GET','POST'])
def ql_don_hang_theo_ma():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form = Form_don_hang_hoan()
    hoa_don = None
    chuoi_thong_bao = ''
    if form.validate_on_submit():
        tim_kiem = form.ma_hoa_don.data.strip()
        
        hoa_don = Hoa_don.query.join(Khach_hang).filter(Hoa_don.ma_hoa_don == tim_kiem).first()
        
        if hoa_don != None:
            chuoi_thong_bao = 'Không tìm thấy mã hóa đơn ' + tim_kiem

            
    return render_template('Quan_ly/QL_don_hang/QL_don_hang_theo_ma_hd.html', form = form, hoa_don = hoa_don)

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
            page_filter = San_pham.query.filter(San_pham.ma_san_pham == int(tim_kiem)).paginate(page,5,False)
        else:
            chuoi_truy_van = '%'+tim_kiem.lower()+'%'
            page_filter = San_pham.query.filter(San_pham.ten_san_pham.like(chuoi_truy_van)).paginate(page,5,False)
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
    print(form.errors)
    return render_template('Quan_ly/QL_kho_hang/Chi_tiet_nhap_hang.html', chuoi_thong_bao = chuoi_thong_bao, form = form, san_pham = san_pham)

@app.route('/QL-kho/cap-nhat-sp/sp_<int:ma_sp>', methods = ['GET','POST'])
def ql_cap_nhat_sp(ma_sp):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form = Form_cap_nhat_san_pham()
    san_pham = San_pham.query.filter(San_pham.ma_san_pham == ma_sp).first()
    loai = Loai_san_pham.query.filter(Loai_san_pham.ma_loai == san_pham.ma_loai).first()
    form.gia_nhap.data = san_pham.gia_nhap
    form.thuoc_tinh.data = san_pham.thuoc_tinh
    form.ten_loai.choices = tao_danh_sach_category()
    

    chuoi_thong_bao = ''
    today = datetime.now()
    if form.validate_on_submit():
        gia_ban_moi = form.gia_ban.data
        san_pham.gia_ban = gia_ban_moi
        san_pham.current_edit_price = today.strftime("%d-%m-%Y %H:%M:%S")
        db.session.add(san_pham)
        db.session.commit()
        chuoi_thong_bao = "Cập nhật thành công!"
    print(form.errors)
    
    return render_template('Quan_ly/QL_kho_hang/Cap_nhat_san_pham.html', form = form, san_pham  = san_pham, chuoi_thong_bao = chuoi_thong_bao)

@app.route('/QL-kho/ton-kho/<int:page>', methods = ['GET', 'POST'])
def ql_so_luong_ton(page):
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form = Form_tim_kiem()
    page_filter = San_pham.query.paginate(page,5,False)
    if form.validate_on_submit():
        tim_kiem = form.noi_dung.data
        if tim_kiem.isdigit():
            page_filter = San_pham.query.filter(San_pham.ma_san_pham == int(tim_kiem)).paginate(page,5,False)
        else:
            chuoi_truy_van = '%'+tim_kiem.lower()+'%'
            page_filter = San_pham.query.filter(San_pham.ten_san_pham.like(chuoi_truy_van)).paginate(page,5,False)
        if len(page_filter.items) == 0:
            thong_bao = 'Không tìm thấy sản phẩm!'
    
    return render_template('Quan_ly/QL_kho_hang/Ton_kho.html', form=form, page_filter = page_filter)

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
    tong_loi_nhuan = 0
   
    for hoa_don in ds_hoa_don:
        
        don_hang = Don_hang.query.filter(Don_hang.ma_hoa_don == hoa_don.ma_hoa_don).all()
        for san_pham in don_hang:
            tong_loi_nhuan += san_pham.loi_nhuan
            if san_pham.ma_san_pham not in dict_sp_trong_ngay:
                dict_sp_trong_ngay[san_pham.ma_san_pham] = san_pham.so_luong
            else:
                dict_sp_trong_ngay[san_pham.ma_san_pham] += san_pham.so_luong
    lst_sp_trong_ngay = []
    for item in dict_sp_trong_ngay:
        san_pham = San_pham.query.filter(San_pham.ma_san_pham == item).first()
        dict_temp = {}
        dict_temp['ma_sp'] = item
        dict_temp['ten_sp'] = san_pham.ten_san_pham
        dict_temp['so_luong'] = dict_sp_trong_ngay[item]
        dict_temp['gia_ban'] = san_pham.gia_ban
        lst_sp_trong_ngay.append(dict_temp)
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
    
    tong_loi_nhuan = 0
    danh_sach_hoa_don = []
    for item in hoa_don:
        if item.trang_thai != 13:
            loi_nhuan_1_hoa_don = 0
            dict_temp = {}
            don_hang = Don_hang.query.filter(Don_hang.ma_hoa_don == item.ma_hoa_don).all()
            
            for item_1 in don_hang:
                tong_loi_nhuan += item_1.loi_nhuan
                san_pham = San_pham.query.filter(San_pham.ma_san_pham == item_1.ma_san_pham).first()
                loi_nhuan_1_hoa_don += item_1.loi_nhuan
                
            dict_temp['ngay_tao_hoa_don'] = item.ngay_tao_hoa_don.strftime("%d-%m-%Y")
            dict_temp['loi_nhuan'] = loi_nhuan_1_hoa_don
            danh_sach_hoa_don.append(dict_temp)
    
    for ngay in danh_sach_cac_ngay:
        loi_nhuan_theo_ngay = 0
        for bill in danh_sach_hoa_don:
            if bill['ngay_tao_hoa_don'] == ngay['ngay_tao_hoa_don']:
                loi_nhuan_theo_ngay += bill['loi_nhuan']
        ngay['tong_loi_nhuan'] = loi_nhuan_theo_ngay
    
        
    return render_template('Quan_ly/QL_doanh_thu/Doanh_thu_all.html', form=form, danh_sach_cac_ngay = danh_sach_cac_ngay)

@app.route('/QL-doanh-thu/tong-ket',methods=['GET','POST'])
def ql_doanh_thu_tong_ket():
    if not current_user.is_authenticated or current_user.ma_loai_nguoi_dung != 2:
        return redirect(url_for('log_in', next=request.url))
    form = Form_xem_khoan_chi()
    today = datetime.now()
    ngay_dau_thang = datetime(today.year, today.month, 1)
    str_temp_1 = calendar.monthrange(today.year, today.month)
    ngay_cuoi_thang = datetime(today.year, today.month, str_temp_1[1])
    tieu_de = 'Tính từ ngày ' + ngay_dau_thang.strftime("%d-%m-%Y") + ' đến ngày ' + ngay_cuoi_thang.strftime("%d-%m-%Y")
    ds_chi = Thu_chi.query.filter(Thu_chi.thoi_gian.between(ngay_dau_thang, ngay_cuoi_thang)).all()
    ds_hoa_don = Hoa_don.query.filter(Hoa_don.ngay_tao_hoa_don.between(ngay_dau_thang,ngay_cuoi_thang)).all()
    if form.validate_on_submit():
        ds_chi =Thu_chi.query.filter(Thu_chi.thoi_gian.between(form.tu_ngay.data,form.den_ngay.data)).all()
        hoa_don = Hoa_don.query.filter(Hoa_don.ngay_tao_hoa_don.between(form.tu_ngay.data,form.den_ngay.data)).all()
        tieu_de = 'Tính từ ngày ' + form.tu_ngay.data.strftime("%d-%m-%Y") + ' đến ngày ' + form.den_ngay.data.strftime("%d-%m-%Y")
    tong_chi_phi = 0
    for item in ds_chi:
        tong_chi_phi += item.so_tien
    tong_loi_nhuan = 0
    for hoa_don in ds_hoa_don:
        don_hang = Don_hang.query.filter(Don_hang.ma_hoa_don == hoa_don.ma_hoa_don).all()
        for dh in don_hang:
            tong_loi_nhuan += dh.loi_nhuan 
    return render_template('Quan_ly/QL_doanh_thu/Tong_ket.html', tong_chi_phi = tong_chi_phi, tong_loi_nhuan = tong_loi_nhuan, tieu_de = tieu_de,form = form)    


admin = Admin(app, name = "Admin", index_view=MyAdminIndexView(name="Admin"), template_mode='bootstrap3')
admin.add_view(admin_view(Loai_nguoi_dung, db.session, 'Loại người dùng'))
admin.add_view(admin_view(Nguoi_dung, db.session, 'Người dùng'))
admin.add_view(admin_view(Loai_san_pham, db.session, 'Loại sản phẩm'))
admin.add_view(admin_view(San_pham, db.session, 'Sản phẩm'))
admin.add_view(admin_view(Hoa_don, db.session, 'Hoá đơn'))
admin.add_view(admin_view(Don_hang, db.session, 'Đơn hàng'))
admin.add_view(admin_view(Thu_chi, db.session, 'Thu chi'))