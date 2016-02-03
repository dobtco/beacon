# -*- coding: utf-8 -*-

from beacon.database import Column, Model, db

from sqlalchemy.schema import Table
from sqlalchemy.dialects.postgres import ARRAY
from sqlalchemy.dialects.postgresql import TSVECTOR

from beacon.utils import build_downloadable_groups

category_vendor_association_table = Table(
    'category_vendor_association', Model.metadata,
    Column('category_id', db.Integer, db.ForeignKey('category.id', ondelete='SET NULL'), index=True),
    Column('vendor_id', db.Integer, db.ForeignKey('vendor.id', ondelete='SET NULL'), index=True)
)

opportunity_vendor_association_table = Table(
    'opportunity_vendor_association_table', Model.metadata,
    Column('opportunity_id', db.Integer, db.ForeignKey('opportunity.id', ondelete='SET NULL'), index=True),
    Column('vendor_id', db.Integer, db.ForeignKey('vendor.id', ondelete='SET NULL'), index=True)
)

class Category(Model):
    '''Category model for opportunities and Vendor signups

    Categories are based on the codes created by the `National Institute
    of Government Purchasing (NIGP) <http://www.nigp.org/eweb/StartPage.aspx>`_.
    The names of the categories have been re-written a bit to make them more
    human-readable and in some cases a bit more modern.

    Attributes:
        id: Primary key unique ID
        nigp_codes: Array of integers refering to NIGP codes.
        category: parent top-level category
        subcategory: NIGP designated subcategory name
        category_friendly_name: Rewritten, more human-readable subcategory name
        examples: Pipe-delimited examples of items that fall in each subcategory
        examples_tsv: TSVECTOR of the examples for that subcategory

    See Also:
        The :ref:`nigp-importer` contains more information about how NIGP codes
        are imported into the system.
    '''
    __tablename__ = 'category'

    id = Column(db.Integer, primary_key=True, index=True)
    nigp_codes = Column(ARRAY(db.Integer()))
    category = Column(db.String(255))
    subcategory = Column(db.String(255))
    category_friendly_name = Column(db.Text)
    examples = Column(db.Text)
    examples_tsv = Column(TSVECTOR)

    def __unicode__(self):
        return '{sub} (in {main})'.format(sub=self.category_friendly_name, main=self.category)

    @classmethod
    def parent_category_query_factory(cls):
        '''Query factory to return a query of all of the distinct top-level categories
        '''
        return db.session.query(db.distinct(cls.category).label('category')).order_by('category')

    @classmethod
    def query_factory(cls):
        '''Query factory that returns all category/subcategory pairs
        '''
        return cls.query

class Vendor(Model):
    '''Base Vendor model for businesses interested in Beacon

    The primary driving thought behind Beacon is that it should be as
    easy as possible to sign up to receive updates about new front.
    Therefore, there are no Vendor accounts or anything like that, just
    email addresses and business names.

    Attributes:
        id: Primary key unique ID
        business_name: Name of the business, required
        email: Email address for the vendor, required
        first_name: First name of the vendor
        last_name: Last name of the vendor
        phone_number: Phone number for the vendor
        fax_number: Fax number for the vendor
        minority_owned: Whether the vendor is minority owned
        veteran_owned: Whether the vendor is veteran owned
        woman_owned: Whether the vendor is woman owned
        disadvantaged_owned: Whether the vendor is any class
            of Disadvantaged Business Enterprise (DBE)
        categories: Many-to-many relationship with
            :py:class:`~purchasing.models.front.Category`;
            describes what the vendor is subscribed to
        opportunities: Many-to-many relationship with
            :py:class:`~purchasing.models.front.Opportunity`;
            describes what opportunities the vendor is subscribed to
        subscribed_to_newsletter: Whether the vendor is subscribed to
            receive the biweekly newsletter of all opportunities
    '''
    __tablename__ = 'vendor'

    id = Column(db.Integer, primary_key=True, index=True)
    business_name = Column(db.String(255), nullable=False)
    email = Column(db.String(80), unique=True, nullable=False)
    first_name = Column(db.String(30), nullable=True)
    last_name = Column(db.String(30), nullable=True)
    phone_number = Column(db.String(20))
    fax_number = Column(db.String(20))
    minority_owned = Column(db.Boolean())
    veteran_owned = Column(db.Boolean())
    woman_owned = Column(db.Boolean())
    disadvantaged_owned = Column(db.Boolean())
    categories = db.relationship(
        'Category',
        secondary=category_vendor_association_table,
        backref='vendors',
        collection_class=set
    )
    opportunities = db.relationship(
        'Opportunity',
        secondary=opportunity_vendor_association_table,
        backref='vendors',
        collection_class=set
    )

    subscribed_to_newsletter = Column(db.Boolean(), default=False, nullable=False)

    @classmethod
    def newsletter_subscribers(cls):
        '''Query to return all vendors signed up to the newsletter
        '''
        return cls.query.filter(cls.subscribed_to_newsletter == True).all()

    def build_downloadable_row(self):
        '''Take a Vendor object and build a list for a .tsv download

        Returns:
            List of all vendor fields in order for a bulk vendor download
        '''
        return [
            self.first_name, self.last_name, self.business_name,
            self.email, self.phone_number, self.minority_owned,
            self.woman_owned, self.veteran_owned, self.disadvantaged_owned,
            build_downloadable_groups('category_friendly_name', self.categories),
            build_downloadable_groups('title', self.opportunities)
        ]

    def __unicode__(self):
        return self.email
