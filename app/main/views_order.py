from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, abort, request, jsonify
from flask import current_app as app
from . import main
from .forms import NameForm, EditProfileForm, EditProfileAdminForm, NewStockForm
from .. import db, mongo
from ..models import User, Role, Permission, Post, Stock, StockItem, SellOrder, OrderItem, Customer
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
from .util import create_customer,create_stock_item,create_product, create_item
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
    # if request.method=='POST':
    #     customer = Customer.query.filter(and_(Customer.name==request.form['buyername'], Customer.cellphone==request.form['cellphone'])).first()
    #     if customer is None:
    #         customer = create_customer(user=current_user, name=request.form['buyername'],
    #                                address=request.form['address'], cellphone=request.form['cellphone'])
    #         db.session.add(customer)
    #     order = SellOrder(user=current_user, customer=customer)
    #
    #     db.session.add(order)
    #     upcs = request.form.getlist('upc')
    #     brands = request.form.getlist('brand')
    #     names = request.form.getlist('name')
    #     counts = request.form.getlist('qty')
    #     types = request.form.getlist('type')
    #     getprice = request.form.getlist('getprice')
    #     sellprices = request.form.getlist('sellprice')
    #     print(upcs)
    #     print(names)
    #     total_sell = 0.0
    #     total_get = 0.0
    #     for i in range(len(upcs)):
    #         product=""
    #         if upcs[i]:
    #             product = mongo.db.products.find_one({"upc":upcs[i]})
    #         elif brands[i] and names[i]:
    #             product = mongo.db.products.find_one({"$and":[{"brand":brands[i]},{"$or":[{"name":names[i]},{"nick_name":names[i]}]} ]})
    #         if product is not None:
    #             print(product['_id'])
    #             stock_item = StockItem.query.filter(and_(StockItem.product_id==str(product['_id']), StockItem.stock==current_user.stock)).first()
    #             if stock_item:
    #                 print(stock_item.count)
    #                 stock_item.count = stock_item.count - int(counts[i])
    #             else:
    #                 stock_item = create_stock_item(product_id=str(product['_id']),stock=current_user.stock)
    #                 stock_item.count = 0 - int(counts[i])
    #                 db.session.add(stock_item)
    #         else:
    #             product_id =create_product(brand=brands[i],name=names[i],nick_name=names[i],upc=upcs[i])
    #             product = mongo.db.find_one({"_id":product_id})
    #             stock_item = create_stock_item(product_id=str(product['_id']), stock=current_user.stock)
    #             stock_item.count = 0 - int(counts[i])
    #             db.session.add(stock_item)
    #
    #         order_item = OrderItem(get_price=float(getprice[i]),sell_price=float(sellprices[i]), count= int(counts[i]), sellorder=order, product_id=str(product['_id']))
    #         db.session.add(order_item)
    #         db.session.commit()
    #         total_sell += order_item.sell_price*order_item.count
    #         total_get += order_item.get_price*order_item.count
    #     order.total_get = total_get
    #     order.total_sell = total_sell
    #     return redirect(url_for('.sell_orders'))
    #
    # print('render new sell')
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
    # print("add order")
    order_data = request.get_json()
    buyer = order_data.pop('buyer',None)
    # print(order_data)
    # print(type(buyer))
    # print(buyer)
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
        if stock_item:
            if stock_item.count >=int(value['qty']):
                order_item.stock_count=int(value['qty'])
            else:
                order_item.stock_count=max(-int(value['qty']),stock_item.count - int(value['qty']))
            stock_item.count -= int(value['qty'])
        else:
            stock_item = create_stock_item(product_id=str(key), stock=current_user.stock)
            order_item.stock_count = 0 - int(value['qty'])
            stock_item.count = 0 - int(value['qty'])
            db.session.add(stock_item)
            db.session.commit()
        db.session.add(order_item)
        db.session.commit()
        total_sell += order_item.count*order_item.sell_price
    order.total_sell=total_sell

    return jsonify(url_for('.new_sell'))


@main.route('/order/ship',methods=['GET','POST'])
def item_ship():
    pass


@main.route('/order/details/<int:order_id>',methods=['GET','POST'])
def order_details(order_id):
    order = SellOrder.query.get_or_404(order_id)
    items = order.order_items.all()
    # print(items)
    products =[]
    for i in range(len(items)):
        # print(items[i].product_id)
        product = mongo.db.products.find_one({'_id': ObjectId(items[i].product_id)})
        # print(product)
        product['_id'] = str(product['_id'])
        products.append(product)

    return render_template('order_details.html',order=order, items=items, products=products)


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
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for('.sell_orders'))


@main.route('/order/edit/<int:order_id>',methods=['GET','POST'])
def order_edit(order_id):
    return 0