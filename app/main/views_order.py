from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, abort, request, jsonify
from flask import current_app as app
from . import main
from .forms import NameForm, EditProfileForm, EditProfileAdminForm, NewStockForm
from .. import db, mongo
from ..models import User, Role, Permission, Post, Stock, StockItem, SellOrder, OrderItem, Customer,Operation, Shipment, OrderStatus
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
from .util import create_customer,create_stock_item,create_product, create_item,update_stock, delete_orderItem, delete_order, get_orders, get_parent
from bson import ObjectId
import json



@main.route('/order/sell_orders/<int:user_id>',methods=['GET','POST'])
@login_required
def sell_orders(user_id):
    form = CreateForm()
    sale_user = get_parent()
    if current_user.can(Permission.POST_PRODUCT):
        if form.validate_on_submit():

            return redirect(url_for('.new_sell'))
    # if current_user.can(Permission.POST_PRODUCT):
    #     print("user can create")
    # else:
    #     print(current_user.role)
        orders = get_orders()
        return render_template('sellorders.html', form=form,orders=orders,status=OrderStatus.status)
    else:
        return render_template('sellorders.html')


@main.route('/order/new_sell',methods=['GET','POST'])
@login_required
def new_sell():
    sources = []
    sale_user = get_parent()
    if current_user.is_administrator:
        cursor = mongo.db.sources.find()
    else:
        cursor = mongo.db.sources.find({"user":sale_user.id})
    for doc in cursor:
        sources.append(doc["source"])

    return render_template('new_sell.html',sources=sources)


@main.route('/_search_source')
@login_required
def search_source():
    source=request.args.get('source','',type=str)
    sale_user = get_parent()
    # upc_data = upc.split(',')
    products=[]
    if current_user.is_administrator:
        cursor = mongo.db.products.find({"source":source.upper()})
    else:
        cursor = mongo.db.products.find({"$and": [{"source": source.upper()}, {"user": sale_user.id}]})
    if cursor:
        for product in cursor:
            product["_id"]=str(product["_id"])
            stock_item=StockItem.query.filter(StockItem.product_id==product["_id"]).first()
            if stock_item:
                product["count"]=stock_item.count
            else:
                product["count"]=0
            products.append(product)

    return jsonify(products)


@main.route('/_add_order',methods=['GET','POST'])
@login_required
def create_order():
    sale_user = get_parent()
    order_data = request.get_json()
    print(order_data)
    bill = order_data.pop('bill',None)
    # ship = order_data.pop('ship', None)
    print(bill)
    # print(ship)
    # print(order_data)
    bill_c = Customer.query.filter(and_(Customer.name == bill['name'], Customer.cellphone == bill['cellphone'])).first()
    if bill_c is None:
        bill_c = create_customer(user=sale_user, name=bill['name'], address=bill['addr'], cellphone=bill['cellphone'])
        db.session.add(bill_c)
        db.session.commit()
    # ship_addr = ship['name']+','+ship['addr']+','+ship['addr']
    # ship_c = Customer.query.filter(and_(Customer.name == ship['name'], Customer.cellphone == ship['cellphone'])).first()
    # if ship_c is None:
    #     ship_c = create_customer(user=current_user, name=ship['name'], address=ship['addr'],
    #                              cellphone=ship['cellphone'])
    #     db.session.add(ship_c)
    #     db.session.commit()
    order = SellOrder(user=sale_user, bill=bill_c,creator=current_user)

    db.session.add(order)
    db.session.commit()
    total_sell = 0
    for key, value in order_data.items():
        # print(value)
        order_item = OrderItem(sell_price=float(value['price']), count=int(value['qty']), sellorder=order,product_id=str(key))

        stock_item = StockItem.query.filter(and_(StockItem.product_id==str(key), StockItem.stock==sale_user.stock)).first()
        order_item.note=str(value['note'])
        db.session.add(order_item)
        db.session.commit()
        if not stock_item:
            stock_item = create_stock_item(product_id=str(key), stock=sale_user.stock)
            db.session.add(stock_item)
            db.session.commit()

        update_stock(order_item=order_item,stock_item=stock_item,action=Operation.CREATE)
        # if stock_item:
        #     if stock_item.count >=int(value['qty']):
        #         order_item.stock_count=int(value['qty'])
        #     else:
        #         order_item.stock_count=max(-int(value['qty']),stock_item.count - int(value['qty']))
        #     stock_item.count -= int(value['qty'])
        # else:
        #     stock_item = create_stock_item(product_id=str(key), stock=current_user.stock)
        #     order_item.stock_count = 0 - int(value['qty'])
        #     stock_item.count = 0 - int(value['qty'])
        #     db.session.add(stock_item)
        #     db.session.commit()

        total_sell += order_item.count*order_item.sell_price
    order.total_sell=total_sell

    return jsonify(url_for('.new_sell'))


def ship_order_item(order_item,info):
    sale_user = get_parent()
    stock_item = StockItem.query.filter(StockItem.product_id == order_item.product_id,
                                        StockItem.stock == sale_user.stock).first()
    update_stock(order_item=order_item, stock_item=stock_item, action=Operation.SHIP, ship_info=info)


