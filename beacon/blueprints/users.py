# -*- coding: utf-8 -*-

from flask import (
    render_template, request, flash,
    current_app, url_for, redirect,
    Blueprint
)

from flask_security import current_user, login_required

from beacon.database import db
from beacon.forms.users import DepartmentForm

blueprint = Blueprint(
    'users', __name__, url_prefix='/users',
    template_folder='../templates'
)

@blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    '''View to update user model with data passed through form after validation
    '''
    form = DepartmentForm(obj=current_user)

    if form.validate_on_submit():
        user = current_user
        data = request.form

        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        user.department_id = int(data.get('department'))
        db.session.commit()

        flash('Updated your profile!', 'alert-success')
        data = data.to_dict().pop('csrf_token', None)
        current_app.logger.debug('PROFILE UPDATE: Updated profile for {email} with {data}'.format(
            email=user.email, data=data
        ))

        return redirect(url_for('users.profile'))

    return render_template('users/profile.html', form=form, user=current_user)
