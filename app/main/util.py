from ..models import StockItem, Customer, OrderItem, Role, User, Post, Operation, OrderStatus, Shipment, PurchaseItem
from app import db, mongo
from flask_login import current_user


def create_product(brand="", name="", nick_name="", figure=[], upc="", sku="", size="", color="", p_color="",source="", description=""):
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
        "description": description,
        "user": [current_user.id]
    }
    if source:
        if not mongo.db.sources.find_one({'source':source.upper()}):
            mongo.db.sources.insert({'source':source.upper()})
    product_id = mongo.db.products.insert_one(product).inserted_id
    return product_id
    # return Product(name=name, figure=figure, upc=upc, sku=sku, description=description)


def create_stock_item(product_id, stock,price=0 ):
    return StockItem(product_id=product_id, stock=stock, price=price, count=0)


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


def update_stock(order_item,stock_item, action,new_qty=0,price=0):
    if action == Operation.CREATE:
        stock_item.order_count += order_item.count
        db.session.commit()
    elif action == Operation.SHIP:
        stock_item.count -= order_item.count
        stock_item.order_count -= order_item.count
        order_item.shipped_count = order_item.count
        order_item.status = OrderStatus.SHIPPED
        shipment = Shipment(count=order_item.count, orderitem=order_item)
        db.session.add(shipment)

        db.session.commit()
    elif action == Operation.ADDSTOCK:
        stock_item.price = (stock_item.count * stock_item.price + price * new_qty)/(stock_item.count + new_qty)
        stock_item.count += new_qty
        purchase = PurchaseItem(count=new_qty, get_price=price, product_id=stock_item.product_id)
        db.session.add(purchase)
        db.session.commit()


