#created by Shikang Xu
from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, abort, request, jsonify
from flask import current_app as app
from . import main
from .forms import NameForm, EditProfileForm, EditProfileAdminForm, NewStockForm
from .. import db, mongo
from ..models import *
from .. import auth
from werkzeug.utils import secure_filename
from config import basedir
import os
from flask_login import login_required, current_user
from ..decoraters import admin_required
from sqlalchemy import and_, or_
from hashlib import sha1
import hmac
from uuid import uuid4
from json import dumps
from base64 import b64encode
from datetime import datetime, timedelta
from .forms import CreateForm, SellForm, SellItemForm
from .util import *
import json

@main.route('/shipping/',methods=['GET','POST'])
@login_required
def shipping_all():
    sale_user=get_parent()
    shipments = Shipment.query.filter(Shipment.user_id==sale_user.id, Shipment.active==True).order_by(Shipment.date.desc()).all()

    stocks={}
    for shipment in shipments:
        for item in shipment.shipmentitems:
            product_id=item.orderitem.product_id
            if product_id not in stocks:
                stocks[product_id]=StockItem.query.filter(StockItem.stock_id==sale_user.stock.id,StockItem.product_id==product_id).all()[0]


    return render_template('shipping.html',shipments=shipments,stocks=stocks)


@main.route('/shipping/new',methods=['GET','POST'])
@login_required
def new_shipping():
    sale_user = get_parent()
    dues = {}
    customers = Customer.query.filter(Customer.user_id == sale_user.id).all()

    for customer in customers:
        # print(customer.name)
        all_orders = SellOrder.query.filter(and_(SellOrder.buyer == customer, SellOrder.active == True)).all()
        orders = []
        if all_orders:
            for order in all_orders:
                if not order.shipped:
                    orders.append(order)
        if orders:

            # total_due = 0
            orders_detail = []
            for order in orders:
                ship_needed = False
                # print(order.id)
                for item in order.order_items:
                    # print(str(item.count)+' '+str(item.shipped_count + item.packaged_count))
                    if item.active and (item.count > (item.shipped_count + item.packaged_count)):
                        # print(item.product_id)
                        ship_needed = True

                            # products[item.product_id] = product
                        # total_due += (item.count - item.paid_count - item.checked_count)
                if ship_needed:
                    # total_due += order.total_sell
                    orders_detail.append({'order': order})
            payer = {'customer': customer, 'order_infos': orders_detail}
            # payer['amount'] = total_due
            dues[payer['customer'].id]=payer

    # print(dues)
    # print(products)
    return render_template("new_shipping.html", dues=dues)


@main.route('/order/shipping/_add_shipment',methods=['GET','POST'])
@login_required
def add_shipment():

    ship_data = request.get_json()
    # print(pay_data)

    # ship = {}
    # for key, value in ship_data.items():
    #     ship[key] = value["qty"]
    # print(ship_data)
    create_shipment(ship_data)
    return jsonify(request.referrer)

@main.route('/order/shipping/delete/<int:shipment_id>',methods=['GET','POST'])
@login_required
def delete_shipment(shipment_id):
    shipment=Shipment.query.get_or_404(shipment_id)
    cancel_shipment(shipment)
    return redirect(request.referrer)

@main.route('/order/shipping/delete_item/<int:shipmentitem_id>',methods=['GET','POST'])
@login_required
def delete_shipmentitem(shipmentitem_id):
    shipment_item=ShipmentItem.query.get_or_404(shipmentitem_id)
    cancel_shipment_item(shipment_item)
    return redirect(request.referrer)


@main.route('/order/shipping/release/<int:shipment_id>',methods=['GET','POST'])
@login_required
def release_shipment(shipment_id):
    shipment=Shipment.query.get_or_404(shipment_id)
    shipment_release(shipment)
    return redirect(request.referrer)


@main.route('/order/shipping/details/<int:shipment_id>',methods=['GET','POST'])
@login_required
def shipment_details(shipment_id):
    shipment=Shipment.query.get_or_404(shipment_id)
    return render_template('shipment_details.html',shipment=shipment)