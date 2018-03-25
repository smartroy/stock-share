from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, abort, request, jsonify
from flask import current_app as app
from . import main
from .forms import NameForm, EditProfileForm, EditProfileAdminForm, NewStockForm
from .. import db, mongo
from ..models import User, Role, Permission, Post, Stock, StockItem, SellOrder, OrderItem, Customer, Operation
from ..models import PurchaseItem
from .. import auth
from werkzeug.utils import secure_filename
from config import basedir
import os
from flask_login import login_required, current_user
from ..decoraters import admin_required
from sqlalchemy import and_, or_,asc
from hashlib import sha1
import hmac
from uuid import uuid4
from json import dumps
from base64 import b64encode
from datetime import datetime, timedelta
from .forms import CreateForm, SellForm, SellItemForm
from .util import create_customer,create_stock_item,create_product, create_item, create_post,update_stock,get_parent
from bson import ObjectId


@main.route('/stock/new',methods=['GET','POST'])
@login_required
def new_stock():
    sale_user = get_parent()
    sources = []
    cursor = mongo.db.sources.find({})
    for doc in cursor:
        sources.append(doc["source"])
    form = NewStockForm()
    product = None
    if form.validate_on_submit():
        if form.upc.data is not None:
            product = mongo.db.products.find_one({"upc":form.upd.data})
        if product is not None:
            stock_item = StockItem.query.filter_by(product_id=str(product["_id"]),stock_id=sale_user.stock.id).first()
            if stock_item is not None:
                stock_item.count+=1
                db.session.commit()
            else:
                stock_item = create_stock_item(product_id=str(product["_id"]),stock=sale_user.stock, price=form.price.data)
                db.session.add(stock_item)
                db.session.commit()

        else:
            product_id = create_product(name=form.name.data, upc=form.upc.data, sku=form.sku.data,brand=form.brand.data)
            stock_item = create_stock_item(product_id=product_id, stock=sale_user.stock, price=form.price.data)
            db.session.add(stock_item)
            db.session.commit()

        return redirect(url_for('.index'))
    return render_template('new_stock.html',sources=sources)


@main.route('/stock/shopping',methods=['GET','POST'])
@login_required
def shopping_list():
    sale_user = get_parent()
    # if request.method == 'POST':
    #     shop_data = request.get_json()
    #     for key, value in shop_data.items():
    #         stock_item = StockItem.query.filter(
    #             and_(StockItem.product_id == str(key), StockItem.stock == current_user.stock)).first()
    #         stock_item

    stocks_all=StockItem.query.filter(StockItem.stock == sale_user.stock).order_by(StockItem.id.desc()).all()
    stocks=[]
    for stock in stocks_all:
        if stock.need_count >0:
            stocks.append(stock)
    products = []
    for i in range(len(stocks)):
        product = mongo.db.products.find_one({'_id': ObjectId(stocks[i].product_id)})
        product['_id'] = str(product['_id'])
        products.append(product)


    return render_template('shopping_list.html',stocks=stocks,products=products)



@main.route('/stock/item_post/<int:item_id>')
@login_required
def stock_item_post(item_id):
    sale_user = get_parent()
    item = StockItem.query.filter(StockItem.id==item_id).first()

    post = Post.query.filter(Post.stockitem_id==item.id, Post.user_id==sale_user.id).all()
    print(post)
    if not post:
        print('create new post')
        post = create_post(user=sale_user, stockitem=item, product_id=item.product_id, description=None)
        db.session.add(post)
        db.session.commit()
    return redirect(url_for('.post_all'))


