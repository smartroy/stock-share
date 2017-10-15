import os
from app import create_app, db, mongo
from app.models import User, Role, Post, Stock, StockItem, SellOrder, Customer#, SellOrderItem
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
import app.main.util as ut

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, mongo=mongo, User=User, Role=Role, Post=Post, Stock=Stock, StockItem=StockItem, SellOrder=SellOrder, Customer=Customer, ut=ut)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

if __name__ == '__main__':
    manager.run()