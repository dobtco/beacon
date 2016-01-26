# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located
in app.py
"""

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from flask_security import Security, current_user
security = Security()

from flask_migrate import Migrate
migrate = Migrate()

from flask_cache import Cache
cache = Cache()

from flask_debugtoolbar import DebugToolbarExtension
debug_toolbar = DebugToolbarExtension()

from flask_s3 import FlaskS3
s3 = FlaskS3()

from flask_mail import Mail
mail = Mail()

from flask_admin import Admin, AdminIndexView, expose
class AuthMixin(object):
    accepted_roles = ['admin']

    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        if current_user.role.name in self.accepted_roles:
            return True
        return False

class PermissionsBase(AuthMixin, AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

admin = Admin(endpoint='admin', index_view=PermissionsBase(), template_mode='bootstrap3')
