from flask import Blueprint

main = Blueprint('main',__name__)

from . import views, errors, views_stock, views_order, views_scan, views_product

from ..models import Permission

@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
