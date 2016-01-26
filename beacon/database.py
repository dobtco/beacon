# -*- coding: utf-8 -*-
"""Database module, including the SQLAlchemy database object and DB-related
utilities.
"""
import datetime

import sqlalchemy

from flask_security import current_user

from sqlalchemy.sql.functions import GenericFunction
from sqlalchemy.orm import relationship

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declared_attr

from .extensions import db
from .compat import basestring

# Alias common SQLAlchemy names
Column = db.Column
relationship = relationship

class CRUDMixin(object):
    """Mixin that adds convenience methods for CRUD (create, read, update, delete)
    operations.
    """

    @classmethod
    def create(cls, **kwargs):
        """Create a new record and save it the database."""
        instance = cls(**kwargs)
        return instance.save()

    def update(self, commit=True, **kwargs):
        """Update specific fields of a record."""
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        """Save the record."""
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        """Remove the record from the database."""
        db.session.delete(self)
        return commit and db.session.commit()

def ReferenceCol(tablename, nullable=False, ondelete=None, pk_name='id', **kwargs):
    """Column that adds primary key foreign key reference.

    Usage: ::

        category_id = ReferenceCol('category')
        category = relationship('Category', backref='categories')
    """
    return db.Column(
        db.ForeignKey("{0}.{1}".format(tablename, pk_name), ondelete=ondelete),
        nullable=nullable, **kwargs)

class Model(CRUDMixin, db.Model):
    '''Base model class that includes CRUD convenience methods.

    All models that inherit from this model automatically have several
    additional attributes attached to them:

    Attributes:
        created_at: Timestamp for when the model was created
        updated_at: Timestamp for when the model was updated
        created_by_id: Foreign key to
            :py:class:`~purchasing.data.users.User`
        created_by: Sqlalchemy relationship to
            :py:class:`~purchasing.data.users.User`
        updated_by_id: Foreign key to
            :py:class:`~purchasing.data.users.User`
        updated_by: Sqlalchemy relationship to
            :py:class:`~purchasing.data.users.User`
    '''
    __abstract__ = True

    created_at = Column(db.DateTime)
    updated_at = Column(db.DateTime)

    @declared_attr
    def created_by_id(cls):
        return Column(
            db.Integer(), db.ForeignKey('users.id', use_alter=True, name='created_by_id_fkey'), nullable=True
        )

    @declared_attr
    def created_by(cls):
        return db.relationship('User', foreign_keys=lambda: cls.created_by_id)

    @declared_attr
    def updated_by_id(cls):
        return Column(
            db.Integer(), db.ForeignKey('users.id', use_alter=True, name='updated_by_id_fkey'), nullable=True
        )

    @declared_attr
    def updated_by(cls):
        return db.relationship('User', foreign_keys=lambda: cls.updated_by_id)

    def unicode_helper(self, field):
        if field:
            return field.encode('utf-8').strip()
        return u''

    def serialize_dates(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return obj

    def as_dict(self):
        return {
            c.name: self.serialize_dates(getattr(self, c.name)) for c in self.__table__.columns
        }

@sqlalchemy.event.listens_for(Model, 'before_insert', propagate=True)
def before_insert(mapper, connecton, instance):
    instance.created_at = datetime.datetime.utcnow()
    instance.created_by_id = current_user.id if hasattr(current_user, 'id') and not current_user.is_anonymous else None

@sqlalchemy.event.listens_for(Model, 'before_update', propagate=True)
def before_update(mapper, connection, instance):
    if db.session.object_session(instance).is_modified(instance, include_collections=False):
        instance.updated_at = datetime.datetime.utcnow()
        instance.updated_by_id = current_user.id if hasattr(current_user, 'id') and not current_user.is_anonymous else None

# From Mike Bayer's "Building the app" talk
# https://speakerdeck.com/zzzeek/building-the-app
class SurrogatePK(object):
    """A mixin that adds a surrogate integer 'primary key' column named
    ``id`` to any declarative-mapped class.
    """
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)

    @classmethod
    def get_by_id(cls, id):
        if any(
            (isinstance(id, basestring) and id.isdigit(),
             isinstance(id, (int, float))),
        ):
            return cls.query.get(int(id))
        return None

def get_or_create(session, model, create_method='', create_method_kwargs=None, **kwargs):
    '''Get a method or create it if it doesn't exist.

    For implementation details, see `this post
    <http://skien.cc/blog/2014/01/15/sqlalchemy-and-race-conditions-implementing/>`_

    Arguments:
        session: SQLAlchemy database session
        model: The model object to find or create
        create_method: Optional custom instantiation method for model
        create_method_kwargs: Optional instantiation kwargs for model
        **kwargs: Any arguments needed to find or create the model

    Returns:
        Two-tuple of (Created/Found model, True if found False if created)
    '''
    try:
        return session.query(model).filter_by(**kwargs).one(), True
    except NoResultFound:
        kwargs.update(create_method_kwargs or {})
        created = getattr(model, create_method, model)(**kwargs)
        try:
            session.add(created)
            session.flush()
            return created, False
        except IntegrityError:
            session.rollback()
            return session.query(model).filter_by(**kwargs).one(), True

class SplitPart(GenericFunction):
    package = 'string'
    name = 'split_part'
