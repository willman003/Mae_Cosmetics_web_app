import requests
import json
from datetime import datetime, timedelta

from sqlalchemy.orm import sessionmaker, configure_mappers
from sqlalchemy import exc,asc,desc
from flask_sqlalchemy import Pagination

from flask_sqlalchemy import BaseQuery

from Mae.xu_ly.xu_ly_model import *
from Mae import db
# from xu_ly_model import *


# dbSession.rollback()

client_key = '62bee939365a425b93c13bca9882041c'

def Lay_token_xac_thuc(client_key=client_key):
    url = "https://sapi.sendo.vn/shop/authentication"

    payload = 'Content-Type=application/x-www-form-urlencoded&Cache-Control=no-cache&grant_type=password&username=' + client_key + '&password=9397f820941f37f2d28383cc419ea34632022b54'
    headers = {
    'Authorization': 'Bearer PuAM0B2qJ_JCoaW5zpQlxuksc0PINGBFvEaRl5d3a1LWBGJ8ZJ8FX6RmDol2KsP6bo9kMKcQW-1bVXJN00SK9baDHR7lO8p3wGocK_QbSXkfm0_R3FQZUSlvfSV7VxSkMUGEcFfL4luB1MGynz1bnA0xrSan4gjYXZw1KcEIN9WGPV61CYA7xF619YfMotauQzc49T6rCfRPg-hrkRi9bvD_Wgd9XUF2r2n6yU8Au5GFbI8A4P26chvWVdEwMwvpaH4KxxHl7Y8VVaR5WeJynirsMP_xPeWbN2EYenFGK-y9GC-2XbiMpqJnBynLT0a0-im6GE1TH2rRM9_d0Uvl_Mzc8Nr_Sc4gT-9N_qvX2s4FCD2s2WALQUXV1YdA-57YS6YIRUyW6C3gdE6JZG2B06mR1zZ26IlZqn8hLfbCyHYQ6zuAnDRpP3QRLHQXf8AfkczracLm07fA6uQi9tsoDIDW2vH3PmH4xOwtS7KR1Y4kIum5UX1JmvZ7EwVns183Xy8frfXwjeAwXG2skIU4F9ZsJEZ65iuBC7fgiHcaPt57_ai5_wIugY886IQd70u0RCS-EQ',
    'Cache-Control': 'no-cache',
    'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.request("POST", url, headers=headers, data = payload)
    result = json.loads(response.text)
    return result['access_token']

def Lay_danh_sach_order():
    ngay=datetime.now().date()

    today = str(ngay.year) + "/" + str(ngay.month) + "/" + str(ngay.day)
    ten_days_ago = ngay - timedelta(days=10)
    from_date = str(ten_days_ago.year) + "/" + str(ten_days_ago.month) + "/" + str(ten_days_ago.day)
    url = "http://sapi.sendo.vn/shop/salesOrder/Merchant?frDate="+from_date+"&ttDate="+today+"&offset=0&limit=50"
    
    payload = {}
    headers = {
    'Authorization': 'Bearer ' + Lay_token_xac_thuc(),
    'Cache-Control': 'no-cache',
    'Postman-token': '9c32433d-dcb0-f837-a0f2-69ba8257d27b'
    }

    response = requests.request("GET", url, headers=headers, data = payload)
    result = json.loads(response.text)
    list_order = result['result']['data']
   
    return list_order

def Lay_thong_tin_chi_tiet_order(order_number):
    url = "http://sapi.sendo.vn/shop/salesorder?orderNumber=" + order_number

    payload = {}
    headers = {
    'Authorization': 'Bearer ' + Lay_token_xac_thuc(),
    }

    response = requests.request("GET", url, headers=headers, data = payload)
    result = json.loads(response.text)
    return result['result']

def Lay_danh_sach_san_pham():
    to_date = datetime.now().strftime("%Y-%m-%d")

    payload = {}
    
    headers = {
    'Authorization': 'Bearer ' + Lay_token_xac_thuc(),
    'Cache-Control': 'no-cache',
    'Postman-token': '9c32433d-dcb0-f837-a0f2-69ba8257d27b'

    }
    tra_loi = []
    for i in range(150):
        url = "https://sapi.sendo.vn/shop/v2/product/search?limit=10&pageIndex="+str(i)+"&amp;dateForm=2016-01-01&amp;dateTo="+to_date+"&amp;productName={productname || sku}"
        response = requests.request("GET", url, headers=headers, data = payload)
        result = json.loads(response.text)
        data = result['result']['data']
        if data != None:
            tra_loi += data
    return tra_loi

def Lay_thong_tin_chi_tiet_san_pham(id_san_pham):
    url = "http://sapi.sendo.vn/shop/v2/product/"+str(id_san_pham)

    payload = {}
    headers = {
    'Authorization': 'Bearer ' + Lay_token_xac_thuc(),
    'cache-control': 'no-cache'
    }

    response = requests.request("GET", url, headers=headers, data = payload)
    result = json.loads(response.text)
    ket_qua = result['result']
    return ket_qua

def tao_san_pham_moi(name, gia_ban, gia_nhap, id_sendo):
    sp = San_pham()
    sp.ten_san_pham = name
    sp.gia_ban = gia_ban
    sp.gia_nhap = gia_nhap
    sp.id_sendo = id_sendo
    db.session.add(sp)
    db.session.commit()
    return sp.get_id()

def tao_khach_hang_moi(order):
    khach_hang = Khach_hang()
    khach_hang.ten_khach_hang = order['salesOrder']['receiverName'].lower()
    khach_hang.email = order['salesOrder']['receiverEmail']
    khach_hang.dia_chi = order['salesOrder']['regionName']
    khach_hang.dien_thoai = order['salesOrder']['buyerPhone']
    db.session.add(khach_hang)
    db.session.commit()
    return khach_hang.get_id()

def tao_don_hang_moi(ma_hd, item):
    sp = dbSession.query(San_pham).filter(San_pham.id_sendo == item['productVariantId']).first()
    if sp == None:
        ma_sp_moi = tao_san_pham_moi(item['productName'],item['price'],0,item['productVariantId'])
        sp = dbSession.query(San_pham).filter(San_pham.ma_san_pham == ma_sp_moi).first()
    don_hang = Don_hang()
    don_hang.ma_hoa_don = ma_hd
    don_hang.ma_san_pham = sp.ma_san_pham
    don_hang.ten_san_pham = sp.ten_san_pham
    don_hang.so_luong = item['quantity']
    don_hang.don_gia = sp.gia_ban
    don_hang.loi_nhuan = (sp.gia_ban - sp.gia_nhap)*item['quantity']
    don_hang.ghi_chu = item['description']
    dbSession.add(don_hang)
    dbSession.commit()
    return

def tao_hoa_don_moi(order_number):
    order = Lay_thong_tin_chi_tiet_order(order_number)
    hoa_don = Hoa_don()
    hoa_don.ngay_tao_hoa_don = datetime.strptime(order['salesOrder']['orderDate'],"%Y-%m-%d %H:%M:%S")
    #Create new customer
    khach_hang_cu = dbSession.query(Khach_hang).filter(Khach_hang.ten_khach_hang == order['salesOrder']['receiverName'].lower()).first()
    if khach_hang_cu == None:
        hoa_don.ma_khach_hang = tao_khach_hang_moi(order)
    else:
        hoa_don.ma_khach_hang = khach_hang_cu.ma_khach_hang
    hoa_don.tong_tien = order['salesOrder']['totalAmount']
    hoa_don.ma_hoa_don_sendo = order['salesOrder']['orderNumber']
    hoa_don.ma_van_don = order['salesOrder']['trackingNumber']
    hoa_don.trang_thai = order['salesOrder']['orderStatus']
    hoa_don.nha_van_chuyen = order['salesOrder']['carrierName']
    hoa_don.ghi_chu = order['salesOrder']['note']
    hoa_don.da_in_hd = 0
    hoa_don.da_cap_nhat_kho = 0
    dbSession.add(hoa_don)
    dbSession.commit()
    #Create order_detail
    for item in order['salesOrderDetails']:
        tao_don_hang_moi(hoa_don.get_id(),item)
    return 
   

def cap_nhat_hoa_don_database(chi_tiet_order):
    
    order = chi_tiet_order['salesOrder']
    hoa_don = dbSession.query(Hoa_don).filter(Hoa_don.ma_hoa_don_sendo == order['orderNumber']).first()
    if hoa_don == None:
        tao_hoa_don_moi(order['orderNumber'])
    else:
        hoa_don.trang_thai = order['orderStatus']
        hoa_don.nha_van_chuyen = order['carrierName']
        hoa_don.ma_van_don = order['trackingNumber']
        if order['orderStatus'] == 13:
            hoa_don.ghi_chu = '[HUỶ] ' + order['reasonCancel']
        dbSession.add(hoa_don)
        dbSession.commit()
    return  

def cap_nhat_san_pham(item):
    
    product = Lay_thong_tin_chi_tiet_san_pham(item.id_sendo)
    
    if product['promotionPrice'] != None:
        sp = dbSession.query(San_pham).filter(San_pham.id_sendo==product['id']).first()
        sp.gia_ban = product['promotionPrice']
        dbSession.add(sp)
        dbSession.commit()
     
    return

def tao_danh_sach_category():
    ds_category = Loai_san_pham.query.all()
    lst_ket_qua =[]
    for item in ds_category:
        tup_temp = (str(item.ma_loai),item.ten_loai)
        lst_ket_qua.append(tup_temp)
    return lst_ket_qua