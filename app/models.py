from app import db, mongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from . import login_manager
from datetime import datetime
import hashlib
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import backref
from bson import ObjectId
from sqlalchemy import and_, or_

class Permission:
    BROWSE = 0x01
    SHOP = 0X02
    POST_PRODUCT = 0X04
    ADD_PRODUCT = 0X08
    MODERATOR = 0x0f
    ADMINISTER = 0Xff


class OrderStatus:
    CREATED = 0x01
    INSTOCK = 0x02
    PAID = 0x03
    SHIPPED = 0x04
    DELIVERED = 0x05
    CANCEL = 0x90
    status = {CREATED:"Created",PAID:"Paid",INSTOCK:"In Stock",SHIPPED:"Shipped", DELIVERED:"Delivered", CANCEL:"Canceled"}

class Operation:
    CREATE = 0x01
    ADDSTOCK = 0x02
    SHIP = 0x03
    SHIP_CANCEL = 0x04


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)

    def __repr__(self):
        return '<Role %r>' % self.name

    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User':(Permission.BROWSE | Permission.SHOP | Permission.POST_PRODUCT, False),
            'Moderator':(Permission.BROWSE | Permission.SHOP |
                         Permission.POST_PRODUCT | Permission.ADD_PRODUCT, True),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()


class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    posts = db.relationship('Post', backref='user', lazy='dynamic')
    stock = db.relationship('Stock', uselist=False, backref='user')

    sell_orders = db.relationship('SellOrder', backref='user', lazy='dynamic',foreign_keys='[SellOrder.user_id]')
    create_orders = db.relationship('SellOrder', backref='creator', lazy='dynamic', foreign_keys='[SellOrder.creator_id]')
    payments = db.relationship('Payment', backref='user', lazy='dynamic', foreign_keys='[Payment.user_id]')
    payments_creator = db.relationship('Payment', backref='creator', lazy='dynamic',
                                    foreign_keys='[Payment.creator_id]')
    shipments = db.relationship('Shipment', backref='user', lazy='dynamic', foreign_keys='[Shipment.user_id]')
    shipments_creator = db.relationship('Shipment', backref='creator', lazy='dynamic',
                                       foreign_keys='[Shipment.creator_id]')


    usd_cny = db.Column(db.Float,default=0)
    profit_rate = db.Column(db.Float, default=0.15)
    sales_tax = db.Column(db.Float,default=0.0625)
    # product_items = db.relationship('ProductItem', uselist=False, backref='user')
    # bill = db.relationship('SellOrder',backref='bill',lazy='dynamic',foreign_keys='[SellOrder.bill_id]')

    customers = db.relationship('Customer', backref='user', lazy='dynamic')
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    children = db.relationship('User',backref=backref('parent', remote_side=[id]))
    def __init__(self, **kwargs):
        super(User,self).__init__(**kwargs)
        # print('creating user')
        if self.role is None:
            # print('assign role')
            if self.email == current_app.config['FLASKY_ADMIN']:
                # print('admin')
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                # print('normal')
                print(Role.query.filter_by(default=True).first())

                self.role = Role.query.filter_by(default=True).first()

        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()
        if self.stock is None:
            self.stock = Stock()
        self.sell_orders = []
        self.customers = []
        # print(self.role)
        db.session.commit()

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm')!=self.id:
            return False
        self.confirmed = True
        db.session.add(self)

        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(
            self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)


class Post(db.Model):
    __tablename__='posts'
    id = db.Column(db.Integer, primary_key=True)

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_id = db.Column(db.Text)
    stockitem_id = db.Column(db.Integer, db.ForeignKey('stock_items.id'))
    description = db.Column(db.Text)


class Stock(db.Model):
    __tablename__='stocks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    stock_items = db.relationship('StockItem',backref='stock',lazy='dynamic')

    def __init__(self, **kwargs):
        super(Stock,self).__init__(**kwargs)
        self.stock_items = []


class StockItem(db.Model):
    __tablename__='stock_items'
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer,default=0)
    avg_price = db.Column(db.Float,default=0)
    current_price = db.Column(db.Float,default=0)
    # shipped_count = db.Column(db.Integer, default=0)
    product_id = db.Column(db.Text)
    # order_count = db.Column(db.Integer,default=0)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'))
    posts = db.relationship('Post',backref='stockitem',lazy='dynamic')

    @hybrid_property
    def need_count(self):

        return max(0,self.pending_count - self.count)


    @hybrid_property
    def pending_count(self):
        return self.order_count - self.shipped_count

    @hybrid_property
    def order_count(self):
        count=0

        order_items=OrderItem.query.filter(OrderItem.product_id==self.product_id, OrderItem.active==True).all()
        if order_items:
            for item in order_items:
                # print(str(item.sellorder.i)
                if item.sellorder.user==self.stock.user:
                    count+=item.count
        return count

    @hybrid_property
    def shipped_count(self):
        count=0
        order_items= OrderItem.query.filter(OrderItem.product_id==self.product_id, OrderItem.active==True).all()
        if order_items:
            for item in order_items:
                if item.sellorder.user==self.stock.user:
                    count+=item.shipped_count
        return count

    @hybrid_property
    def product_info(self):
        product = mongo.db.products.find_one({'_id': ObjectId(self.product_id)})
        product["_id"] = str(product["_id"])
        return product


