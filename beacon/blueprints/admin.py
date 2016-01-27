# -*- coding: utf-8 -*-

from beacon.extensions import admin, db, AuthMixin

from beacon.models.opportunities import RequiredBidDocument
from beacon.models.users import User, Department
from beacon.models.public import AcceptedEmailDomains

from flask_admin.contrib import sqla

GLOBAL_EXCLUDE = [
    'created_at', 'updated_at', 'created_by', 'updated_by', 'password'
]

class BaseModelViewAdmin(sqla.ModelView):
    form_excluded_columns = GLOBAL_EXCLUDE
    column_exclude_list = GLOBAL_EXCLUDE

class DocumentAdmin(AuthMixin, BaseModelViewAdmin):
    pass

class DepartmentAdmin(AuthMixin, BaseModelViewAdmin):
    form_excluded_columns = GLOBAL_EXCLUDE + ['users', 'opportunities']

class UserAdmin(AuthMixin, BaseModelViewAdmin):
    form_columns = ['email', 'first_name', 'last_name', 'department', 'roles']
    column_exclude_list = GLOBAL_EXCLUDE + [
        'last_login_at', 'current_login_at',
        'last_login_ip', 'current_login_ip', 'login_count']

    form_extra_fields = {
        'department': sqla.fields.QuerySelectField(
            'Department', query_factory=Department.query_factory,
            allow_blank=True, blank_text='-----'
        ),
    }

class AcceptedEmailDomainsAdmin(AuthMixin, BaseModelViewAdmin):
    pass

admin.add_view(DocumentAdmin(
    RequiredBidDocument, db.session, name='Bid Document', endpoint='bid-document'
))

admin.add_view(UserAdmin(
    User, db.session, name='User', endpoint='user', category='Users'
))
admin.add_view(DocumentAdmin(
    Department, db.session, name='Department', endpoint='department', category='Users'
))
admin.add_view(AcceptedEmailDomainsAdmin(
    AcceptedEmailDomains, db.session, name='Accepted Domains',
    endpoint='accepted-email-domain', category='Users'
))
