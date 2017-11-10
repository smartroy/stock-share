import os
from app import create_app, db, mongo
from app.models import User, Role, Post, Stock, StockItem, SellOrder, Customer, OrderItem#, SellOrderItem
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
import app.main.util as ut

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, mongo=mongo, User=User, Role=Role, Post=Post, Stock=Stock, StockItem=StockItem, SellOrder=SellOrder, Customer=Customer, ut=ut, OrderItem=OrderItem)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def deploy():
    import app.main.util as ut
    from flask_migrate import upgrade,init,migrate
    init()
    migrate()
    upgrade()
    ut.db_init()



@manager.command
def deploy_mongo():
    ut.insert_product_mongo('product-list.csv')

if __name__ == '__main__':
    manager.run()