class SellOrder(db.Model):
    __tablename__ = 'sellorders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.DateTime(), default=datetime.utcnow)
    order_items = db.relationship('OrderItem', backref='sellorder', lazy='dynamic',cascade="delete")
    # ship_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    # bill_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    # ship_addr= db.Column(db.Text)
    buyer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    # paid = db.Column(db.Boolean,default=False)

    status = db.Column(db.Integer, default=OrderStatus.CREATED)
    # total_get = db.Column(db.Float)
    # total_sell = db.Column(db.Float)
    active = db.Column(db.Boolean, default=True)
    # def __init__(self, **kwargs):
    #     super(SellOrder, self).__init__(**kwargs)
    #     self.order_items = []
    @hybrid_property
    def paid(self):
        for item in self.order_items:

            if not item.paid:
                return False
        return True

    @hybrid_property
    def shipped(self):
        for item in self.order_items:

            if not item.shipped:
                return False
        return True

    @hybrid_property
    def total_sell(self):
        total=0.0
        for item in self.order_items:
            total+=item.count*item.sell_price

        return total

    @hybrid_property
    def total_get(self):
        total=0
        for item in self.order_items:
            total+=item.count*item.get_price
        return total
        # print(all([item.paid for item in self.order_items]))
        # return all([item.paid for item in self.order_items])
            # all([item.paid for item in self.order_items])
    # @paid.expression
    # def paid(cls):



class ProductItem(db.Model):
    __tablename__='productitem'
    id = db.Column(db.Integer, primary_key=True)
    # user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # buyer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    # product_id = db.Column(db.Text)
    # order_items = db.relationship('OrderItem', backref='productitem', lazy='dynamic', cascade="delete")
    # shipments = db.relationship('Shipment', backref='productitem', lazy='dynamic', cascade="delete")
    @hybrid_property
    def count(self):
        total = 0
        for item in self.order_items:
            total += item.count
        for shipment in self.shipments:
            total -= shipment.count
        return total


class OrderItem(db.Model):
    __tablename__ = 'orderitems'
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer,default=0)
    stock_count = db.Column(db.Integer)
    shipped_count = db.Column(db.Integer, default=0)
    # paid_count = db.Column(db.Integer, default=0)
    sell_price = db.Column(db.Float)
    get_price = db.Column(db.Float,default=0.0)
    type = db.Column(db.Text)
    note = db.Column(db.Text)
    status = db.Column(db.Integer, default=OrderStatus.CREATED)
    product_id = db.Column(db.Text)
    # productitem_id = db.Column(db.Integer, db.ForeignKey('productitem.id'))
    # paid = db.Column(db.Boolean, default=False)
    order_id = db.Column(db.Integer, db.ForeignKey('sellorders.id'))
    active = db.Column(db.Boolean,default=True)
    # shipitems = db.relationship('ShipItem', backref='orderitem', lazy='dynamic', cascade="delete")
    paymentitems = db.relationship('PaymentItem', backref='orderitem', lazy='dynamic', cascade="delete")
    shipmentitems = db.relationship('ShipmentItem', backref='orderitem', lazy='dynamic', cascade="delete")

    @hybrid_property
    def paid(self):
        return self.paid_count >= self.count

    @hybrid_property
    def checked_count(self):
        count=0
        for item in self.paymentitems:
            # print(item.count)
            if item and (not item.payment.confirmed):
                count += item.count

        return count

    @hybrid_property
    def paid_count(self):
        count = 0
        for item in self.paymentitems:
            if item and item.payment.confirmed:
                count += item.count

        return count


    @hybrid_property
    def shipped(self):
        return self.shipped_count>=self.count

    @hybrid_property
    def shipped_count(self):
        count=0
        for item in self.shipmentitems:
            if item and item.released:
                count+=item.count
        return count

    @hybrid_property
    def packaged_count(self):
        count=0
        for item in self.shipmentitems:
            if item and (not item.released):
                count+=item.count
        return count

    @hybrid_property
    def product_info(self):
        product = mongo.db.products.find_one({'_id':ObjectId(self.product_id)})
        product["_id"] = str(product["_id"])
        return product


