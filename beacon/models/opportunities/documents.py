# -*- coding: utf-8 -*-

from flask import current_app

from beacon.database import Column, Model, db, ReferenceCol

from sqlalchemy.orm import backref

class OpportunityDocument(Model):
    '''Model for bid documents associated with opportunities

    Attributes:
        id: Primary key unique ID
        opportunity_id: Foreign Key relationship back to the related
            :py:class:`~purchasing.models.front.Opportunity`
        opportunity: Sqlalchemy relationship back to the related
            :py:class:`~purchasing.models.front.Opportunity`
        name: Name of the document for display
        href: Link to the document
    '''
    __tablename__ = 'opportunity_document'

    id = Column(db.Integer, primary_key=True, index=True)
    opportunity_id = ReferenceCol('opportunity', ondelete='cascade')
    opportunity = db.relationship(
        'Opportunity',
        backref=backref('opportunity_documents', lazy='dynamic', cascade='all, delete-orphan')
    )

    name = Column(db.String(255))
    href = Column(db.Text())

    def get_href(self):
        '''Builds link to the file

        Returns:
            S3 link if using S3, local filesystem link otherwise
        '''
        if current_app.config['UPLOAD_S3']:
            return self.href
        else:
            if self.href.startswith('http'):
                return self.href
            return 'file://{}'.format(self.href)

    def clean_name(self):
        '''Replaces underscores with spaces
        '''
        return self.name.replace('_', ' ')

class RequiredBidDocument(Model):
    '''Model for documents that a vendor would be required to provide

    There are two types of documents associated with an opportunity -- documents
    that the City will provide (RFP/IFB/RFQ, Q&A documents, etc.), and documents
    that the bidder will need to provide upon bidding (Insurance certificates,
    Bid bonds, etc.). This model describes the latter.

    See Also:
        These models get rendered into a select multi with the descriptions rendered
        in tooltips. For more on how this works, see the
        :py:func:`~purchasing.beacon.blueprints.opportunity_view_utils.select_multi_checkbox`.

    Attributes:
        id: Primary key unique ID
        display_name: Display name for the document
        description: Description of what the document is, rendered in a tooltip
        form_href: A link to an example document
    '''
    __tablename__ = 'document'

    id = Column(db.Integer, primary_key=True, index=True)
    display_name = Column(db.String(255), nullable=False)
    description = Column(db.Text, nullable=False)
    form_href = Column(db.String(255))

    def get_choices(self):
        '''Builds a custom two-tuple for the CHOICES.

        Returns:
            Two-tuple of (ID, [name, description, href]), which can then be
            passed to :py:func:`~purchasing.beacon.blueprints.opportunity_view_utils.select_multi_checkbox`
            to generate multi-checkbox fields
        '''
        return (self.id, [self.display_name, self.description, self.form_href])

    @classmethod
    def generate_choices(cls):
        '''Builds a list of custom CHOICES

        Returns:
            List of two-tuples described in the
            :py:meth:`RequiredBidDocument.get_choices`
            method
        '''
        return [i.get_choices() for i in cls.query.all()]
