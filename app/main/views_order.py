from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, abort, request, jsonify
from flask import current_app as app
from . import main
from .forms import NameForm, EditProfileForm, EditProfileAdminForm, NewStockForm
from .. import db, mongo
from ..models import User, Role, Permission, Post, Stock, StockItem, SellOrder, OrderItem, Customer,Operation, Shipment, OrderStatus,Payment,PaymentItem
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
from bson import ObjectId
import json




@main.route('/order/sales_orders/',methods=['GET','POST'])
@login_required
def sales_orders():
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


@main.route('/order/sales_items/',methods=['GET','POST'])
@login_required
def sales_items():
    form = CreateForm()

    if current_user.can(Permission.POST_PRODUCT):
        if form.validate_on_submit():

            return redirect(url_for('.new_sell'))
    # if current_user.can(Permission.POST_PRODUCT):
    #     print("user can create")
    # else:
    #     print(current_user.role)
        items=[]
        orders = get_orders()
        for order in orders:
            items.extend(get_items(order))
        sale_details ={}
        products = {}

        for item in items:

            if not item.product_id in products:
                product = mongo.db.products.find_one({'_id': ObjectId(item.product_id)})
                product['_id'] = str(product['_id'])
                products[item.product_id] = product
            stock_item = StockItem.query.filter_by(product_id=item.product_id).first()
            customer = item.sellorder.buyer
            if customer.id in sale_details:
                if stock_item.id in sale_details[customer.id]['sale_items']:
                    update_dict = sale_details[customer.id]['sale_items'][stock_item.id]
                    update_dict['order_count'] += item.count
                    update_dict['paid_count']+=item.paid_count
                    update_dict['checked_count']+=item.checked_count
                    # print(str(item.id)+' '+str(item.paid_count)+ ' '+str(item.checked_count))
                    update_dict['ship_count'] += item.shipped_count
                    update_dict['sales'].append(item)
                    sale_details[customer.id]['sale_items'][stock_item.id] = update_dict
                else:
                    sale_item = {'stock_item': stock_item, 'order_count': item.count, 'ship_count': item.shipped_count,'sales': [item],'paid_count':item.paid_count,'checked_count':item.checked_count}
                    sale_details[customer.id]['sale_items'][stock_item.id] = sale_item

            else:
                sale_item={'stock_item':stock_item,'order_count':item.count,'paid_count':item.paid_count,'checked_count':item.checked_count,'ship_count':item.shipped_count,'sales':[item]}
                sale_details[customer.id] = {'customer':customer,'sale_items':{stock_item.id:sale_item}}
            # pass
        # print(sale_details)
        infos=[]
        for k,v in sorted(sale_details.items()):
            infos.append(v)
        return render_template('salesitems.html',products = products,sale_details=sale_details)
    else:
        return render_template('salesitems.html')


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





@main.route('/_add_order',methods=['GET','POST'])
@login_required
def add_order():
    sale_user = get_parent()
    order_data = request.get_json()
    print(order_data)
    bill = order_data.pop('bill',None)
    # ship = order_data.pop('ship', None)
    # print(bill)
    # print(ship)
    # print(order_data)
    ship=order_data.pop('ship',None)
    filled=order_data.pop('empty',None)
    bill_c = Customer.query.filter(and_(Customer.name == bill['name'], Customer.cellphone == bill['cellphone'])).first()
    if bill_c is None:
        bill_c = create_customer(user=sale_user, name=bill['name'], address=bill['addr'], cellphone=bill['cellphone'])
        db.session.add(bill_c)
        db.session.commit()
    order = create_order(user=sale_user, buyer=bill_c,creator=current_user,order_data=order_data)
    if bill['pay']:
        pay = {}
        for item in order.order_items:
            pay[item.id] = item.count
        payment=create_payment(pay)
        payment.confirmed=True
        db.session.commit()
    if ship['package']:
        shipment={}
        for item in order.order_items:
            shipment[item.id]={"qty":item.count}
        ship['items']=shipment
        create_shipment(ship)

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
    items = OrderItem.query.filter(OrderItem.order_id==order_id,OrderItem.active==True).all()
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

    return redirect(request.referrer)


