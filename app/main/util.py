from ..models import StockItem, Customer, OrderItem, Role, User, Post, Operation, OrderStatus, Shipment, PurchaseItem, SellOrder
from app import db, mongo
from flask_login import current_user
from sqlalchemy import and_, or_

def create_product(brand="", name="", nick_name="", figure=[], upc="", sku="", size="", color="", p_color="",source="", description=""):
    if not source:
        source = "OTHERS"
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
            mongo.db.sources.insert({'source':source.upper(),"user":[current_user.id]})
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


def delete_order(order):
    items = order.order_items.all()

    for i in range(len(items)):
        # print(items[i].product_id)
        delete_orderItem(items[i])

        # db.session.delete(items[i])
    db.session.delete(order)
    db.session.commit()


def delete_orderItem(item):
    sale_user = get_parent()
    stock_item = StockItem.query.filter(
        and_(StockItem.product_id == item.product_id, StockItem.stock == sale_user.stock)).first()
    # print(product)
    # product['_id'] = str(product['_id'])

    stock_item.order_count -= item.count
    shipments = item.shipment.all()
    for i in range(len(shipments)):
        stock_item.count += shipments[i].count
        stock_item.shipped_count -= shipments[i].count
        db.session.delete(shipments[i])

    db.session.delete(item)
    db.session.commit()


def update_stock(**kwargs):
    sale_user = get_parent()
    # sale_user = get_parent()
    if kwargs['action'] == Operation.CREATE:
        kwargs['stock_item'].order_count += kwargs['order_item'].count
        db.session.commit()
    elif kwargs['action'] == Operation.SHIP:
        ship_info=kwargs['ship_info']
        kwargs['stock_item'].count -= int(ship_info['qty'])
        kwargs['stock_item'].shipped_count += int(ship_info['qty'])
        kwargs['order_item'].shipped_count += int(ship_info['qty'])
        if kwargs['order_item'].count <= kwargs['order_item'].shipped_count:
            kwargs['order_item'].status = OrderStatus.SHIPPED
        shipment = Shipment(count=int(ship_info['qty']),name=ship_info['name'],cell=ship_info['cell'],addr=ship_info['addr'], orderitem=kwargs['order_item'])
        db.session.add(shipment)
        db.session.commit()
    elif kwargs['action'] == Operation.SHIP_CANCEL:
        shipment = kwargs['shipment']
        stock_item = kwargs['stock_item']
        order_item = shipment.orderitem
        stock_item.count += shipment.count
        stock_item.shipped_count -= shipment.count
        order_item.shipped_count -= shipment.count
        if order_item.shipped_count < order_item.count:
            order_item.status = OrderStatus.CREATED
        db.session.delete(shipment)
        db.session.commit()

    elif kwargs['action'] == Operation.ADDSTOCK:
        kwargs['stock_item'].price = (kwargs['stock_item'].count * kwargs['stock_item'].price +
                                                kwargs['price'] * kwargs['new_qty']) / (
                                               kwargs['stock_item'].count + kwargs['new_qty'])
        kwargs['stock_item'].count += kwargs['new_qty']
        purchase = PurchaseItem(count=kwargs['new_qty'], get_price = kwargs['price'], product_id = kwargs[
            'stock_item'].product_id)
        db.session.add(purchase)
        db.session.commit()
    # if action == Operation.CREATE:
    #     stock_item.order_count += order_item.count
    #     db.session.commit()
    # elif action == Operation.SHIP:
    #     stock_item.count -= ship_qty
    #     stock_item.shipped_count += ship_qty
    #     order_item.shipped_count += ship_qty
    #     if order_item.count<= order_item.shipped_count:
    #         order_item.status = OrderStatus.SHIPPED
    #     shipment = Shipment(count=ship_qty, orderitem=order_item)
    #     db.session.add(shipment)
    #
    #     db.session.commit()
    # elif action == Operation.ADDSTOCK:
    #     stock_item.price = (stock_item.count * stock_item.price + price * new_qty)/(stock_item.count + new_qty)
    #     stock_item.count += new_qty
    #     purchase = PurchaseItem(count=new_qty, get_price=price, product_id=stock_item.product_id)
    #     db.session.add(purchase)
    #     db.session.commit()


def inventory_add(brand="", name="", nick_name="", upc="", sku="", size="", color="", p_color="",source="", description="",figure=[]):
    sale_user = get_parent()
    product = ""
    if upc:
        product = mongo.db.products.find_one({"upc": upc})
    elif brand and name:
        product = mongo.db.products.find_one(
            {"$and": [{"brand": brand}, {"$or": [{"name": name}, {"nick_name": name}]}]})
    if not product:
        product_id = create_product(brand=brand, name=name, nick_name=nick_name, upc=upc, size=size,
                                    color=color, p_color=p_color, source=source,description=description,figure=figure)
    else:
        # print(product)
        # print(current_user.id)
        if not (sale_user.id in product["user"]):
            mongo.db.products.update({"_id": product["_id"]}, {'$push': {"user": sale_user.id}})
            source = product["source"]
            if not mongo.db.sources.find_one({"$and": [{"source": source}, {"user": sale_user.id}]}):
                mongo.db.sources.update({"source": source}, {'$push': {"user": sale_user.id}})


def get_orders():
    if current_user.role.name == 'User':
        orders = SellOrder.query.filter_by(user_id=current_user.parent.id).order_by(SellOrder.id.asc()).all()
    else:
        orders = SellOrder.query.filter_by(user_id=current_user.id).order_by(SellOrder.id.asc()).all()
    return orders


def get_parent():
    if current_user.role.name == 'User':
        return current_user.parent
    else:
        return current_user