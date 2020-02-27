from Mae import app, db

from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import TextField, SubmitField, IntegerField, StringField, PasswordField, SelectField, DateTimeField
from wtforms import form, fields, validators
from wtforms.widgets.html5 import NumberInput, DateInput


from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import sessionmaker

from flask_ckeditor import CKEditorField

from Mae.xu_ly.xu_ly_model import *
from Mae.xu_ly.xu_ly_form import *


class Form_mua_hang(FlaskForm):
    so_luong = IntegerField('Nhập số lượng', widget=NumberInput())
    submit_1 = SubmitField('Thêm vào giỏ hàng')

class Form_dang_nhap(FlaskForm):
    ten_dang_nhap = fields.StringField('Tên đăng nhập', [validators.required()])
    password = fields.PasswordField('Mật khẩu', [validators.required()])

    def validate_ten_dang_nhap(self, ten_dang_nhap):
        user = self.get_user()
        if user is None:
            raise validators.ValidationError('Tên đăng nhập không tồn tại!')
        if not check_password_hash(user.mat_khau_hash, self.password.data):
            raise validators.ValidationError('Mật khẩu không hợp lệ!')
    
    def get_user(self):
        return Nguoi_dung.query.filter_by(ten_dang_nhap = self.ten_dang_nhap.data).first()

class Form_dang_ky(FlaskForm):
    ho_ten = fields.StringField('Họ tên:', [validators.required()])
    
    ten_dang_nhap = fields.StringField('Tên đăng nhập:', [validators.required()])
    mat_khau = fields.PasswordField('Mật khẩu:',[validators.required()])
    
    
    def validate_ten_dang_nhap(self, ten_dang_nhap):
        if Nguoi_dung.query.filter_by(ten_dang_nhap = self.ten_dang_nhap.data).count() > 0:
            raise validators.ValidationError('Tên đăng nhập đã được sử dụng!')

class Form_hoa_don(FlaskForm):
    ma_don_hang = fields.StringField('Mã đơn hàng:')
    kenh_ban = fields.SelectField(choices=[('Sendo','Sendo'),('Shopee','Shopee'),('Lazada','Lazada'),('Khác','Khác'),('Người quen','Người quen'),('Facebook','Facebook'),('Zalo','Zalo')])
    ho_ten = fields.StringField('Tên khách hàng:')
    ngay_tao = fields.DateField('Ngày:',widget=DateInput())
    dia_chi = fields.StringField('Địa chỉ:')
    so_dien_thoai = fields.StringField('Số điện thoại:')
    giam_gia = fields.FloatField('Giảm giá:')
    nha_van_chuyen = fields.SelectField('Hãng ship:', choices=[
    ('GHN','GHN')
    ,('Viettel','Viettel Post')
    ,('VNC','VNC')
    ,('NJV','Ninja Van')
    ,('LEX','Lazada Express')
    ,('VNPost','VN Post')
    ,('Others','Khác')
    ])
    ma_van_don = fields.StringField('Mã vận đơn:')
    phi_van_chuyen = fields.FloatField('Phí ship:')
    ghi_chu = fields.TextField('Ghi chú:')
    submit = fields.SubmitField('Kế tiếp')

    def tao_khach_hang(self):
        khach_hang = Khach_hang()
        khach_hang.ten_khach_hang = self.ho_ten.data.strip().lower()
        khach_hang.dia_chi = self.dia_chi.data.strip().lower()
        khach_hang.dien_thoai = self.so_dien_thoai.data.strip()
        db.session.add(khach_hang)
        db.session.commit()
        return khach_hang.get_id()

    def tao_hoa_don(self, ngay_tao, ma_kh):
        hoa_don = Hoa_don()
        hoa_don.ma_hoa_don_kenh_ban = self.ma_don_hang.data.strip()
        hoa_don.ngay_tao_hoa_don = ngay_tao
        hoa_don.ma_khach_hang = ma_kh
        hoa_don.tong_tien = 0
        hoa_don.kenh_ban = self.kenh_ban.data
        hoa_don.nha_van_chuyen = self.nha_van_chuyen.data
        hoa_don.ma_van_don = self.ma_van_don.data.strip()
        hoa_don.phi_van_chuyen = self.phi_van_chuyen.data
        hoa_don.ghi_chu = self.ghi_chu.data
        hoa_don.giam_gia = self.giam_gia.data
        db.session.add(hoa_don)
        db.session.commit()
        return hoa_don.get_id()



