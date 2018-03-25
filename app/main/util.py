from ..models import *
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


def create_stock_item(product_id, stock):
    return StockItem(product_id=product_id, stock=stock,count=0)


def create_customer(user=None, name=None, address=None,zip=0,cellphone=0):
    return Customer(user=user, name=name, address=address,zip=zip,cellphone=cellphone)

def create_productitem(user=None, buyer=None, product_id=""):
    return ProductItem(user=user, buyer=buyer, product_id=product_id)


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

def create_order(user,buyer,creator,order_data):
    order = SellOrder(user=user, buyer=buyer, creator=creator)

    db.session.add(order)
    db.session.commit()
    # total_sell = 0
    for key, value in order_data.items():

        order_item = create_order_item(key,value,order,user,buyer)
        # total_sell += order_item.count * order_item.sell_price
    # order.total_sell = total_sell
    db.session.commit()
    return order


def create_payment(pay):
    sales_user=get_parent()
    buyer = OrderItem.query.get_or_404(list(pay.keys())[0]).sellorder.buyer
    payment = Payment(user=sales_user,creator=current_user,buyer=buyer)
    db.session.add(payment)
    db.session.commit()
    for key,value in pay.items():
        order_item = OrderItem.query.get_or_404(key)
        payment_item = PaymentItem(payment=payment, orderitem=order_item,count=value,price=order_item.sell_price)
        db.session.add(payment_item)
        db.session.commit()
    payment.gen_confirmID()


def create_shipment(ship_data):
    sales_user=get_parent()
    # print(ship_data)
    # print(list(ship_data["items"].keys())[0])
    # print(ship_data)
    # print(ship_data.keys)
    buyer = OrderItem.query.get_or_404(list(ship_data["items"].keys())[0]).sellorder.buyer
    shipment = Shipment(user=sales_user,creator=current_user,buyer=buyer,addr=ship_data["addr"],cell=ship_data["cell"],name=ship_data["name"])
    db.session.add(shipment)
    db.session.commit()

    for key, value in ship_data["items"].items():
        order_item = OrderItem.query.get_or_404(key)
        shipment_item = ShipmentItem(shipment=shipment, orderitem=order_item,count=value["qty"])
        db.session.add(shipment_item)
        db.session.commit()



def create_order_item(key,value,order,user,buyer):
    order_item = OrderItem(sell_price=float(value['price']), count=int(value['qty']), sellorder=order,
                           product_id=str(key))

    stock_item = StockItem.query.filter(
        and_(StockItem.product_id == str(key), StockItem.stock == user.stock)).first()
    order_item.note = str(value['note'])
    db.session.add(order_item)
    db.session.commit()

    if not stock_item:
        stock_item = create_stock_item(product_id=str(key), stock=user.stock)
        db.session.add(stock_item)
        db.session.commit()
    db.session.commit()
    # update_stock(order_item=order_item, stock_item=stock_item, action=Operation.CREATE)
    return order_item


def delete_order(order):
    items = order.order_items.all()

    for item in items:
        # print(items[i].product_id)
        if item.active:
            delete_orderItem(item)

        # db.session.delete(items[i])
    order.active = False
    order.status = OrderStatus.CANCEL
    db.session.commit()


def delete_orderItem(item):
    sale_user = get_parent()
    stock_item = StockItem.query.filter(
        and_(StockItem.product_id == item.product_id, StockItem.stock == sale_user.stock)).first()
    # print(product)
    # product['_id'] = str(product['_id'])
    # stock_item.productitem_id = None
    stock_item.order_count -= item.count

    item.sellorder.total_sell -= item.count*item.sell_price
    item.active=False
    db.session.commit()
    items = OrderItem.query.filter(OrderItem.order_id==item.sellorder.id,OrderItem.active==True).all()
    # print()
    if not items:
        print("empty order")
        item.sellorder.active = False
        item.sellorder.status = OrderStatus.CANCEL
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
        kwargs['stock_item'].avg_price = (kwargs['stock_item'].count * kwargs['stock_item'].avg_price +
                                                kwargs['price'] * kwargs['new_qty']) / (
                                               kwargs['stock_item'].count + kwargs['new_qty'])
        kwargs['stock_item'].current_price = kwargs['price']
        kwargs['stock_item'].count += kwargs['new_qty']
        purchase = PurchaseItem(count=kwargs['new_qty'], get_price = kwargs['price'], product_id = kwargs['stock_item'].product_id)
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
    sale_user = get_parent()
    # if current_user.role.name == 'User':
    #     orders = SellOrder.query.filter_by(user_id=current_user.parent.id).order_by(SellOrder.id.asc()).all()
    # else:
    #     orders = SellOrder.query.filter_by(user_id=current_user.id).order_by(SellOrder.id.asc()).all()
    return SellOrder.query.filter(SellOrder.user_id==sale_user.id,SellOrder.active==True).order_by(SellOrder.id.asc()).all()


def get_items(order):
    # sale_user = get_parent()
    # orders = get_orders()
    items = []
    # for order in orders:
    for item in order.order_items:
        if item.active:
            items.append(item)
    return items


def get_parent():
    if current_user.role.name == 'User':
        return current_user.parent
    else:
        return current_user

def cancel_shipment(shipment):
    for item in shipment.shipmentitems:
        cancel_shipment_item(item)
    # db.session.commit()
    db.session.delete(shipment)
    db.session.commit()

def cancel_shipment_item(item):
    db.session.delete(item)
    db.session.commit()


def shipment_release(shipment):
    for item in shipment.shipmentitems:
        item.released=not item.released
        db.session.commit()
    shipment.released=not shipment.released
    db.session.commit()