class Payment(db.Model):
    __tablename__="payments"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.DateTime(), default=datetime.utcnow)
    buyer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    confirmed = db.Column(db.Boolean, default=False)
    paymentitems = db.relationship('PaymentItem', backref='payment', lazy='dynamic', cascade="all, delete-orphan")
    confirm_id = db.Column(db.Text)


    @hybrid_property
    def total(self):
        total=0
        for item in self.paymentitems:
            total+=item.count * item.price
        return total

    def gen_confirmID(self):
        self.confirm_id = str(self.user.id).zfill(5) + str(self.id).zfill(5)
        db.session.commit()

class PaymentItem(db.Model):
    ___tablename__ = "paymentitems"
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    price = db.Column(db.Float)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'))
    orderitem_id = db.Column(db.Integer, db.ForeignKey('orderitems.id'))



class PurchaseItem(db.Model):
    __tablename__='purchaseitem'
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0)
    get_price = db.Column(db.Float, default=0.0)
    # type = db.Column(db.Text)
    source = db.Column(db.Text)
    product_id = db.Column(db.Text)
    date = db.Column(db.DateTime(),default=datetime.utcnow)

class Shipment(db.Model):
    __tablename__ = 'shipments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # count = db.Column(db.Integer, default=0)
    track = db.Column(db.Text)

    buyer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    # stockitem_id = db.Column(db.Integer, db.ForeignKey('stock_items.id'))
    date = db.Column(db.DateTime(), default=datetime.utcnow)
    addr = db.Column(db.Text)
    cell = db.Column(db.Text)
    name = db.Column(db.Text)
    active = db.Column(db.Boolean,default=True)
    # productitem_id = db.Column(db.Integer, db.ForeignKey('productitem.id'))
    shipmentitems = db.relationship('ShipmentItem', backref='shipment', lazy='dynamic', cascade="delete")
    released = db.Column(db.Boolean, default=False)

    @hybrid_property
    def release_ready(self):
        for item in self.shipmentitems:
            if not item.release_ready:
                return False
        return True

class ShipmentItem(db.Model):
    __tablename__='shipment_items'
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0)
    shipment_id = db.Column(db.Integer, db.ForeignKey('shipments.id'))
    orderitem_id = db.Column(db.Integer, db.ForeignKey('orderitems.id'))
    released = db.Column(db.Boolean, default=False)

    @hybrid_property
    def release_ready(self):
        stock=self.shipment.user.stock
        stockitem=StockItem.query.filter(StockItem.stock_id==stock.id,StockItem.product_id==self.orderitem.product_id).all()
        if stockitem[0].count>=self.count:
            return True
        else:
            return False


class Customer(db.Model):
    __tablename__='customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    address = db.Column(db.Text)
    cellphone = db.Column(db.Text,default=0)
    zip = db.Column(db.Text,default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # bill = db.relationship('SellOrder',backref='bill',lazy='dynamic',foreign_keys='[SellOrder.bill_id]')
    buy_orders = db.relationship('SellOrder',backref='buyer',lazy='dynamic')
    shipments = db.relationship('Shipment',backref='buyer',lazy='dynamic')
    # productitems = db.relationship('ProductItem', uselist=False, backref='buyer')
    payments = db.relationship('Payment',backref='buyer',lazy='dynamic')

    # ship = db.relationship('SellOrder',backref='ship',lazy='dynamic',foreign_keys='[SellOrder.ship_id]')
# class Order(db.Model):
#     __tablename__='orders'
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
#     order_item = db.relationship('OrderItem', backref='order', lazy='dynamic')
#
#
# class OrderItem(db.Model):
#     __tablename__='stock_items'
#     id = db.Column(db.Integer, primary_key=True)
#     count = db.Column(db.Integer)
#     product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
#     order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser

# class Product(db.Model):
#     __tablename__='products'
#     id = db.Column(db.Integer, primary_key=True)
#     brand = db.Column(db.Text)
#     nick_name = db.Column(db.Text)
#     size = db.Column(db.Text)
#     color = db.Column(db.Text)
#     p_color = db.Column(db.Text)
#     source = db.Column(db.Text)
#     name = db.Column(db.Text)
#     figure = db.Column(db.Text)
#     description = db.Column(db.Text)
#     sku = db.Column(db.Text)
#     upc = db.Column(db.Text)
#     #count = db.Column(db.Integer)
#     posts = db.relationship('Post',backref='product',lazy='dynamic')
#     stock_items = db.relationship('StockItem',backref='product',lazy='dynamic')
#     order_item = db.relationship('OrderItem', backref='product', lazy='dynamic')
#     #order_items = db.relationship('OrderItem',backref='product',lazy='dynamic')
#
#     @staticmethod
#     def insert_product(file):
#         f = open(file,'r')
#         while 1:
#             line = f.readline().rstrip()
#             if not line:
#                 break
#             data = line.split(',')
#             product=Product(brand=data[0],name=data[1],nick_name=data[2],sku=data[3],size=data[4],color=data[5],p_color=data[6],upc=data[7],source=data[8])
#             db.session.add(product)
#         db.session.commit()
