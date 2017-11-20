#created by Shikang Xu
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
from .util import create_customer,create_stock_item,create_product, create_item, inventory_add
from bson import ObjectId
from ..email import send_email

ALLOWED_EXTENSIONS = set(['csv','txt'])

@main.route('/product/all')
@login_required
def list_products():
    #products = Product.query.all()
    products={}
    sources = []
    if current_user.is_administrator:
        cursor = mongo.db.sources.find()
    else:
        cursor = mongo.db.sources.find({"user": current_user.id})
    for doc in cursor:
        sources.append(doc["source"])

    if current_user.is_administrator():
        products = mongo.db.products.find()
    else:
        products = mongo.db.products.find({"user":current_user.id})
    return render_template("products.html", products=products,sources=sources)


@main.route('/_sort_products',methods=['GET','POST'])
@login_required
def sort_products():
    source = request.args.get('source', '', type=str)
    products = []
    if source.upper() =="ALL":
        search_dict ={}
    else:
        search_dict = {"source":source.upper()}
    if current_user.is_administrator():
        products = list(mongo.db.products.find(search_dict))
    else:
        search_dict["user"] = current_user.id
        products = list(mongo.db.products.find(search_dict))
    for product in products:
        product["_id"] = str(product["_id"])
    return jsonify(products)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main.route('/product/add',methods=['GET','POST'])
@login_required
def add_products():
    #products = Product.query.all()
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            line = file.readline()
            while 1:
                line = (file.readline().rstrip()).decode('utf-8')

                if not line:
                    break
                data = line.split(',')
                inventory_add(brand=data[0], name=data[1], nick_name=data[2], sku=data[3], size=data[4], color=data[5],p_color=data[6], upc=data[7], source=data[8], figure=[])
        return redirect(url_for('.list_products'))
    return render_template('new_products.html')


@main.route('/product/add_manual',methods=['GET','POST'])
@login_required
def add_products_manual():
    if request.method == 'POST':
        upcs = request.form.getlist('upc')
        brands = request.form.getlist('brand')
        names = request.form.getlist('name')

        sizes = request.form.getlist('size')
        colors = request.form.getlist('color')
        sources = request.form.getlist('source')
        for i in range(len(upcs)):
            inventory_add(brand=brands[i], name=names[i], nick_name=names[i], upc=upcs[i],size=sizes[i],color=colors[i],source=sources[i])

    return redirect(url_for('.list_products'))


@main.route('/product/product_details/<product_id>',methods=['GET','POST'])
@login_required
def product_details(product_id):

    product = mongo.db.products.find_one({'_id':ObjectId(product_id)})
    product['_id'] = str(product['_id'])
    if request.method == 'POST':
        new_value ={}
        # print(request.form)
        for key,value in product.items():
            if not(key == "user" or key == "fig" or key=="_id"):
                new_value[key] = request.form.get(key)
        # print(new_value)
        mongo.db.products.update_one({"_id":ObjectId(product_id)},{"$set":new_value})
        product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
    return render_template('product_details.html', product=product)


@main.route('/product/product_delete/<product_id>',methods=['GET','POST'])
@login_required
def product_delete(product_id):
    product = mongo.db.products.find_one({"_id":ObjectId(product_id)})
    mongo.db.products.update({"_id": ObjectId(product_id)}, {'$pull': {"user": current_user.id}})
    return redirect(url_for('.list_products'))