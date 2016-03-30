# -*- coding: utf-8 -*-

import pytz
import datetime

from flask import current_app
from jinja2 import Markup

from beacon.database import Column, Model, db, ReferenceCol
from beacon.utils import localize_today, localize_now

from sqlalchemy.schema import Table
from sqlalchemy.orm import backref
from sqlalchemy.dialects.postgres import ARRAY, JSON

from beacon.notifications import Notification
from beacon.utils import random_id
from beacon.models.vendors import Vendor, Category
from beacon.models.users import User, Role
from beacon.models.questions import Question
from beacon.models.opportunities.documents import RequiredBidDocument, OpportunityDocument

category_opportunity_association_table = Table(
    'category_opportunity_association', Model.metadata,
    Column('category_id', db.Integer, db.ForeignKey('category.id', ondelete='SET NULL'), index=True),
    Column('opportunity_id', db.Integer, db.ForeignKey('opportunity.id', ondelete='SET NULL'), index=True)
)

class Opportunity(Model):
    '''Base Opportunity Model -- the central point for Beacon

    The Beacon model is centered around three dates:
    :py:attr:`~purchasing.models.front.Opportunity.planned_publish`,
    :py:attr:`~purchasing.models.front.Opportunity.planned_submission_start`,
    and :py:attr:`~purchasing.models.front.Opportunity.planned_submission_end`.
    The publish date is when opportunities that are approved appear on Beacon. The
    publication date also is when vendors are notified via email.

    Attributes:
        id: Primary key unique ID
        title: Title of the Opportunity
        description: Short (maximum 500-word) description of the opportunity
        planned_publish: Date when the opportunity should show up on Beacon
        planned_submission_start: Date when vendors can begin submitting
            responses to the opportunity
        planned_submission_end: Deadline for submitted responses to the
            Opportunity
        enable_qa: Flag for whether or not questions/answers are enabled
            for this Opportunity
        qa_start: Start date for accepting questions from vendors
        qa_end: End date for accepting questions from vendors
        vendor_documents_needed: Array of integers that relate to
            :py:class:`~purchasing.models.front.RequiredBidDocument` ids
        is_public: True if opportunity is approved (publicly visible), False otherwise
        is_archived: True if opportunity is archived (not visible), False otherwise
        published_at: Date when an alert email was sent out to relevant vendors
        publish_notification_sent: True is notification sent, False otherwise
        department_id: ID of primary :py:class:`~purchasing.models.users.Department`
            for this opportunity
        department: Sqlalchemy relationship to primary
            :py:class:`~purchasing.models.users.Department`
            for this opportunity
        contact_id: ID of the :py:class:`~purchasing.models.users.User` for this opportunity
        contact: Sqlalchemy relationship to :py:class:`~purchasing.models.users.User`
            for this opportunity
        categories: Many-to-many relationship of the
            :py:class:`~purchasing.models.front.Category` objects
            for this opportunity

        type: Polymorphic mapping identity field for sqlalchemy single
            table inheritance. This is used by the child sqlalchemy types
            to implement different submission and response instruction behavior
        submission_data: JSON field used to handle additional data for
            submissions based on the type of the opportunity


    See Also:
        For more on the Conductor <--> Beacon relationship, look at the
        :py:func:`~purchasing.conductor.handle_form()` Conductor utility method and the
        :py:class:`~purchasing.conductor.forms.PostOpportunityForm` Conductor Form
    '''
    __tablename__ = 'opportunity'

    id = Column(db.Integer, primary_key=True)
    title = Column(db.String(255))
    description = Column(db.Text)

    planned_publish = Column(db.DateTime, nullable=False)
    planned_submission_start = Column(db.DateTime, nullable=False)
    planned_submission_end = Column(db.DateTime, nullable=False)

    enable_qa = Column(db.Boolean, nullable=False, default=True)
    qa_start = Column(db.DateTime)
    qa_end = Column(db.DateTime)

    vendor_documents_needed = Column(ARRAY(db.Integer()))

    is_public = Column(db.Boolean(), default=False)
    is_archived = Column(db.Boolean(), default=False, nullable=False)

    published_at = Column(db.DateTime, nullable=True)
    publish_notification_sent = Column(db.Boolean, default=False, nullable=False)

    department_id = ReferenceCol('department', ondelete='SET NULL', nullable=True)
    department = db.relationship(
        'Department', backref=backref('opportunities', lazy='dynamic')
    )

    contact_id = ReferenceCol('users', ondelete='SET NULL')
    contact = db.relationship(
        'User', backref=backref('opportunities', lazy='dynamic'),
        foreign_keys='Opportunity.contact_id'
    )

    categories = db.relationship(
        'Category',
        secondary=category_opportunity_association_table,
        backref='opportunities',
        collection_class=set
    )

    type = Column(db.String(255))
    submission_data = Column(JSON)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'Opportunity'
    }

    @property
    def accepting_questions(self):
        if self.qa_start is None or self.qa_end is None:
            return False
        return all([
            self.enable_qa,
            datetime.datetime.today() >= self.qa_start,
            datetime.datetime.today() <= self.qa_end
        ])

    @property
    def qa_closed(self):
        if not self.enable_qa:
            return False
        return datetime.datetime.today() > self.qa_end

    @classmethod
    def create(cls, data, user, documents, publish=False):
        '''Create a new opportunity

        Arguments:
            data: dictionary of fields needed to populate new
                opportunity object
            user: :py:class:`~purchasing.models.users.User` object
                creating the new opportunity
            documents: The documents FieldList from the
                :py:class:`~purchasing.forms.front.OpportunityForm`

        Keyword Arguments:
            publish: Boolean as to whether to publish this document. If
                True, it will set ``is_public`` to True.

        See Also:
            The :py:class:`~purchasing.forms.front.OpportunityForm`
            and :py:class:`~purchasing.forms.front.OpportunityDocumentForm`
            have more information about the documents.

        '''
        opportunity = super(Opportunity, cls).create(**data)

        current_app.logger.info(
'''BEACON NEW - New Opportunity Created: Department: {} | Title: {} | Publish Date: {} | Submission Start Date: {} | Submission End Date: {}
            '''.format(
                opportunity.id, opportunity.department.name if opportunity.department else '',
                opportunity.title.encode('ascii', 'ignore'),
                str(opportunity.planned_publish),
                str(opportunity.planned_submission_start), str(opportunity.planned_submission_end)
            )
        )

        if not (user.is_admin() or publish):
            # only send 'your post has been sent/a new post needs review'
            # emails when 1. the submitter isn't from OMB and 2. they are
            # saving a draft as opposed to publishing the opportunity
            opportunity.notify_approvals(user)

        opportunity._handle_uploads(documents)
        opportunity._publish(publish)

        return opportunity

    def raw_update(self, **kwargs):
        '''Performs a basic update based on the passed kwargs.

        Arguments:
            **kwargs: Keyword arguments of fields to be updated in
                the existing Opportunity model
        '''
        super(Opportunity, self).update(**kwargs)

    def update(self, data, user, documents, publish=False):
        '''Performs an update, uploads new documents, and publishes

        Arguments:
            data: dictionary of fields needed to populate new
                opportunity object
            user: :py:class:`~purchasing.models.users.User` object
                updating the opportunity
            documents: The documents FieldList from the
                :py:class:`~purchasing.forms.front.OpportunityForm`

        Keyword Arguments:
            publish: Boolean as to whether to publish this document. If
                True, it will set ``is_public`` to True.
        '''
        data.pop('publish_notification_sent', None)
        for attr, value in data.iteritems():
            setattr(self, attr, value)

        current_app.logger.info(
'''BEACON Update - Opportunity Updated: ID: {} | Title: {} | Publish Date: {} | Submission Start Date: {} | Submission End Date: {}
            '''.format(
                self.id, self.title.encode('ascii', 'ignore'), str(self.planned_publish),
                str(self.planned_submission_start), str(self.planned_submission_end)
            )
        )

        self._handle_uploads(documents)
        self._publish(publish)

    @classmethod
    def get_opp_class(cls, form_type):
        from beacon.models.opportunities import types
        return getattr(types, form_type, cls)

    @classmethod
    def get_types(cls):
        from beacon.models.opportunities import types
        return [
            i.get_opportunity_type() for i in cls.__subclasses__()
        ]

    @classmethod
    def get_help_blocks(cls):
        from beacon.models.opportunities import types
        help_block = {}
        for i in Opportunity.__subclasses__():
            help_block.update(i.get_help_block())
        return help_block

    @classmethod
    def get_opportunity_type(cls):
        '''
        Returns:
            Two-tuple of (type, label) to be used for rendering
            and selecting different opportunity types
        '''
        raise NotImplementedError

    @classmethod
    def get_help_block(cls):
        raise NotImplementedError

    @property
    def is_published(self):
        '''Determine if an opportunity can be displayed

        Returns:
            True if the planned publish date is before or on today,
            and the opportunity is approved, False otherwise
        '''
        return self.coerce_to_date(self.planned_publish) <= localize_today() and self.is_public

    @property
    def is_upcoming(self):
        '''Determine if an opportunity is upcoming

        Returns:
            True if the planned publish date is before or on today, is approved,
            is not accepting submissions, and is not closed; False otherwise
        '''
        return self.coerce_to_date(self.planned_publish) <= localize_today() and \
            not self.is_submission_start and not self.is_submission_end and self.is_public

    @property
    def is_submission_start(self):
        '''Determine if the oppportunity is accepting submissions

        Returns:
            True if the submission start date and planned publish date are
            before or on today, is approved, and the opportunity is not closed;
            False otherwise
        '''
        return self.coerce_to_date(self.planned_submission_start) <= localize_today() and \
            self.coerce_to_date(self.planned_publish) <= localize_today() and \
            not self.is_submission_end and self.is_public

    @property
    def is_submission_end(self):
        '''Determine if an opportunity is closed to new submissions

        Returns:
            True if the submission end date is on or before today,
            and it is approved
        '''
        return pytz.UTC.localize(self.planned_submission_end).astimezone(
            current_app.config['DISPLAY_TIMEZONE']
        ) <= localize_now() and \
            self.is_public

    @property
    def has_docs(self):
        '''True if the opportunity has at least one document, False otherwise
        '''
        return self.opportunity_documents.count() > 0

    def estimate_submission_start(self):
        '''Returns the month/year based on submission start date
        '''
        return self.planned_submission_start.strftime('%B %d, %Y')

    def estimate_submission_end(self):
        '''Returns the localized date and time based on submission end date
        '''
        return pytz.UTC.localize(self.planned_submission_end).astimezone(
            current_app.config['DISPLAY_TIMEZONE']
        ).strftime('%B %d, %Y at %I:%M%p %Z')

    def can_view(self, user):
        '''Check if a user can see opportunity detail

        Arguments:
            user: A :py:class:`~purchasing.models.users.User` object

        Returns:
            Boolean indiciating if the user can view this opportunity
        '''
        return False if user.is_anonymous and not self.is_published else True

    def can_edit(self, user):
        '''Check if a user can edit the contract

        Arguments:
            user: A :py:class:`~purchasing.models.users.User` object

        Returns:
            Boolean indiciating if the user can edit this opportunity.
            Conductors, the opportunity creator, and the primary opportunity
            contact can all edit the opportunity before it is published. After
            it is published, only conductors can edit it.
        '''
        if self.is_public and user.is_approver():
            return True
        elif not self.is_public and \
            (user.is_approver() or
                user.id in (self.created_by_id, self.contact_id)):
                return True
        return False

    def coerce_to_date(self, field):
        '''Coerces the input field to a datetime.date object

        Arguments:
            field: A datetime.datetime or datetime.date object

        Returns:
            A datetime.date object
        '''
        if isinstance(field, datetime.datetime):
            return field.date()
        if isinstance(field, datetime.date):
            return field
        return field

    def get_vendor_emails(self):
        '''Return list of all signed up vendors
        '''
        return [i.email for i in self.vendors]

    def has_vendor_documents(self):
        '''Returns a Boolean for whether there are required bid documents

        See Also:
            :py:class:`~purchasing.models.front.RequiredBidDocument`
        '''
        return self.vendor_documents_needed and len(self.vendor_documents_needed) > 0

    def get_vendor_documents(self):
        '''Returns a list of documents the the vendor will need to provide

        See Also:
            :py:class:`~purchasing.models.front.RequiredBidDocument`
        '''
        if self.has_vendor_documents():
            return RequiredBidDocument.query.filter(
                RequiredBidDocument.id.in_(self.vendor_documents_needed)
            ).all()
        return []

    def get_events(self):
        '''Returns the opportunity dates out as a nice ordered list for rendering
        '''
        return [
            {
                'event': 'bid_submission_start', 'classes': 'event event-submission_start',
                'date': self.estimate_submission_start(),
                'description': 'Opportunity opens for submissions.'
            },
            {
                'event': 'bid_submission_end', 'classes': 'event event-submission_end',
                'date': self.estimate_submission_end(),
                'description': 'Deadline to submit proposals.'
            }
        ]

    def _handle_uploads(self, documents):
        opp_documents = self.opportunity_documents.all()

        for document in documents.entries:
            if document.title.data == '':
                continue

            _id = self.id if self.id else random_id(6)

            _file = document.document.data
            if _file.filename in [i.name for i in opp_documents]:
                continue

            filename, filepath = document.upload_document(_id)
            if filepath:
                self.opportunity_documents.append(OpportunityDocument(
                    name=document.title.data, href=filepath
                ))

    def _publish(self, publish):
        if not self.is_public:
            if publish:
                self.is_public = True

    def _notify_user(self, user):
        return Notification(
            to_email=[user.email],
            subject='Your post has been sent to OMB for approval',
            html_template='beacon/emails/staff_postsubmitted.html',
            opportunity=self
        ).send(multi=True)

    def _notify_admins(self):
        return Notification(
            to_email=db.session.query(User.email).filter(
                User.roles.any(Role.name.in_(['conductor', 'admin', 'superadmin']))
            ).all(),
            subject='A new Beacon post needs review',
            html_template='beacon/emails/admin_postforapproval.html',
            opportunity=self
        ).send(multi=True)

    def notify_approvals(self, user):
        '''Send the approval notifications to everyone with approval rights

        Arguments:
            user: A :py:class:`~purchasing.models.users.User` object
        '''
        self._notify_user(user)
        # re-add the opportunity to the session -- it's popped by
        # the celery task
        db.session.add(self)
        self._notify_admins()
        return True

    def get_category_ids(self):
        '''Returns the IDs from the Opportunity's related categories
        '''
        return [i.id for i in self.categories]

    def send_publish_email(self):
        '''Sends the "new opportunity available" email to subscribed vendors

        If a new Opportunity is created and it has a publish date before or
        on today's date, it will trigger an immediate publish email send. This
        operates in a very similar way to the nightly
        :py:class:`~purchasing.jobs.beacon_nightly.BeaconNewOppotunityOpenJob`.
        It will build a list of all vendors signed up to the Opportunity
        or to any of the categories that describe the Opportunity.
        '''
        if self.is_published and not self.publish_notification_sent:
            vendors = db.session.query(Vendor).filter(
                Vendor.categories.any(Category.id.in_(self.get_category_ids()))
            ).all()

            Notification(
                to_email=[i.email for i in vendors],
                subject='A new opportunity from Beacon!',
                html_template='beacon/emails/newopp.html',
                opportunity=self
            ).send(multi=True)

            self.publish_notification_sent = True
            self.published_at = datetime.datetime.utcnow()

            current_app.logger.info(
'''BEACON PUBLISHED:  ID: {} | Title: {} | Publish Date: {} | Submission Start Date: {} | Submission End Date: {}
                '''.format(
                    self.id, self.title.encode('ascii', 'ignore'), str(self.planned_publish),
                    str(self.planned_submission_start), str(self.planned_submission_end)
                )
            )
            return self
        return self

    def get_answered_questions(self):
        return Question.query.filter(
            Question.opportunity_id == self.id,
            Question.answer_text != None
        ).all()

    @classmethod
    def validate(self, form):
        raise NotImplementedError

    @classmethod
    def serialize_submission_data(self, submission_data):
        raise NotImplementedError

    def deserialize_submission_data(self):
        return None

    def render_instructions(self):
        '''Render submission instructions to a vendor
        '''
        return Markup(
            '<p>Please refer to the opportunity document for more information.</p>'
        )

    def submissions_page_exists(self):
        '''Returns a boolean for whether or not a submissions page exists
        '''
        return False

    def render_submissions_html(self):
        '''Render submission page for individual vendor
        '''
        raise NotImplementedError

    def submissions_nav_url(self):
        '''Render submissions link in navbar
        '''
        raise NotImplementedError
