# -*- coding: utf-8 -*-

from beacon.extensions import login_manager, admin, db
from beacon.models.users import User, Role, Department

from beacon.decorators import AuthMixin

from beacon.models.opportunities import RequiredBidDocument

from flask_admin.contrib import sqla


GLOBAL_EXCLUDE = [
    'created_at', 'updated_at', 'created_by', 'updated_by'
]


@login_manager.user_loader
def load_user(userid):
    return User.get_by_id(int(userid))

class BaseModelViewAdmin(sqla.ModelView):
    form_excluded_columns = GLOBAL_EXCLUDE
    column_exclude_list = GLOBAL_EXCLUDE

class DocumentAdmin(AuthMixin, BaseModelViewAdmin):
    pass

admin.add_view(DocumentAdmin(
    RequiredBidDocument, db.session, name='Bid Document', endpoint='bid_document', category='Beacon'
))

