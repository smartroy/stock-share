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


@main.route('/', methods=['GET', 'POST'])
def index():
    form = CreateForm()
    if current_user.can(Permission.WRITE_ARTICLES):
        if form.validate_on_submit():
            return redirect(url_for('.new_stock'))
    # if current_user.can(Permission.WRITE_ARTICLES):
    #     print("user can create")
    # else:
    #     print(current_user.role)
        stocks = StockItem.query.filter_by(stock_id=current_user.stock.id).all()
        products=[]
        for i in range(len(stocks)):
            product = mongo.db.products.find_one({'_id':ObjectId(stocks[i].product_id)})
            product['_id'] = str(product['_id'])
            products.append(product)

        return render_template('index.html', form=form,stocks=stocks,products=products)
    else:
        return render_template('index.html')


@main.route('/post/post_product/<int:upc>')
def post_product(upc):
    pass


# @main.route('/stock/new',methods=['GET','POST'])
# def new_stock():
#     form = NewStockForm()
#     product = None
#     if form.validate_on_submit():
#         if form.upc.data is not None:
#             product = mongo.db.products.find_one({"upc":form.upd.data})
#         if product is not None:
#             stock_item = StockItem.query.filter_by(product_id=str(product["_id"]),stock_id=current_user.stock.id).first()
#             if stock_item is not None:
#                 stock_item.count+=1
#                 db.session.commit()
#             else:
#                 stock_item = create_stock_item(product_id=str(product["_id"]),stock=current_user.stock, price=form.price.data)
#                 db.session.add(stock_item)
#                 db.session.commit()
#
#         else:
#             product_id = create_product(name=form.name.data, upc=form.upc.data, sku=form.sku.data,brand=form.brand.data)
#             stock_item = create_stock_item(product_id=product_id, stock=current_user.stock, price=form.price.data)
#             db.session.add(stock_item)
#             db.session.commit()
#
#         return redirect(url_for('.index'))
#     return render_template('new_stock.html', form=form)
    #         product = Product.query.filter_by(upc=form.upc.data).first()
    #         if product is not None:
    #             stock_item = StockItem.query.filter_by(product_id=product.id, stock_id=current_user.stock.id).first()
    #             if stock_item is not None:
    #                 stock_item.count += 1
    #                 db.session.commit()
    #             else:
    #                 stock_item = create_stock_item(product=product, stock=current_user.stock, price=form.price.data)
    #                 db.session.add(stock_item)
    #                 db.session.commit()
    #         else:
    #             product = create_product(name = form.name.data, upc=form.upc.data, sku=form.sku.data)
    #             stock_item = create_stock_item(product=product, stock=current_user.stock, price=form.price.data)
    #             db.session.add(product)
    #             db.session.add(stock_item)
    #             db.session.commit()
    #     else:
    #         stock_item=create_stock_item(name = form.name.data, stock=current_user.stock, price=form.price.data)
    #         db.session.add(stock_item)
    #         db.session.commit()
    #     return redirect(url_for('.index'))




# @main.route('/_add_stock')
# def add_stock():
#     product_id = request.args.get('product_id',type=str)
#     price = request.args.get('price',type=float)
#     item = StockItem.query.filter(StockItem.product_id==product_id, StockItem.stock_id==current_user.stock.id).all()
#     if not item:
#         # print("item not found")
#         item = create_stock_item(product_id=product_id, stock=current_user.stock,price=price)
#         db.session.add(item)
#     else:
#         new_count = int(request.args.get('qty',type=int))
#         item[0].count += new_count
#         item[0].price = price
#     db.session.commit()
#     return jsonify(url_for('.index'))
#
#
# @main.route('/_search_upc')
# def search_upc():
#     upc=request.args.get('upc','',type=str)
#     upc_data = upc.split(',')
#     products=[]
#     for data in upc_data:
#         product = mongo.db.products.find_one({"upc":data})
#         if product is not None:
#             product["_id"]=str(product["_id"])
#             products.append(product)
#
#     return jsonify(products)






