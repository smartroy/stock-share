import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'xSkAJJ2170A@@l4824'
    SQLALCHEMY_COMMIT_ON_TEARDOWN =  True
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky admin <xushikang1127@gmail.com>'
    FLASKY_ADMIN = 'xushikang1127@gmail.com'
    # AWS_S3_BUCKET = 'psy-axwave'
    # AWS_ACCESS_KEY_ID = 'AKIAI2EWQBXIXGHZH3OQ'
    # AWS_SECRET_ACCESS_KEY = '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'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.sendgrid.net'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'app80708088@heroku.com'
    MAIL_PASSWORD = 'efq5vskg8381'
    SQLALCHEMY_DATABASE_URI =os.environ.get('DATABASE_URL') or 'postgresql://stockshare:stockshare@localhost/devdb'
    #os.environ.get('DEV_DATABASE_URL') or \
                              #'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    MONGO_DBNAME = 'testmongo'
    MONGO_URI = 'mongodb://localhost:27017/testmongo'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data.sqlite')


class HerokuConfig(Config):
    # DEBUG = True
    MAIL_SERVER = 'smtp.sendgrid.net'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('SENDGRID_USERNAME')
    MAIL_PASSWORD = os.environ.get('SENDGRID_PASSWORD')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://stockshare:stockshare@localhost/devdb'
    MONGO_DBNAME = 'testmongo'
    MONGO_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/testmongo'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
    'heroku': HerokuConfig
}
