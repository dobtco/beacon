from test.test_base import BaseTestCase
from beacon.models.users import User
from test.factories import RoleFactory, AcceptedEmailDomainsFactory

class TestUsers(BaseTestCase):
    def setUp(self):
        super(TestUsers, self).setUp()
        RoleFactory.create(name='staff')
        AcceptedEmailDomainsFactory.create(domain='foo.com')

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
        self.assertTrue(User.query.first().has_role('staff'))
