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
from .util import get_parent,create_customer,create_stock_item,create_product, create_item, inventory_add
from bson import ObjectId
from ..email import send_email



@main.route('/', methods=['GET', 'POST'])
@login_required
def index():
    sale_user = get_parent()
    form = CreateForm()
    if current_user.can(Permission.POST_PRODUCT):
        if form.validate_on_submit():
            return redirect(url_for('.new_stock'))
    # if sale_user.can(Permission.POST_PRODUCT):
    #     print("user can create")
    # else:
    #     print(sale_user.role)
        stocks = StockItem.query.filter_by(stock_id=sale_user.stock.id).order_by(StockItem.id.desc()).all()
        products=[]
        for i in range(len(stocks)):
            product = mongo.db.products.find_one({'_id':ObjectId(stocks[i].product_id)})
            product['_id'] = str(product['_id'])
            products.append(product)

        return render_template('index.html', form=form,stocks=stocks,products=products)
    else:
        return render_template('index.html')


@main.route('/post/post_product/<int:upc>')
@login_required
def post_product(upc):
    pass

@main.route('/user/customer',methods=['GET','POST'])
def my_customer():
    sale_user = get_parent()
    customers = Customer.query.filter_by(user_id=sale_user.id).all()
    return render_template('my_customers.html',customers=customers)