class Form_tao_san_pham(FlaskForm):
    ten_san_pham = fields.StringField('Tên sản phẩm:', [validators.required('Tên sản phẩm bỏ trống')])
    ten_loai = fields.SelectField('Loại:', [validators.required('Tên sản phẩm bỏ trống')])
    gia_ban = fields.IntegerField('Giá bán:', [validators.required('Giá bán bỏ trống')])
    gia_nhap = fields.IntegerField('Giá nhập:',[validators.required('Giá nhập bỏ trống')])
    thuoc_tinh = fields.TextField('Thuộc tính:')
    so_luong_ton = fields.IntegerField('Số lượng: ')
    submit = fields.SubmitField('Tạo')

    def ghi_vao_db(self):
        san_pham = San_pham()
        ten_sp = self.ten_san_pham.data.strip().lower()
        san_pham.ten_san_pham = ten_sp
        san_pham.ma_loai = int(self.ten_loai.data)
        san_pham.gia_ban = int(self.gia_ban.data)
        san_pham.gia_nhap = int(self.gia_nhap.data)
        san_pham.thuoc_tinh = self.thuoc_tinh.data.strip()
        san_pham.so_luong_ton = int(self.so_luong_ton.data)
        db.session.add(san_pham)
        db.session.commit()
        return san_pham.get_id()
        

class Form_xac_nhan_don_hang(FlaskForm):
    gia_ban = fields.StringField('Giá bán:')
    gia_nhap = fields.StringField('Giá nhập:')
    so_luong = fields.IntegerField('Số lượng', widget=NumberInput())

class Form_don_hang_hoan(FlaskForm):
    ma_hoa_don = fields.StringField('Mã hóa đơn:')



class Form_QL_don_hang(FlaskForm):
    ma_hoa_don_tim_kiem = fields.IntegerField([validators.required()])
    ngay_tim_kiem = fields.DateField(format='%Y-%m-%d')

class Form_tim_kiem(FlaskForm):
    noi_dung = fields.StringField()
    submit = fields.SubmitField('Tìm')

class Form_tim_kiem_nhap_hang(FlaskForm):
    noi_dung = fields.StringField()

class Form_nhap_hang(FlaskForm):
    so_luong_nhap = fields.IntegerField(widget=NumberInput())
    gia_nhap = fields.IntegerField(widget=NumberInput())
    submit = fields.SubmitField('Cập nhật')
    
class Form_cap_nhat_san_pham(FlaskForm):
    ten_loai = fields.SelectField('Loại:')
    gia_ban = fields.IntegerField(widget=NumberInput())
    gia_nhap = fields.IntegerField(widget=NumberInput())
    thuoc_tinh = fields.TextField()
    submit = fields.SubmitField('Cập nhật')

class Form_y_kien(FlaskForm):
    ma_khach_hang = fields.IntegerField('Mã khách hàng')
    tieu_de = fields.StringField('Tiêu đề')
    diem_danh_gia = fields.IntegerField('Điểm đánh giá', widget=NumberInput())
    noi_dung = CKEditorField()
    submit_2 = SubmitField('Gửi ý kiến')

class Form_huy_don_hang(FlaskForm):
    li_do = fields.TextAreaField()
    submit = fields.SubmitField('Đồng ý')

class Form_lua_chon(FlaskForm):
    lua_chon = fields.SelectField('Trạng thái:',choices=[('0','Chưa thanh toán'),('1','Đã thanh toán'),('2','Huỷ')])
    submit = SubmitField('Xem')

class Form_khoan_chi(FlaskForm):
    ten = fields.TextField([validators.required()])
    noi_dung = fields.TextField()
    so_tien = fields.FloatField([validators.required()])
    submit_1 = fields.SubmitField('Hoàn tất')

class Form_xem_khoan_chi(FlaskForm):
    tu_ngay = fields.DateField(widget=DateInput())
    den_ngay = fields.DateField(widget=DateInput())
    submit_2 = fields.SubmitField('Xem')




	




    