# @main.route('/order/sell_orders',methods=['GET','POST'])
# def sell_orders():
#     form = CreateForm()
#     if current_user.can(Permission.WRITE_ARTICLES):
#         if form.validate_on_submit():
#
#             return redirect(url_for('.new_sell'))
#     # if current_user.can(Permission.WRITE_ARTICLES):
#     #     print("user can create")
#     # else:
#     #     print(current_user.role)
#         orders = SellOrder.query.filter_by(user_id=current_user.id).all()
#         return render_template('sellorders.html', form=form,orders=orders)
#     else:
#         return render_template('sellorders.html')
#
#
# @main.route('/order/new_sell',methods=['GET','POST'])
# def new_sell():
#
#     if request.method=='POST':
#         customer = Customer.query.filter(and_(Customer.name==request.form['buyername'], Customer.cellphone==request.form['cellphone'])).first()
#         if customer is None:
#             customer = create_customer(user=current_user, name=request.form['buyername'],
#                                    address=request.form['address'], cellphone=request.form['cellphone'])
#             db.session.add(customer)
#         order = SellOrder(user=current_user, customer=customer)
#
#         db.session.add(order)
#         upcs = request.form.getlist('upc')
#         names = request.form.getlist('name')
#         counts = request.form.getlist('qty')
#         prices = request.form.getlist('price')
#
#         for i in range(len(upcs)):
#             product = mongo.db.products.find_one({"upc":upcs[i]})
#             if product is not None:
#                 stock_item = StockItem.query.filter(and_(StockItem.product_id==str(product['_id']), StockItem.stock==current_user.stock)).first()
#                 if stock_item:
#                     print(stock_item.count)
#                     stock_item.count = stock_item.count - int(counts[i])
#                 else:
#                     stock_item = create_stock_item(product_id=str(product['_id']),stock=current_user.stock)
#                     stock_item.count = 0 - int(counts[i])
#                     db.session.add(stock_item)
#             order_item = OrderItem(sell_price=float(prices[i]), count= int(counts[i]), sellorder=order)
#             db.session.add(order_item)
#             db.session.commit()
#         return redirect(url_for('.sell_orders'))

    # if sell_form.cancel.data:
    #     return redirect(url_for('.sell_orders'))
    #
    # if sell_form.submit.data:
    #     print('check order details')
    #
    #     if not (item_form.name.data is None and item_form.upc.data==0):
    #         print('new order')
    #         customer = create_customer(user=current_user, name=sell_form.buyer.data, address=sell_form.address.data,zip=0,cellphone=0)
    #         order = SellOrder(user=current_user, customer=customer)
    #         db.session.add(customer)
    #         db.session.add(order)
    #         db.session.commit()
    #     return redirect(url_for('.sell_orders'))
    # if item_form.more.data:
    #
    #     return redirect(url_for(".new_sell"))
    #     # return render_template('new_sell.html', sell_form=sell_form, item_form=item_form, items=new_items)
    # print('render new sell')
    # return render_template('new_sell.html')


# @main.route('/order/details/<int:order_id>',methods=['GET','POST'])
# def order_details(order_id):
#     order = SellOrder.query.get_or_404(order_id)
#     items = order.order_items
#
#     return render_template('order_details.html',order=order, items=items)
#
#
# @main.route('/order/delete/<int:order_id>',methods=['GET','POST'])
# def order_delete(order_id):
#     order = SellOrder.query.get_or_404(order_id)
#     print(order)
#     db.session.delete(order)
#     db.session.commit()
#     return redirect(url_for('.sell_orders'))
#
#
# @main.route('/order/edit/<int:order_id>',methods=['GET','POST'])
# def order_edit(order_id):
#     return 0


@main.route('/user/customer',methods=['GET','POST'])
def my_customer():
    customers = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('my_customers.html',customers=customers)


@main.route('/user/customers/delete/<int:customer_id>',methods=['GET','POST'])
def customer_delete(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    # print(order)
    db.session.delete(customer)
    db.session.commit()
    return redirect(url_for('.my_customer'))


@main.route('/user/customers/edit/<int:customer_id>',methods=['GET','POST'])
def customer_edit(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.address = request.form['address']
        customer.cellphone = request.form['cellphone']
        return redirect(url_for('.my_customer'))
    return render_template('customer_details.html',customer=customer)


# def create_sell(upc=None, sku=None, name=None, price=0, buyer=None, address=None, description=None):
#     if upc in not None:
#         product = Product.query.filter_by(upc=upc).first()
#         if product is not None:

@main.route('/product/all')
@login_required
@admin_required
def list_products():
    #products = Product.query.all()
    products = mongo.db.products.find()
    return render_template("products.html", products=products)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@main.route('/product/add',methods=['GET','POST'])
@login_required
@admin_required
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
            while 1:
                line = (file.readline().rstrip()).decode('utf-8')

                if not line:
                    break
                data = line.split(',')
                create_product(brand=data[0], name=data[1], nick_name=data[2], sku=data[3], size=data[4], color=data[5],p_color=data[6], upc=data[7], source=data[8], figure=[])
        return redirect(url_for('.list_products'))
    return render_template('new_products.html')



@main.route('/user/<username>')
@login_required
def user(username):
    # if not current_user.can(Permission.FOLLOW):
    #     return redirect(url_for('.index'))
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, post=posts)





@main.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


ALLOWED_EXTENSIONS = set(['csv','txt'])