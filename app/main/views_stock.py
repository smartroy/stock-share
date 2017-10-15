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
from .util import create_customer,create_stock_item,create_product, create_item, create_post
from bson import ObjectId


@main.route('/stock/new',methods=['GET','POST'])
def new_stock():
    form = NewStockForm()
    product = None
    if form.validate_on_submit():
        if form.upc.data is not None:
            product = mongo.db.products.find_one({"upc":form.upd.data})
        if product is not None:
            stock_item = StockItem.query.filter_by(product_id=str(product["_id"]),stock_id=current_user.stock.id).first()
            if stock_item is not None:
                stock_item.count+=1
                db.session.commit()
            else:
                stock_item = create_stock_item(product_id=str(product["_id"]),stock=current_user.stock, price=form.price.data)
                db.session.add(stock_item)
                db.session.commit()

        else:
            product_id = create_product(name=form.name.data, upc=form.upc.data, sku=form.sku.data,brand=form.brand.data)
            stock_item = create_stock_item(product_id=product_id, stock=current_user.stock, price=form.price.data)
            db.session.add(stock_item)
            db.session.commit()

        return redirect(url_for('.index'))
    return render_template('new_stock.html', form=form)


@main.route('/stock/item_post/<int:item_id>')
def stock_item_post(item_id):
    item = StockItem.query.filter(StockItem.id==item_id).first()

    post = Post.query.filter(Post.stockitem_id==item.id, Post.user_id==current_user.id).all()
    print(post)
    if not post:
        print('create new post')
        post = create_post(user=current_user, stockitem=item, product_id=item.product_id, description=None)
        db.session.add(post)
        db.session.commit()
    return redirect(url_for('.post_all'))


@main.route('/post/all')
def post_all():
    form = CreateForm()
    if current_user.can(Permission.WRITE_ARTICLES):
        if form.validate_on_submit():
            return redirect(url_for('.new_stock'))
            # if current_user.can(Permission.WRITE_ARTICLES):
            #     print("user can create")
            # else:
            #     print(current_user.role)
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
    # post=Post.query.filter_by(user_id=current_user.id).all()



@main.route('/stock/item_edit/<int:item_id>')
def stock_item_edit(item_id):
    pass


@main.route('/stock/item_delete/<int:item_id>')
def stock_item_delete(item_id):
    stock_item = StockItem.query.get_or_404(item_id)
    db.session.delete(stock_item)
    db.session.commit()
    return redirect(url_for('.index'))



@main.route('/_add_stock')
def add_stock():
    product_id = request.args.get('product_id',type=str)
    price = request.args.get('price',type=float)
    item = StockItem.query.filter(StockItem.product_id==product_id, StockItem.stock_id==current_user.stock.id).all()
    new_count = int(request.args.get('qty', type=int))
    if not item:
        # print("item not found")
        item = create_stock_item(product_id=product_id, stock=current_user.stock,price=price)
        item.count = new_count
        db.session.add(item)
    else:

        item[0].count += new_count
        item[0].price = price
    db.session.commit()
    return jsonify(url_for('.index'))


@main.route('/_search_upc')
def search_upc():
    upc=request.args.get('upc','',type=str)
    upc_data = upc.split(',')
    products=[]
    for data in upc_data:
        product = mongo.db.products.find_one({"upc":data})
        if product is not None:
            product["_id"]=str(product["_id"])
            products.append(product)

    return jsonify(products)