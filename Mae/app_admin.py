from Mae import app, login_manager, db

from flask import render_template, redirect, url_for, session, request

from datetime import datetime

from flask_login import current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash

from flask_admin import helpers, expose
import flask_login as login

from Mae.xu_ly.xu_ly_form import *
from Mae.xu_ly.xu_ly_model import *




# Create user loader function
@login_manager.user_loader
def load_user(user_id):
    return Nguoi_dung.query.get(user_id)


@app.route('/dang-nhap', methods = ['GET', 'POST'])
def log_in():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form_dang_nhap = Form_dang_nhap()
    if form_dang_nhap.validate_on_submit():
        form_dang_nhap.validate_ten_dang_nhap(form_dang_nhap.ten_dang_nhap.data)
        user = form_dang_nhap.get_user()
        login_user(user)
        if 'next' in request.args:
            return redirect(request.args.get('next'))
        else:
            return redirect(url_for('index'))
        
    return render_template('Quan_ly/MH_Dang_nhap.html', form_dang_nhap = form_dang_nhap)

@app.route('/dang-xuat',methods = ['GET','POST'])
def log_out():
    session.clear()
    login.logout_user()
    return redirect(url_for('index'))

@app.route('/dang-ky', methods = ['GET', 'POST'])
def user_register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = Form_dang_ky()
    thong_bao = ''
    if form.validate_on_submit():
        form.validate_ten_dang_nhap(form.ten_dang_nhap.data)
        loai_nguoi_dung = Loai_nguoi_dung.query.all()
        if len(loai_nguoi_dung) == 0:
            loai = Loai_nguoi_dung()
            loai.ma_loai_nguoi_dung = 2
            loai.ten_loai_nguoi_dung =  'admin'
            db.session.add(loai)
            db.session.commit()

        user = Nguoi_dung()
        form.populate_obj(user)
        user.ten_dang_nhap = form.ten_dang_nhap.data
        user.mat_khau_hash = generate_password_hash(form.mat_khau.data)
        user.ma_loai_nguoi_dung = 1
        db.session.add(user)
        db.session.commit()
        
        login.login_user(user)
        thong_bao = 'Đăng ký thành công! Liên hệ admin để được cấp quyền truy cập.'
    
    return render_template('Quan_ly/MH_Dang_ky.html',form = form, thong_bao = thong_bao)

