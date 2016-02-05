from test.test_base import BaseTestCase
from test.factories import (
    UserFactory, RoleFactory, AcceptedEmailDomainsFactory,
    DepartmentFactory
)

from beacon.models.users import User
from beacon.database import db

class TestUsers(BaseTestCase):
    def setUp(self):
        super(TestUsers, self).setUp()
        self.staff = RoleFactory.create(name='staff')
        AcceptedEmailDomainsFactory.create(domain='foo.com')
        self.new_dept = DepartmentFactory.create(name='New User').save()
        self.department1 = DepartmentFactory.create(name='Test').save()

    def test_no_register_bad_domain(self):
        post = self.client.post('/register', data=dict(
            email='bad@notgood.com',
            password='password',
            password_confirm='password'
        ))
        self.assertEquals(User.query.count(), 0)
        self.assert200(post)
        self.assertTrue('not a valid email domain! You must be associated with the city.' in post.data)

    def test_new_user_has_staff_role(self):
        self.client.post('/register', data=dict(
            email='email@foo.com',
            password='password',
            password_confirm='password'
        ))
        self.assertEquals(User.query.count(), 1)
        new_user = User.query.first()
        self.assertTrue(new_user.has_role('staff'))
        self.assertEquals(new_user.department.name, 'New User')

    def test_user_update_profile(self):
        user = UserFactory.create(
            roles=[self.staff], department=self.new_dept
        )
        db.session.commit()
        self.login_user(user)

        first_profile_visit = self.client.get('/users/profile')
        self.assertTrue('Welcome to Beacon' in first_profile_visit.data)

        bad_update = self.client.post('/users/profile', data=dict(
            department='THIS IS NOT A VALID DEPARTMENT'
        ), follow_redirects=True)

        self.assertTrue(
            'THIS IS NOT A VALID DEPARTMENT' not in [i.department for i in User.query.all()]
        )
        self.assertTrue('Not a valid choice' in bad_update.data)

        update = self.client.post('/users/profile', data=dict(
            first_name='foo', last_name='bar',
            department=str(self.department1.id)
        ))

        self.assertEquals(update.status_code, 302)
        self.assert_flashes('Updated your profile!', 'alert-success')

        repeat_visit = self.client.get('/users/profile')
        self.assertFalse('Welcome to Beacon' in repeat_visit.data)