@main.route('/user/customers/delete/<int:customer_id>',methods=['GET','POST'])
@login_required
def customer_delete(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    # print(order)
    db.session.delete(customer)
    db.session.commit()
    return redirect(url_for('.my_customer'))


@main.route('/user/customers/edit/<int:customer_id>',methods=['GET','POST'])
@login_required
def customer_edit(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.address = request.form['address']
        customer.cellphone = request.form['cellphone']
        return redirect(url_for('.my_customer'))
    return render_template('customer_details.html',customer=customer)


@main.route('/user/<int:user_id>')
@login_required
def user(user_id):
    # if not sale_user.can(Permission.BROWSE):
    #     return redirect(url_for('.index'))
    user = User.query.filter_by(id=user_id).first()
    users=[]
    if user is None:
        abort(404)
    if current_user.can(Permission.ADMINISTER):
        users = User.query.order_by(User.id).all()
    elif current_user.can(Permission.MODERATOR):
        users = current_user.children
    return render_template('user.html', user=user, users=users)


@main.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():

    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.commit()
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


@main.route('/_send_email', methods=['GET', 'POST'])
@login_required
def email_handle():
    data = request.get_json()
    print(data)
    send_email(data['email'], data['subject'], 'auth/email/confirm', user=user,token='')

    return jsonify(request.referrer)


@main.route('/_add_service',methods=['GET', 'POST'])
@login_required
def add_child():
    data = request.get_json()
    print(data)
    if User.query.filter_by(email=data['email']).first():
        flash('email has been registered')
        return jsonify(request.referrer)

    user = User(email=data['email'],
                username='',
                password='stockshare',
                parent_id=current_user.id,
                )
    print(user.role)
    db.session.add(user)
    db.session.commit()
    token = user.generate_confirmation_token()
    send_email(user.email, 'Confirm your account', 'auth/email/confirm', user=user, token=token)
    flash('A confirmation email has been sent to you by email.')
    return jsonify(request.referrer)
# @main.route('/stock/new',methods=['GET','POST'])
# def new_stock():
#     form = NewStockForm()
#     product = None
#     if form.validate_on_submit():
#         if form.upc.data is not None:
#             product = mongo.db.products.find_one({"upc":form.upd.data})
#         if product is not None:
#             stock_item = StockItem.query.filter_by(product_id=str(product["_id"]),stock_id=sale_user.stock.id).first()
#             if stock_item is not None:
#                 stock_item.count+=1
#                 db.session.commit()
#             else:
#                 stock_item = create_stock_item(product_id=str(product["_id"]),stock=sale_user.stock, price=form.price.data)
#                 db.session.add(stock_item)
#                 db.session.commit()
#
#         else:
#             product_id = create_product(name=form.name.data, upc=form.upc.data, sku=form.sku.data,brand=form.brand.data)
#             stock_item = create_stock_item(product_id=product_id, stock=sale_user.stock, price=form.price.data)
#             db.session.add(stock_item)
#             db.session.commit()
#
#         return redirect(url_for('.index'))
#     return render_template('new_stock.html', form=form)
    #         product = Product.query.filter_by(upc=form.upc.data).first()
    #         if product is not None:
    #             stock_item = StockItem.query.filter_by(product_id=product.id, stock_id=sale_user.stock.id).first()
    #             if stock_item is not None:
    #                 stock_item.count += 1
    #                 db.session.commit()
    #             else:
    #                 stock_item = create_stock_item(product=product, stock=sale_user.stock, price=form.price.data)
    #                 db.session.add(stock_item)
    #                 db.session.commit()
    #         else:
    #             product = create_product(name = form.name.data, upc=form.upc.data, sku=form.sku.data)
    #             stock_item = create_stock_item(product=product, stock=sale_user.stock, price=form.price.data)
    #             db.session.add(product)
    #             db.session.add(stock_item)
    #             db.session.commit()
    #     else:
    #         stock_item=create_stock_item(name = form.name.data, stock=sale_user.stock, price=form.price.data)
    #         db.session.add(stock_item)
    #         db.session.commit()
    #     return redirect(url_for('.index'))




# @main.route('/_add_stock')
# def add_stock():
#     product_id = request.args.get('product_id',type=str)
#     price = request.args.get('price',type=float)
#     item = StockItem.query.filter(StockItem.product_id==product_id, StockItem.stock_id==sale_user.stock.id).all()
#     if not item:
#         # print("item not found")
#         item = create_stock_item(product_id=product_id, stock=sale_user.stock,price=price)
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
#     if sale_user.can(Permission.POST_PRODUCT):
#         if form.validate_on_submit():
#
#             return redirect(url_for('.new_sell'))
#     # if sale_user.can(Permission.POST_PRODUCT):
#     #     print("user can create")
#     # else:
#     #     print(sale_user.role)
#         orders = SellOrder.query.filter_by(user_id=sale_user.id).all()
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
#             customer = create_customer(user=sale_user, name=request.form['buyername'],
#                                    address=request.form['address'], cellphone=request.form['cellphone'])
#             db.session.add(customer)
#         order = SellOrder(user=sale_user, customer=customer)
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
#                 stock_item = StockItem.query.filter(and_(StockItem.product_id==str(product['_id']), StockItem.stock==sale_user.stock)).first()
#                 if stock_item:
#                     print(stock_item.count)
#                     stock_item.count = stock_item.count - int(counts[i])
#                 else:
#                     stock_item = create_stock_item(product_id=str(product['_id']),stock=sale_user.stock)
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
    #         customer = create_customer(user=sale_user, name=sell_form.buyer.data, address=sell_form.address.data,zip=0,cellphone=0)
    #         order = SellOrder(user=sale_user, customer=customer)
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





# def create_sell(upc=None, sku=None, name=None, price=0, buyer=None, address=None, description=None):
#     if upc in not None:
#         product = Product.query.filter_by(upc=upc).first()
#         if product is not None:

# @main.route('/product/all')
# @login_required
# def list_products():
#     #products = Product.query.all()
#     if sale_user.is_administrator():
#         products = mongo.db.products.find()
#     else:
#         products = mongo.db.products.find({"user":sale_user.id})
#     return render_template("products.html", products=products)
#
# def allowed_file(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
#
#
# @main.route('/product/add',methods=['GET','POST'])
# @login_required
# def add_products():
#     #products = Product.query.all()
#     if request.method == 'POST':
#         if 'file' not in request.files:
#             flash('No file part')
#             return redirect(request.url)
#         file = request.files['file']
#
#         if file.filename == '':
#             flash('No selected file')
#             return redirect(request.url)
#         if file and allowed_file(file.filename):
#             line = file.readline()
#             while 1:
#                 line = (file.readline().rstrip()).decode('utf-8')
#
#                 if not line:
#                     break
#                 data = line.split(',')
#                 inventory_add(brand=data[0], name=data[1], nick_name=data[2], sku=data[3], size=data[4], color=data[5],p_color=data[6], upc=data[7], source=data[8], figure=[])
                # product=""
                # if data[7]:
                #     product = mongo.db.products.find_one({"upc": data[7]})
                # elif data[0] and data[1]:
                #     product = mongo.db.products.find_one(
                #         {"$and": [{"brand": data[0]}, {"$or": [{"name": data[1]}, {"nick_name": data[2]}]}]})
                # if not product:
                #     create_product(brand=data[0], name=data[1], nick_name=data[2], sku=data[3], size=data[4], color=data[5],p_color=data[6], upc=data[7], source=data[8], figure=[])
                # else:
                #     if not (sale_user.id in product["user"]):
                #         mongo.db.products.update({"_id": product["_id"]}, {'$push': {"user": sale_user.id}})
                #         source = product["source"]
                #         if not mongo.db.sources.find_one({"$and": [{"source":source},{"user":sale_user.id}]}):
                #             mongo.db.sources.update({"source":source},{'$push':{"user":sale_user.id}})

                        # product["user"].append(sale_user.id)
    #     return redirect(url_for('.list_products'))
    # return render_template('new_products.html')


# @main.route('/product/add_manual',methods=['GET','POST'])
# @login_required
# def add_products_manual():
#     if request.method == 'POST':
#         upcs = request.form.getlist('upc')
#         brands = request.form.getlist('brand')
#         names = request.form.getlist('name')
#
#         sizes = request.form.getlist('size')
#         colors = request.form.getlist('color')
#         sources = request.form.getlist('source')
#         for i in range(len(upcs)):
#             inventory_add(brand=brands[i], name=names[i], nick_name=names[i], upc=upcs[i],size=sizes[i],color=colors[i],source=sources[i])
#             # product = ""
#             # if upcs[i]:
#             #     product = mongo.db.products.find_one({"upc": upcs[i]})
#             # elif brands[i] and names[i]:
#             #     product = mongo.db.products.find_one(
#             #         {"$and": [{"brand": brands[i]}, {"$or": [{"name": names[i]}, {"nick_name": names[i]}]}]})
#             # if not product:
#             #     product_id = create_product(brand=brands[i], name=names[i], nick_name=names[i], upc=upcs[i],size=sizes[i],color=colors[i],source=sources[i])
#             # else:
#             #     # print(product)
#             #     # print(sale_user.id)
#             #     if not (sale_user.id in product["user"]):
#             #         mongo.db.products.update({"_id":product["_id"]},{'$push':{"user":sale_user.id}})
#             #         source = product["source"]
#             #         if not mongo.db.sources.find_one({"$and": [{"source": source}, {"user": sale_user.id}]}):
#             #             mongo.db.sources.update({"source": source}, {'$push': {"user": sale_user.id}})
#             #         # product["user"].append(sale_user.id)
#             #     # print(product)
#     return render_template('new_products.html')











