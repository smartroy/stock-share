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
from .util import create_customer,create_stock_item,create_product, create_item,update_stock
from bson import ObjectId
import json



@main.route('/order/sell_orders',methods=['GET','POST'])
def sell_orders():
    form = CreateForm()
    if current_user.can(Permission.WRITE_ARTICLES):
        if form.validate_on_submit():

            return redirect(url_for('.new_sell'))
    # if current_user.can(Permission.WRITE_ARTICLES):
    #     print("user can create")
    # else:
    #     print(current_user.role)
        orders = SellOrder.query.filter_by(user_id=current_user.id).all()
        return render_template('sellorders.html', form=form,orders=orders)
    else:
        return render_template('sellorders.html')


@main.route('/order/new_sell',methods=['GET','POST'])
def new_sell():
    sources = []
    cursor = mongo.db.sources.find({})
    for doc in cursor:
        sources.append(doc["source"])

    return render_template('new_sell.html',sources=sources)


@main.route('/_search_source')
def search_source():
    source=request.args.get('source','',type=str)
    # upc_data = upc.split(',')
    products=[]
    cursor=mongo.db.products.find({"source":source.upper()})
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
def create_order():

    order_data = request.get_json()
    buyer = order_data.pop('buyer',None)

    customer = Customer.query.filter(and_(Customer.name == buyer['name'], Customer.cellphone == buyer['cellphone'])).first()
    if customer is None:
        customer = create_customer(user=current_user, name=buyer['name'],address=buyer['addr'], cellphone=buyer['cellphone'])
        db.session.add(customer)
        db.session.commit()
    order = SellOrder(user=current_user, customer=customer)
    db.session.add(order)
    db.session.commit()
    total_sell = 0
    for key, value in order_data.items():
        # print(value)
        order_item = OrderItem(sell_price=float(value['price']), count=int(value['qty']), sellorder=order,
                               product_id=str(key))

        stock_item = StockItem.query.filter(and_(StockItem.product_id==str(key), StockItem.stock==current_user.stock)).first()
        order_item.note=str(value['note'])
        db.session.add(order_item)
        db.session.commit()
        if not stock_item:
            stock_item = create_stock_item(product_id=str(key), stock=current_user.stock)
            db.session.add(stock_item)
            db.session.commit()

        update_stock(order_item,stock_item,Operation.CREATE)
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


@main.route('/order/ship/item/<int:item_id>',methods=['GET','POST'])
def item_ship(item_id):
    order_item = OrderItem.query.get_or_404(item_id)
    stock_item = StockItem.query.filter(StockItem.product_id==order_item.product_id).first()
    update_stock(order_item,stock_item,Operation.SHIP)

    return redirect(url_for('.order_details', order_id = order_item.sellorder.id))


@main.route('/order/ship/<int:order_id>',methods=['GET','POST'])
def order_ship(order_id):
    order = SellOrder.query.get_or_404(order_id)
    items = order.order_items.all()
    for order_item in items:
        if order_item.status == OrderStatus.CREATED:
            stock_item = StockItem.query.filter(StockItem.product_id == order_item.product_id).first()
            update_stock(order_item, stock_item, Operation.SHIP)

    return redirect(url_for('.order_details', order_id = order_item.sellorder.id))


@main.route('/order/details/<int:order_id>',methods=['GET','POST'])
def order_details(order_id):
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
        stock_item=StockItem.query.filter(StockItem.product_id==items[i].product_id).first()
        stock_items.append(stock_item)
        if items[i].status == OrderStatus.CREATED:
            order.status = OrderStatus.CREATED

    db.session.commit()

    return render_template('order_details.html',order=order, items=items, products=products,stock_items=stock_items,status=OrderStatus.status[order.status])


@main.route('/order/delete/<int:order_id>',methods=['GET','POST'])
def order_delete(order_id):
    order = SellOrder.query.get_or_404(order_id)
    # print(order)
    items = order.order_items.all()
    # print(items)
    # products = []
    for i in range(len(items)):
        # print(items[i].product_id)
        stock_item = StockItem.query.filter(and_(StockItem.product_id==items[i].product_id, StockItem.stock==current_user.stock)).first()
        # print(product)
        # product['_id'] = str(product['_id'])
        stock_item.count += items[i].count
        db.session.delete(items[i])
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('.sell_orders'))


@main.route('/order/edit/<int:order_id>',methods=['GET','POST'])
def order_edit(order_id):
    return 0