# -*- coding: utf-8 -*-

import datetime

import factory
from factory.alchemy import SQLAlchemyModelFactory

from beacon.database import db
from beacon.models.users import User, Role, Department
from beacon.models.public import AcceptedEmailDomains

from beacon.models.opportunities.types import NoSubmissionOpportunity
from beacon.models.opportunities.documents import (
    OpportunityDocument, RequiredBidDocument
)
from beacon.models.vendors import Category, Vendor

from beacon.models.questions import Question
from beacon.jobs.job_base import JobStatus

class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = db.session

class RoleFactory(BaseFactory):
    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: '{}'.format(n))
    description = factory.Sequence(lambda n: 'description - {}'.format(n))

    class Meta:
        model = Role

class DepartmentFactory(BaseFactory):
    id = factory.Sequence(lambda n: n)
    name = factory.Sequence(lambda n: 'department{}'.format(n))

    class Meta:
        model = Department

class UserFactory(BaseFactory):
    id = factory.Sequence(lambda n: n + 100)
    email = factory.Sequence(lambda n: '{}@foo.com'.format(n))
    created_at = factory.Sequence(lambda n: datetime.datetime.now())
    first_name = factory.Sequence(lambda n: '{}'.format(n))
    last_name = factory.Sequence(lambda n: '{}'.format(n))
    department = factory.SubFactory(DepartmentFactory)
    active = factory.Sequence(lambda n: True)
    confirmed_at = factory.Sequence(lambda n: datetime.datetime.now())
    password = 'password'

    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        if extracted:
            for role in extracted:
                self.roles.append(role)

    class Meta:
        model = User

class CategoryFactory(BaseFactory):
    id = factory.Sequence(lambda n: n)
    category_friendly_name = 'i am friendly!'

    class Meta:
        model = Category

class OpportunityFactory(BaseFactory):
    id = factory.Sequence(lambda n: n + 100)
    department = factory.SubFactory(DepartmentFactory)
    created_by = factory.SubFactory(UserFactory)
    contact = factory.SubFactory(UserFactory)
    vendor_documents_needed = []
    title = 'Default'
    enable_qa = True
    qa_start = datetime.datetime.today() - datetime.timedelta(days=1)
    qa_end = datetime.datetime.today() + datetime.timedelta(days=5)
    type = 'NoSubmissionOpportunity'

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for category in extracted:
                self.categories.add(category)

    class Meta:
        model = NoSubmissionOpportunity

class VendorFactory(BaseFactory):
    id = factory.Sequence(lambda n: n + 100)
    email = factory.Sequence(lambda n: '{}@foo.com'.format(n))
    business_name = factory.Sequence(lambda n: '{}'.format(n))

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for category in extracted:
                self.categories.add(category)

    class Meta:
        model = Vendor

class QuestionFactory(BaseFactory):
    id = factory.Sequence(lambda n: n + 100)
    question_text = 'i am a question'
    asked_by = factory.SubFactory(VendorFactory)
    opportunity = factory.SubFactory(OpportunityFactory)

    class Meta:
        model = Question

class RequiredBidDocumentFactory(BaseFactory):
    id = factory.Sequence(lambda n: n + 100)
    display_name = 'name'
    description = 'description'

    class Meta:
        model = RequiredBidDocument

class OpportunityDocumentFactory(BaseFactory):
    class Meta:
        model = OpportunityDocument

class JobStatusFactory(BaseFactory):
    class Meta:
        model = JobStatus

class AcceptedEmailDomainsFactory(BaseFactory):
    class Meta:
        model = AcceptedEmailDomains
