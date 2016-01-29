# -*- coding: utf-8 -*-

from sqlalchemy.orm import backref
from beacon.database import db, Column, Model, ReferenceCol

class Question(Model):
    __tablename__ = 'question'

    id = Column(db.Integer, primary_key=True, index=True)
    question_text = Column(db.Text, nullable=False)

    opportunity = db.relationship(
        'Opportunity', backref=backref('questions', lazy='dynamic')
    )
    opportunity_id = ReferenceCol('opportunity', ondelete='CASCADE', nullable=False)

    asked_by = db.relationship(
        'Vendor', backref=backref('questions', lazy='dynamic')
    )
    asked_by_id = ReferenceCol('vendor', ondelete='SET NULL', nullable=True)
    asked_at = Column(db.DateTime, default=db.func.now())

    answer_text = Column(db.Text)
    answered_by = db.relationship(
        'User', backref=backref('answers', lazy='dynamic'),
        foreign_keys='Question.answered_by_id'
    )
    answered_by_id = ReferenceCol('users', ondelete='SET NULL', nullable=True)
    answered_at = Column(db.DateTime)

    edited = Column(db.Boolean())
    edited_at = Column(db.DateTime)
