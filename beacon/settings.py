# -*- coding: utf-8 -*-
import os
import pytz

HERE = os.path.abspath(os.path.dirname(__file__))
os_env = os.environ
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir))

class Config(object):
    SECRET_KEY = os_env.get('BEACON_SECRET', 'secret-key')  # TODO: Change me
    APP_DIR = HERE
    ASSETS_DEBUG = False
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    PROJECT_ROOT = PROJECT_ROOT
    CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
    BROWSERID_URL = os_env.get('BROWSERID_URL')
    PER_PAGE = 50
    MAIL_DEFAULT_SENDER = os_env.get('MAIL_DEFAULT_SENDER', 'no-reply@buildpgh.com')
    BEACON_SENDER = os_env.get('BEACON_SENDER', 'beaconbot@buildpgh.com')
    MAIL_USERNAME = os_env.get('MAIL_USERNAME')
    MAIL_PASSWORD = os_env.get('MAIL_PASSWORD')
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    UPLOAD_S3 = True
    UPLOAD_DESTINATION = 'beacon-opportunities'
    MAX_CONTENT_LENGTH = int(os_env.get('MAX_CONTENT_LENGTH', 2 * 1024 * 1024))  # max file size, default 2mb
    UPLOAD_FOLDER = os.path.join(HERE, os_env.get('UPLOAD_FOLDER', 'uploads/'))
    S3_BUCKET_NAME = os_env.get('S3_BUCKET_NAME')
    AWS_ACCESS_KEY_ID = os_env.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os_env.get('AWS_SECRET_ACCESS_KEY')
    CELERY_IMPORTS = ("beacon.tasks",)
    BROKER_POOL_LIMIT = None
    SERVER_NAME = os_env.get('BROWSERID_URL')
    DISPLAY_TIMEZONE = pytz.timezone(os_env.get('DISPLAY_TIMEZONE', 'US/Eastern'))
    EXTERNAL_LINK_WARNING = os_env.get('EXTERNAL_LINK_WARNING', None)
    SECURITY_EMAIL_SENDER = MAIL_DEFAULT_SENDER
    SECURITY_CONFIRMABLE = True
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_CHANGEABLE = True
    SECURITY_TOKEN_MAX_AGE = 60 * 60 * 24 * 30
    # more of a namespacing than a traditional salt, see
    # http://pythonhosted.org/itsdangerous/#the-salt
    # for more information
    SECURITY_PASSWORD_SALT = os_env.get('SECURITY_PASSWORD_SALT', 'salty')

class ProdConfig(Config):
    """Production configuration."""
    ENV = 'prod'
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os_env.get('DATABASE_URL', 'postgresql://localhost/beacon')  # TODO: Change me
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    USE_S3 = True
    S3_USE_HTTPS = True
    FLASK_ASSETS_USE_S3 = True
    UGLIFYJS_EXTRA_ARGS = ['-m']
    MAIL_SERVER = 'smtp.sendgrid.net'
    MAIL_MAX_EMAILS = 100
    CELERY_BROKER_URL = os_env.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os_env.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os_env.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 30
    SECURITY_PASSWORD_HASH = 'bcrypt'

class DevConfig(Config):
    """Development configuration."""
    ENV = 'dev'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os_env.get('DATABASE_URL', 'postgresql://localhost/beacon')  # TODO: Change me
    SQLALCHEMY_ECHO = os_env.get('SQLALCHEMY_ECHO', False)
    DEBUG_TB_ENABLED = True
    BROWSERID_URL = os_env.get('BROWSERID_URL', 'http://127.0.0.1:9000')
    MAIL_SERVER = 'smtp.gmail.com'  # Use gmail in dev: https://support.google.com/mail/answer/1173270?hl=en
    ASSETS_DEBUG = True
    UPLOAD_S3 = False
    UPLOAD_DESTINATION = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'uploads'))
    # MAIL_SUPPRESS_SEND = False
    # CELERY_BROKER_URL = os_env.get('REDIS_URL', 'redis://localhost:6379/0')
    # CELERY_RESULT_BACKEND = os_env.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_ALWAYS_EAGER = True
    UGLIFYJS_BIN = os.path.join(PROJECT_ROOT, 'node_modules', '.bin', 'uglifyjs')
    LESS_BIN = os.path.join(PROJECT_ROOT, 'node_modules', '.bin', 'lessc')
    MAIL_SUPPRESS_SEND = True
    SECURITY_PASSWORD_HASH = 'bcrypt'

class TestConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os_env.get('DATABASE_URL', 'postgresql://localhost/beacon_test')
    WTF_CSRF_ENABLED = False  # Allows form testing
    BROWSERID_URL = 'test'
    ASSETS_DEBUG = True
    MAIL_SUPPRESS_SEND = True
    UPLOAD_S3 = False
    UPLOAD_DESTINATION = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'test_uploads'))
    UPLOAD_FOLDER = UPLOAD_DESTINATION
    CELERY_ALWAYS_EAGER = True
    DISPLAY_TIMEZONE = pytz.timezone('UTC')
    SECURITY_PASSWORD_SALT = 'test'
