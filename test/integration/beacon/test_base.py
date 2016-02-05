# -*- coding: utf-8 -*-

import datetime

from os import mkdir, rmdir
from shutil import rmtree

from flask import current_app

from beacon.models.opportunities import Category
from beacon.importer.nigp import main as import_nigp

from test.test_base import BaseTestCase
from test.factories import (
    DepartmentFactory, OpportunityTypeFactory, RequiredBidDocumentFactory,
    UserFactory, RoleFactory, OpportunityFactory, VendorFactory,
    AcceptedEmailDomainsFactory
)

class TestOpportunitiesFrontBase(BaseTestCase):
    def setUp(self):
        super(TestOpportunitiesFrontBase, self).setUp()
        import_nigp(current_app.config.get('PROJECT_ROOT') + '/test/mock/nigp.csv')

class TestOpportunitiesAdminBase(BaseTestCase):
    def setUp(self):
        super(TestOpportunitiesAdminBase, self).setUp()
        try:
            mkdir(current_app.config.get('UPLOAD_DESTINATION'))
        except OSError:
            rmtree(current_app.config.get('UPLOAD_DESTINATION'))
            mkdir(current_app.config.get('UPLOAD_DESTINATION'))

        import_nigp(current_app.config.get('PROJECT_ROOT') + '/test/mock/nigp.csv')

        self.department1 = DepartmentFactory(name='test')
        self.opportunity_type = OpportunityTypeFactory.create()

        AcceptedEmailDomainsFactory.create(domain='foo.com')

        self.admin = UserFactory.create(
            email='foo@foo.com', roles=[RoleFactory.create(name='admin')]
        )
        self.staff = UserFactory.create(
            email='foo2@foo.com', roles=[RoleFactory.create(name='staff')]
        )

        self.document = RequiredBidDocumentFactory.create()

        self.vendor = VendorFactory.create(email='foo@foo.com', business_name='foo2')

        self.opportunity1 = OpportunityFactory.create(
            contact=self.admin, created_by=self.staff,
            title=u'tést unïcode title', description=u'tést unïcode déscription',
            is_public=True, is_archived=False, planned_publish=datetime.date.today() + datetime.timedelta(1),
            planned_submission_start=datetime.date.today() + datetime.timedelta(2),
            planned_submission_end=datetime.datetime.today() + datetime.timedelta(2),
            vendor_documents_needed=[self.document.id],
            categories=(Category.query.first(),)
        ).save()
        self.opportunity2 = OpportunityFactory.create(
            contact=self.admin, created_by=self.staff,
            is_public=True, is_archived=False, planned_publish=datetime.date.today(),
            planned_submission_start=datetime.date.today() + datetime.timedelta(2),
            planned_submission_end=datetime.datetime.today() + datetime.timedelta(2),
            categories=(Category.query.first(),), enable_qa=False, qa_start=None,
            qa_end=None
        ).save()
        self.opportunity3 = OpportunityFactory.create(
            contact=self.admin, created_by=self.staff,
            is_public=True, is_archived=False, planned_publish=datetime.date.today() - datetime.timedelta(2),
            planned_submission_start=datetime.date.today() - datetime.timedelta(2),
            planned_submission_end=datetime.datetime.today() - datetime.timedelta(1),
            categories=(Category.query.first(),)
        ).save()
        self.opportunity4 = OpportunityFactory.create(
            contact=self.admin, created_by=self.staff,
            is_public=True, is_archived=False, planned_publish=datetime.date.today() - datetime.timedelta(1),
            planned_submission_start=datetime.date.today(),
            planned_submission_end=datetime.datetime.today() + datetime.timedelta(2),
            title='TEST TITLE!', categories=(Category.query.first(),)
        ).save()

    def tearDown(self):
        super(TestOpportunitiesAdminBase, self).tearDown()
        # clear out the uploads folder
        rmtree(current_app.config.get('UPLOAD_DESTINATION'))
        try:
            rmdir(current_app.config.get('UPLOAD_DESTINATION'))
        except OSError:
            pass
