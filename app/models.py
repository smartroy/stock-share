from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from . import login_manager
from datetime import datetime
import hashlib
from sqlalchemy.ext.hybrid import hybrid_method

class Permission:
    FOLLOW = 0x01
    COMMENT = 0X02
    WRITE_ARTICLES = 0X04
    MODERATE_COMMENTS = 0X08
    ADMINISTER = 0X80


class OrderStatus:
    CREATED = 0x01
    INSTOCK = 0x02
    SHIPPED = 0x03
    DELIVERED = 0x04
    status = {CREATED:"Created",INSTOCK:"In Stock",SHIPPED:"Shipped", DELIVERED:"Delivered"}

class Operation:
    CREATE = 0x01
    ADDSTOCK = 0x02
    SHIP = 0x03


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
            'User':(Permission.FOLLOW | Permission.COMMENT | Permission.WRITE_ARTICLES, True),
            'Moderator':(Permission.FOLLOW | Permission.COMMENT |
                         Permission.WRITE_ARTICLES | Permission.MODERATE_COMMENTS, False),
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
    confirmed = db.Column(db.Boolean, default=True)
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    avatar_hash = db.Column(db.String(32))
    posts = db.relationship('Post', backref='user', lazy='dynamic')
    stock = db.relationship('Stock', uselist=False, backref='user')
    sell_orders = db.relationship('SellOrder', backref='user', lazy='dynamic')
    customers = db.relationship('Customer', backref='user', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User,self).__init__(**kwargs)
        print('creating user')
        if self.role is None:
            print('assign role')
            if self.email == current_app.config['FLASKY_ADMIN']:
                print('admin')
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                print('normal')
                print(Role.query.filter_by(default=True).first())

                self.role = Role.query.filter_by(default=True).first()

        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(
                self.email.encode('utf-8')).hexdigest()
        if self.stock is None:
            self.stock = Stock()
        self.sell_orders = []
        self.customers = []
        print(self.role)
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
    price = db.Column(db.Float)

    product_id = db.Column(db.Text)
    order_count = db.Column(db.Integer,default=0)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'))
    posts = db.relationship('Post',backref='stockitem',lazy='dynamic')

    @hybrid_method
    def need_more(self):
        return self.count - self.order_count


class SellOrder(db.Model):
    __tablename__ = 'sellorders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.DateTime(), default=datetime.utcnow)
    order_items = db.relationship('OrderItem', backref='sellorder', lazy='dynamic',cascade="delete")
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    status = db.Column(db.Integer, default=OrderStatus.CREATED)
    total_get = db.Column(db.Float)
    total_sell = db.Column(db.Float)
    # def __init__(self, **kwargs):
    #     super(SellOrder, self).__init__(**kwargs)
    #     self.order_items = []


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer,default=0)
    stock_count = db.Column(db.Integer)
    shipped_count = db.Column(db.Integer, default=0)
    sell_price = db.Column(db.Float)
    get_price = db.Column(db.Float,default=0.0)
    type = db.Column(db.Text)
    note = db.Column(db.Text)
    status = db.Column(db.Integer, default=OrderStatus.CREATED)
    product_id = db.Column(db.Text)
    order_id = db.Column(db.Integer, db.ForeignKey('sellorders.id'))
    shipment = db.relationship('Shipment', backref='orderitem', lazy='dynamic', cascade="delete")


class Shipment(db.Model):
    __tablename__ = 'shipments'
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0)
    track = db.Column(db.Text)
    orderitem_id = db.Column(db.Integer, db.ForeignKey('order_items.id'))


class Customer(db.Model):
    __tablename__='customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    address = db.Column(db.Text)
    cellphone = db.Column(db.Text,default=0)
    zip = db.Column(db.Text,default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    orders = db.relationship('SellOrder', backref='customer', lazy='dynamic')
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