def ship_cancel(shipment):
    sale_user = get_parent()
    stock_item = StockItem.query.filter(StockItem.product_id == shipment.orderitem.product_id,
                                        StockItem.stock == sale_user.stock).first()
    update_stock(shipment=shipment, stock_item = stock_item,action=Operation.SHIP_CANCEL)



@main.route('/order/_item_ship_update',methods=['GET','POST'])
@login_required
def item_ship_update():
    data = request.get_json()
    print(data)
    if data["action"] == "cancel":
        item = data["items"]
        shipment_id = int(str(item['id']).split('_')[-1])
        shipment = Shipment.query.get_or_404(shipment_id)
        ship_cancel(shipment)
    elif data["action"] == "release":
        item = data["items"]
        shipment_id = int(str(item['id']).split('_')[-1])
        shipment = Shipment.query.get_or_404(shipment_id)
        shipment.status = "Shipping"
        db.session.commit()
    return jsonify(request.referrer)


@main.route('/order/_item_ship',methods=['GET','POST'])
@login_required
def item_ship():
    sale_user = get_parent()
    ship_data = request.get_json()
    # print(ship_data)
    # item = OrderItem.query.get_or_404(str(list(ship_data.keys())[0]))
    # order = SellOrder.query.get_or_404(item.sellorder.id)
    for key, value in ship_data.items():
        item_key = str(key).split('_')[-1]
        order_item = OrderItem.query.get_or_404(int(item_key))
        ship_order_item(order_item,value)
        # stock_item = StockItem.query.filter(StockItem.product_id==order_item.product_id, StockItem.stock==sale_user.stock).first()
        # update_stock(order_item=order_item,stock_item=stock_item,action=Operation.SHIP,ship_info=value)

    return jsonify(request.referrer)


@main.route('/order/ship/<int:order_id>',methods=['GET','POST'])
@login_required
def order_ship(order_id):
    sale_user = get_parent()
    order = SellOrder.query.get_or_404(order_id)
    items = order.order_items.all()
    for order_item in items:
        if order_item.status == OrderStatus.CREATED:
            stock_item = StockItem.query.filter(StockItem.product_id == order_item.product_id,StockItem.stock==sale_user.stock).first()
            update_stock(order_item=order_item, stock_item=stock_item, action=Operation.SHIP,ship_qty=order_item.count)

    return redirect(request.referrer)


@main.route('/order/details/<int:order_id>',methods=['GET','POST'])
@login_required
def order_details(order_id):
    sale_user = get_parent()
    order = SellOrder.query.get_or_404(order_id)
    items = order.order_items.all()
    # print(items)
    products =[]
    stock_items=[]
    if order.status == OrderStatus.CREATED:
        order.status=OrderStatus.SHIPPED
    for i in range(len(items)):
        # print(items[i].product_id)
        product = mongo.db.products.find_one({'_id': ObjectId(items[i].product_id)})
        # print(product)
        product['_id'] = str(product['_id'])
        products.append(product)
        stock_item=StockItem.query.filter(and_(StockItem.product_id==items[i].product_id, StockItem.stock==sale_user.stock)).first()

        stock_items.append(stock_item)
        if items[i].status == OrderStatus.CREATED:
            order.status = OrderStatus.CREATED

    db.session.commit()

    return render_template('order_details.html',order=order, items=items, products=products,stock_items=stock_items,status=OrderStatus.status[order.status])


@main.route('/order/delete/<int:order_id>',methods=['GET','POST'])
@login_required
def order_delete(order_id):
    sale_user = get_parent()
    order = SellOrder.query.get_or_404(order_id)
    if order.user.id == sale_user.id:
        delete_order(order)
    # print(order)
    # items = order.order_items.all()
    # print(items)
    # products = []
    # for i in range(len(items)):
    #     # print(items[i].product_id)
    #     stock_item = StockItem.query.filter(and_(StockItem.product_id==items[i].product_id, StockItem.stock==current_user.stock)).first()
    #     # print(product)
    #     # product['_id'] = str(product['_id'])
    #     stock_item.count += items[i].count
    #     stock_item.order_count -= items[i].count
    #     db.session.delete(items[i])
    # db.session.delete(order)
    # db.session.commit()
    return redirect(url_for('.sell_orders'))


@main.route('/order/edit/<int:order_id>',methods=['GET','POST'])
@login_required
def order_edit(order_id):
    return 0


@main.route('/order/check',methods=['GET','POST'])
@login_required
def checkout():
    sale_user = get_parent()
    dues = []
    customers = Customer.query.filter(Customer.user_id==sale_user.id).all()
    for customer in customers:

        orders = SellOrder.query.filter(and_(SellOrder.bill==customer, SellOrder.paid==False)).all()
        if orders:

            total_due = 0
            orders_detail =[]
            for order in orders:
                total_due += order.total_sell
                products={}
                for item in order.order_items:
                    product = mongo.db.products.find_one({'_id': ObjectId(item.product_id)})
                    product['_id'] = item.product_id
                    products[item.product_id] = product
                orders_detail.append({'order':order,'products': products})
            payer = {'customer': customer, 'orders_info': orders_detail}
            payer['amount']=total_due
            dues.append(payer)
    print(dues)
    return render_template("checkout.html",dues=dues)