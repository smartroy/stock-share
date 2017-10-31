from ..models import StockItem, Customer, OrderItem, Role, User, Post
from app import db, mongo


def create_product(brand=None, name=None, nick_name=None, figure=[], upc=None, sku=None, size=None, color=None, p_color=None,source=None, description=None):
    product = {
        "brand": brand.upper(),
        "name": name.upper(),
        "nick_name": nick_name.upper(),
        "sku": sku.upper(),
        "size": size.upper(),
        "color": color.upper(),
        "p_color": p_color.upper(),
        "upc": upc,
        "source": source.upper(),
        "fig": figure,
        "description": description
    }
    if source:
        if not mongo.db.sources.find_one({'source':source.upper()}):
            mongo.db.sources.insert({'source':source.upper()})
    product_id = mongo.db.products.insert_one(product).inserted_id
    return product_id
    # return Product(name=name, figure=figure, upc=upc, sku=sku, description=description)


def create_stock_item(price=0, product_id=None, stock=None):
    return StockItem(product_id=product_id, stock=stock, price=price, count=1)


def create_customer(user=None, name=None, address=None,zip=0,cellphone=0):
    return Customer(user=user, name=name, address=address,zip=zip,cellphone=cellphone)


def create_item(count=0, sell_price =0, stockitem=None, sellorder=None ):
    return OrderItem(count=count, sell_price=sell_price,stockitem=stockitem,sellorder=sellorder)


def create_post(user=None, product_id=None, stockitem=None, description=None):
    return Post(user=user, product_id=product_id,stockitem=stockitem,description=description)


def db_init():
    Role.insert_roles()
    user = User(email='kang@example.com',
                username='kang',
                password='19881127')
    print(user.role)
    db.session.add(user)
    db.session.commit()


def insert_product_mongo(file):
    collection = mongo.db.products
    f = open(file, 'r')
    while 1:
        line = f.readline().rstrip()
        if not line:
            break
        data = line.split(',')
        create_product(brand= data[0],name=data[1],nick_name=data[2],sku=data[3],size= data[4],color=data[5],p_color=data[6],upc=data[7],source=data[8],figure=[])

        #collection.insert_one(product)

