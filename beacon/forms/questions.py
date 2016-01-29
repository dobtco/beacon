# -*- coding: utf-8 -*-

from flask import flash, redirect, url_for

from flask_wtf import Form
from wtforms import fields
from wtforms.validators import DataRequired, Email

from beacon.database import db
from beacon.notifications import Notification
from beacon.forms.validators import registered_vendor_email
from beacon.models.opportunities import Vendor
from beacon.models.questions import Question

class QuestionForm(Form):
    question = fields.TextAreaField('Your question', validators=[DataRequired()])
    email = fields.TextField(
        'Your email', validators=[DataRequired(), Email(), registered_vendor_email]
    )
    submit = fields.SubmitField()

    def post_validate_action(self, opportunity):
        question = Question.create(
            question_text=self.question.data,
            asked_by_id=Vendor.query.filter(
                Vendor.email == self.email.data).one().id,
            opportunity_id=opportunity.id
        )
        db.session.commit()

        Notification(
            to_email=[opportunity.created_by.email, opportunity.contact.email],
            subject='New question on Beacon',
            html_template='beacon/emails/new_question.html',
            txt_template='beacon/emails/new_question.txt',
            question=question
        ).send(multi=True)

        flash('''
            Thank you! Your question has been submitted
            and will be reviewed by City Staff. You'll
            be notified once an answer has been posted.
        ''')

        return redirect(
            url_for('front.detail', opportunity_id=opportunity.id)
        )

class AnswerForm(Form):
    answer_text = fields.TextAreaField('Answer', validators=[DataRequired()])
    submit = fields.SubmitField('Save answer')
