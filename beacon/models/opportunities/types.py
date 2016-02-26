# -*- coding: utf-8 -*-

from flask import url_for
from jinja2 import Markup
from wtforms.validators import Email, DataRequired

from beacon.forms.validators import city_domain_email
from beacon.models.opportunities.base import Opportunity

class EmailOpportunity(Opportunity):
    __mapper_args__ = {
        'polymorphic_identity': 'EmailOpportunity'
    }

    @classmethod
    def get_opportunity_type(cls):
        return ('EmailOpportunity', 'Submit responses via email address')

    @classmethod
    def get_help_block(cls):
        return {
            cls.__name__:
            'Please put the submission email address below.'
        }

    @classmethod
    def validate(self, form):
        return form.submission_data.validate(
            form, extra_validators=[DataRequired(), Email(), city_domain_email]
        )

    @classmethod
    def serialize_submission_data(self, submission_data):
        return {
            'email': submission_data
        }

    def deserialize_submission_data(self):
        return self.submission_data['email']

    def render_instructions(self):
        '''Render submission instructions to a vendor
        '''
        return Markup(
            '''<p>To submit a propsal for this opportunity,
            please email <a href="mailto:{0}">{0}</a>.
            </p>'''.format(self.submission_data['email'])
        )

    def submissions_page_exists(self):
        '''Returns a boolean for whether or not a submissions page exists
        '''
        return False

class ScreendoorOpportunity(Opportunity):
    __mapper_args__ = {
        'polymorphic_identity': 'ScreendoorOpportunity'
    }

    @classmethod
    def get_opportunity_type(cls):
        return (cls.__name__, 'Submit responses via screendoor')

    @classmethod
    def get_help_block(cls):
        return {
            cls.__name__:
            'Create a new project on Screendoor and copy the project ID below.'
        }

    @classmethod
    def validate(self, form):
        return form.submission_data.validate(
            form, extra_validators=[DataRequired()]
        )

    @classmethod
    def serialize_submission_data(self, submission_data):
        return {
            'embed_token': submission_data
        }

    def deserialize_submission_data(self):
        return self.submission_data['embed_token']

    def render_instructions(self):
        '''Render submission instructions to a vendor
        '''
        return Markup(
            '''<p>To submit a propsal for this opportunity,
            please visit the <a href="{}">submissions page</a>.
            </p>'''.format(
                url_for('front.new_proposal', opportunity_id=self.id)
            )
        )

    def submissions_page_exists(self):
        '''Returns a boolean for whether or not a submissions page exists
        '''
        return True

    def render_submissions_html(self):
        '''Render submission page for individual vendor
        '''
        return Markup(
            '''
    <form data-formrenderer>This form requires JavaScript to complete.</form>
    <script>
      new FormRenderer({{"project_id": "{}"}});
    </script>
            '''.format(self.submission_data['embed_token'])
        )

    def submissions_nav_url(self):
        return ('https://screendoor.dobt.co/projects/' +
                self.submission_data['embed_token'] +
                '/admin')