@main.route('/orderitem/delete/<int:item_id>',methods=['GET','POST'])
@login_required
def item_delete(item_id):
    sale_user = get_parent()
    item = OrderItem.query.get_or_404(item_id)
    if item.sellorder.user.id == sale_user.id:
        delete_orderItem(item)

    return redirect(request.referrer)



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
    products = {}
    for customer in customers:
        # print(customer.name)
        all_orders = SellOrder.query.filter(and_(SellOrder.buyer==customer,SellOrder.active==True)).all()
        orders=[]
        if all_orders:
            for order in all_orders:
                if not order.paid:
                    orders.append(order)
        if orders:

            total_due = 0
            orders_detail =[]
            for order in orders:
                checkout_needed=False

                for item in order.order_items:
                    if item.active and (item.count>(item.paid_count+item.checked_count)):
                        # print(item.product_id)
                        checkout_needed=True
                        if item.product_id not in products:
                            product = mongo.db.products.find_one({'_id': ObjectId(item.product_id)})
                            product['_id'] = item.product_id
                            products[item.product_id] = product
                        total_due += item.sell_price * (item.count - item.paid_count - item.checked_count)
                if checkout_needed:
                    # total_due += order.total_sell
                    orders_detail.append({'order':order})
            payer = {'customer': customer, 'orders_info': orders_detail}
            payer['amount']=total_due
            dues.append(payer)

    # print(dues)
    return render_template("checkout.html",dues=dues,products=products)


@main.route('/order/check/payments',methods=['GET','POST'])
@login_required
def show_payments():
    sales_user = get_parent()
    payments = Payment.query.filter(Payment.user==sales_user).all()
    buyer_pay={}
    for payment in payments:
        if payment.buyer.id not in buyer_pay:
            buyer_pay[payment.buyer.id]={"buyer":payment.buyer,"pay":[payment]}
        else:
            buyer_pay[payment.buyer.id]["pay"].append(payment)

    return render_template("payment.html", buyer_pay=buyer_pay)


@main.route('/order/checkout/payments/delete/<int:payment_id>',methods=['GET','POST'])
@login_required
def payment_delete(payment_id):
    sale_user = get_parent()
    payment = Payment.query.get_or_404(payment_id)
    if sale_user == payment.user:
        db.session.delete(payment)
        db.session.commit()
    return redirect(request.referrer)


@main.route('/order/checkout/payments/confirm/<int:payment_id>',methods=['GET','POST'])
@login_required
def payment_confirm(payment_id):
    sale_user = get_parent()
    payment = Payment.query.get_or_404(payment_id)
    if sale_user == payment.user:
        payment.confirmed = True
        db.session.commit()
    return redirect(request.referrer)


@main.route('/order/checkout/_add_payment',methods=['GET','POST'])
@login_required
def add_payment():

    pay_data = request.get_json()
    # print(pay_data)
    pay={}
    for key,value in pay_data.items():
        pay[key]=value["qty"]
    create_payment(pay)
    return jsonify(request.referrer)


    # for key,value in pay.items():
    #     orderitem=OrderItem.query.get_or_404(key)



@main.route('/order/history',methods=['GET'])
@login_required
def order_history():

    orders = SellOrder.query.filter(SellOrder.user_id==current_user.id).order_by(SellOrder.id.asc()).all()
    products = {}
    for order in orders:


        for item in order.order_items:

            if not item.product_id in products:
                product = mongo.db.products.find_one({'_id': ObjectId(item.product_id)})
                product['_id'] = str(product['_id'])
                products[item.product_id] = product
    print(orders)
    print(products)
    return render_template("order_history.html",orders=orders,products=products)