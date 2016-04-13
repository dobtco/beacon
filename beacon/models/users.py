# -*- coding: utf-8 -*-
from flask_security import UserMixin, RoleMixin
from flask_login import AnonymousUserMixin

from beacon.database import Column, db, Model, ReferenceCol, SurrogatePK
from sqlalchemy.orm import backref

roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('users.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('roles.id'))
)

class Role(RoleMixin, SurrogatePK, Model):
    '''Model to handle view-based permissions

    Attributes:
        id: primary key
        name: role name
    '''
    __tablename__ = 'roles'
    name = Column(db.String(80), unique=True, nullable=False)
    description = Column(db.String(255), unique=True)

    def __repr__(self):
        return '<Role({name})>'.format(name=self.name)

    def __unicode__(self):
        return self.name

    @classmethod
    def query_factory(cls):
        '''Generates a query of all roles

        Returns:
            `sqla query`_ of all roles
        '''
        return cls.query

    @classmethod
    def no_admins(cls):
        '''Generates a query of non-admin roles

        Returns:
            `sqla query`_ of roles without administrative access
        '''
        return cls.query.filter(cls.name != 'admin')

    @classmethod
    def staff_factory(cls):
        '''Factory to return the staff role

        Returns:
            Role object with the name 'staff'
        '''
        return cls.query.filter(cls.name == 'staff')

class User(UserMixin, SurrogatePK, Model):
    '''User model

    Attributes:
        id: primary key
        email: user email address
        first_name: first name of user
        last_name: last name of user
        active: whether user is currently active or not
        role_id: foreign key of user's role
        role: relationship of user to role table
        department_id: foreign key of user's department
        department: relationship of user to department table
    '''

    __tablename__ = 'users'
    email = Column(db.String(80), unique=True, nullable=False, index=True)
    first_name = Column(db.String(30), nullable=True)
    last_name = Column(db.String(30), nullable=True)
    active = Column(db.Boolean(), default=True)

    roles = db.relationship(
        'Role', secondary=roles_users,
        backref=backref('users', lazy='dynamic'),
    )
    vendor_id = db.relationship(
        'Vendor', backref=backref('users', lazy='dynamic'),
        foreign_keys=vendor_id, primaryjoin='User.department_id==Vendor.id'
    )

    department_id = ReferenceCol('department', ondelete='SET NULL', nullable=True)
    department = db.relationship(
        'Department', backref=backref('users', lazy='dynamic'),
        foreign_keys=department_id, primaryjoin='User.department_id==Department.id'
    )

    password = db.Column(db.String(255))
    

    confirmed_at = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)
    current_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(255))
    current_login_ip = db.Column(db.String(255))
    login_count = db.Column(db.Integer)
    subscribed_to_newsletter = Column(db.Boolean(), default=False, nullable=False)


    def __repr__(self):
        return '<User({email!r})>'.format(email=self.email)

    def __unicode__(self):
        return self.email

    @property
    def role(self):
        if len(self.roles) > 0:
            return self.roles[0]
        return Role(name='')

    @property
    def full_name(self):
        '''Build full name of user

        Returns:
            concatenated string of first_name and last_name values
        '''
        return "{0} {1}".format(self.first_name, self.last_name)

    @classmethod
    def department_user_factory(cls, department_id):
        return cls.query.filter(
            cls.department_id == department_id,
            db.func.lower(Department.name) != 'equal opportunity review commission'
        )

    def is_approver(self):
        '''Check if user can do approvals

        Returns:
            True if user's role is either approver or admin,
            False otherwise
        '''
        return any([
            self.has_role('approver'),
            self.has_role('admin'),
        ])

    def is_admin(self):
        '''Check if user can access admin applications

        Returns:
            True if user's role is admin or superadmin, False otherwise
        '''
        return any([
            self.has_role('admin'),
        ])

    def print_pretty_name(self):
        '''Generate long version text representation of user

        Returns:
            full_name if first_name and last_name exist, email otherwise
        '''
        if self.first_name and self.last_name:
            return self.full_name
        else:
            return self.email

    def print_pretty_first_name(self):
        '''Generate abbreviated text representation of user

        Returns:
            first_name if first_name exists,
            `localpart <https://en.wikipedia.org/wiki/Email_address#Local_part>`_
            otherwise
        '''
        if self.first_name:
            return self.first_name
        else:
            return self.email.split('@')[0]

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

class Department(SurrogatePK, Model):
    '''Department model

    Attributes:
        name: Name of department
    '''
    __tablename__ = 'department'

    name = Column(db.String(255), nullable=False, unique=True)

    def __unicode__(self):
        return self.name

    @classmethod
    def query_factory_all(cls):
        '''Generate a department query factory with all departments.
        '''
        return cls.query

    @classmethod
    def query_factory(cls):
        '''Generate a department query factory.

        Returns:
            Department query with new users filtered out
        '''
        return cls.query.filter(cls.name != 'New User')

    @classmethod
    def get_dept(cls, dept_name):
        '''Query Department by name.

        Arguments:
            dept_name: name used for query

        Returns:
            an instance of Department
        '''
        return cls.query.filter(db.func.lower(cls.name) == dept_name.lower()).first()

    @classmethod
    def choices(cls, blank=False):
        '''Query available departments by name and id.

        Arguments:
            blank: adds none choice to list when True,
                only returns Departments when False. Defaults to False.

        Returns:
            list of (department id, department name) tuples
        '''
        departments = [(i.id, i.name) for i in cls.query_factory().all()]
        if blank:
            departments = [(None, '-----')] + departments
        return departments

class AnonymousUser(AnonymousUserMixin):
    '''Custom mixin for handling anonymous (non-logged-in) users

    Attributes:
        role: :py:class:`~purchasing.user.models.Role`
            object with name set to 'anonymous'
        department: :py:class:`~purchasing.user.models.Department`
            object with name set to 'anonymous'
        id: Defaults to -1

    See Also:
        ``AnonymousUser`` subclasses the `flask_security anonymous user mixin
        <https://flask-login.readthedocs.org/en/latest/#anonymous-users>`_,
        which contains a number of class and instance methods around
        determining if users are currently logged in.
    '''
    roles = [Role(name='anonymous')]
    department = Department(name='anonymous')
    id = -1

    def __init__(self, *args, **kwargs):
        super(AnonymousUser, self).__init__(*args, **kwargs)

    def is_admin(self):
        return False

    def is_approver(self):
        return False
