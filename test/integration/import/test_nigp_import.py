# -*- coding: utf-8 -*-

from flask import current_app
from test.test_base import BaseTestCase

from beacon.importer.nigp import main
from beacon.models.vendors import Category

class TestNigpImport(BaseTestCase):
    def test_nigp_import(self):
        main(current_app.config.get('PROJECT_ROOT') + '/test/mock/nigp.csv')

        categories = Category.query.all()

        self.assertEquals(len(categories), 5)
