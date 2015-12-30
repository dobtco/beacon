# -*- coding: utf-8 -*-

from flask import redirect, flash, request

from flask_login import current_user
from functools import wraps

def requires_roles(*roles):
    '''
    Takes in a list of roles and checks whether the user
    has access to those role
    '''
    def check_roles(view_function):
        @wraps(view_function)
        def decorated_function(*args, **kwargs):

            if current_user.is_anonymous():
                flash('This feature is for city staff only. If you are staff, log in with your pittsburghpa.gov email using the link to the upper right.', 'alert-warning')
                return redirect(request.args.get('next') or '/')
            elif current_user.role.name not in roles:
                flash('You do not have sufficent permissions to do that!', 'alert-danger')
                return redirect(request.args.get('next') or '/')
            return view_function(*args, **kwargs)
        return decorated_function
    return check_roles

class AuthMixin(object):
    accepted_roles = ['admin']

    def is_accessible(self):
        if current_user.is_anonymous():
            return False
        if current_user.role.name in self.accepted_roles:
            return True
        return False
