# -*- coding: utf-8 -*-

from flask import flash, redirect, url_for
from sqlalchemy.orm.exc import NoResultFound

from flask_wtf import Form
from wtforms import fields
from wtforms.validators import DataRequired, Email

from beacon.database import db
from beacon.notifications import Notification
from beacon.models.vendors import Vendor
from beacon.models.questions import Question

class QuestionForm(Form):
    question = fields.TextAreaField('Your question', validators=[DataRequired()])
    email = fields.TextField(
        'Your email', validators=[DataRequired(), Email()]
    )
    business_name = fields.TextField(
        "What's the name of your business?", validators=[DataRequired()]
    )
    submit = fields.SubmitField()

    def post_validate_action(self, opportunity):
        try:
            vendor = Vendor.query.filter(
                Vendor.email == self.email.data
            ).one()
            vendor.update(business_name=self.business_name.data)
        except NoResultFound:
            vendor = Vendor.create(
                email=self.email.data,
                business_name=self.business_name.data
            ).save()

        question = Question.create(
            question_text=self.question.data,
            asked_by_id=vendor.id,
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