@main.route('/post/all')
@login_required
def post_all():
    sale_user = get_parent()
    form = CreateForm()
    if sale_user.can(Permission.POST_PRODUCT):
        if form.validate_on_submit():
            return redirect(url_for('.new_stock'))
            # if sale_user.can(Permission.POST_PRODUCT):
            #     print("user can create")
            # else:
            #     print(sale_user.role)
        posts = Post.query.all()
        products = []
        for i in range(len(posts)):
            product = mongo.db.products.find_one({'_id': ObjectId(posts[i].product_id)})
            product['_id'] = str(product['_id'])
            products.append(product)
        print(posts)
        return render_template('post.html', form=form, posts=posts, products=products)
    else:
        return render_template('post.html')
    # post=Post.query.filter_by(user_id=sale_user.id).all()



@main.route('/stock/item_edit/<int:item_id>',methods=['GET','POST'])
@login_required
def stock_item_edit(item_id):
    sale_user = get_parent()
    stock_item = StockItem.query.get_or_404(item_id)
    product = mongo.db.products.find_one({'_id':ObjectId(stock_item.product_id)})
    if request.method == 'POST':
        stock_item.count = int(request.form.get("current"))
        stock_item.order_count = int(request.form.get("order_total"))
        stock_item.shipped_count = int(request.form.get("shipped_total"))
        # stock_item.pending_count = int(request.form.get("pending"))
        db.session.commit()
    return render_template('edit_stock.html', stock_item=stock_item, product=product)





@main.route('/stock/item_delete/<int:item_id>')
@login_required
def stock_item_delete(item_id):
    stock_item = StockItem.query.get_or_404(item_id)
    db.session.delete(stock_item)
    db.session.commit()
    return redirect(url_for('.index'))





@main.route('/_add_stock',methods=['GET','POST'])
@login_required
def add_stock():
    sale_user = get_parent()
    stock_data = request.get_json()
    for key, value in stock_data.items():
        stock_item = StockItem.query.filter(and_(StockItem.product_id == str(key), StockItem.stock == sale_user.stock)).first()
        if not stock_item:
            stock_item = create_stock_item(product_id=str(key), stock=sale_user.stock)
            db.session.add(stock_item)
        update_stock(order_item=None, stock_item=stock_item, action=Operation.ADDSTOCK,new_qty=int(value['qty']),price=float(value['price']))



        # else:
        #     order_items=OrderItem.query.filter(OrderItem.product_id==str(key)).order_by(OrderItem.sellorder.date).all()
        #     if order_items:
        #         for i in range(len(order_items)):
        #             if order_items[i].stock_count<0 and order_items[i].stock_count + stock_item.count>=0:
        #                 order_items[i].stock_count = order_items[i].count


    return jsonify(request.referrer)


@main.route('/_search_upc',methods=['GET','POST'])
@login_required
def search_upc():
    upc=request.args.get('upc','',type=str)
    # print(upc)
    upc_data = upc.split(',')
    products=[]
    print(upc_data)
    for data in upc_data:

        product = mongo.db.products.find_one({"upc":data})
        if product is not None:
            product["_id"]=str(product["_id"])
            products.append(product)
    # print(products)
    return jsonify(products)




@main.route('/_search_source')
@login_required
def search_source():
    source=request.args.get('source','',type=str)
    sale_user = get_parent()
    # upc_data = upc.split(',')
    products=[]
    if current_user.is_administrator():
        cursor = mongo.db.products.find({"source":source.upper()})
    else:
        # print(sale_user.id)
        cursor = mongo.db.products.find({"$and": [{"source": source.upper()}, {"user": sale_user.id}]})
    if cursor:
        for product in cursor:
            # print(product)
            product["_id"]=str(product["_id"])
            stock_item=StockItem.query.filter(StockItem.product_id==product["_id"]).first()
            if stock_item:
                product["count"]=stock_item.pending_count
                product["avg_price"]=stock_item.avg_price*(current_user.sales_tax + 1)*(1+current_user.profit_rate)*current_user.usd_cny
                product["current_price"]=stock_item.current_price*(current_user.sales_tax + 1)*(1+current_user.profit_rate)*current_user.usd_cny
            else:
                product["count"]=0
                product["avg_price"] = 9999999
                product["current_price"] = 9999999
            products.append(product)
    # print(products)
    return jsonify(products)