# -*- coding: utf-8 -*-

import os

from unittest import TestCase
from mock import patch, Mock, MagicMock
from beacon.notifications import Notification

class TestNotification(TestCase):
    def setUp(self):
        os.environ['CONFIG'] = 'beacon.settings.TestConfig'

    @patch('beacon.notifications.render_template', return_value='a test')
    def test_notification_initialization(self, render_template):
        '''Test notifications properly initialize
        '''
        notification = Notification(
            from_email='foo@foo.com', to_email='foobar@bar.com', cc_email=[('bazbar@bar.com',), ('foobar@foo.com',)]
        )
        self.assertEquals(notification.to_email, ['foobar@bar.com'])
        self.assertEquals(notification.from_email, 'foo@foo.com')
        self.assertListEqual(notification.cc_email, ['bazbar@bar.com', 'foobar@foo.com'])
        self.assertEquals(notification.subject, '')
        self.assertEquals(notification.html_body, 'a test')
        self.assertEquals(notification.txt_body, 'a test\n\n')
        self.assertEquals(notification.attachments, [])

    @patch('beacon.notifications.render_template', return_value='a test')
    def test_notification_flatten(self, render_template):
        '''Test notification kwarg flattener
        '''
        obj = MagicMock()
        obj.__unicode__ = lambda x: 'quux'
        notification = Notification(from_email='foo@foo.com', foo='bar', baz=['qux1', obj])
        self.assertEquals(
            {'foo': 'bar', 'baz': 'qux1; qux2'},
            notification.convert_models(dict(foo='bar', baz=['qux1', 'qux2']))
        )

    @patch('beacon.notifications.render_template', return_value='a test')
    def test_notification_reshape(self, render_template):
        '''Test notification recipient flattener
        '''
        notification = Notification(to_email='foobar@foo.com', from_email='foo@foo.com')
        test_recips = [('a',), ('multi',), ['nested', 'thing']]
        self.assertListEqual(
            ['a', 'multi', 'nested', 'thing'],
            notification.flatten(test_recips)
        )

        test_recips_complex = ['a', ['b', ['c', 'd']], ['e']]
        self.assertListEqual(
            ['a', 'b', 'c', 'd', 'e'],
            notification.flatten(test_recips_complex)
        )

    @patch('beacon.notifications.current_app')
    @patch('beacon.notifications.render_template', return_value='a test')
    def test_notification_build_multi(self, current_app, render_template):
        '''Test multi-messages only have one recipient
        '''
        current_app.logger = Mock(info=Mock())
        notification = Notification(to_email=['foobar@foo.com', 'foobar2@foo.com'], from_email='foo@foo.com')

        # should build two messages on multi send
        msgs = notification._build(multi=True)
        self.assertTrue(len(msgs), 2)
        for msg in msgs:
            self.assertEquals(len(msg.recipients), 1)

    @patch('beacon.notifications.current_app')
    @patch('beacon.notifications.render_template', return_value='a test')
    def test_notification_build_multi(self, current_app, render_template):
        '''Test single build messages have multiple recipients
        '''
        current_app.logger = Mock(info=Mock())
        notification = Notification(to_email=['foobar@foo.com', 'foobar2@foo.com'], from_email='foo@foo.com')

        # should build two messages on multi send
        msgs = notification._build(multi=False)
        self.assertTrue(len(msgs), 1)
        for msg in msgs:
            self.assertEquals(len(msg.recipients), 2)


    @patch('flask_mail.Mail.send')
    @patch('beacon.notifications.send_email.delay', return_value=True)
    @patch('beacon.notifications.render_template', return_value='a test')
    def test_notification_send_multi(self, send, send_email, render_template):
        '''Test multi builds multiple message objects
        '''
        notification = Notification(to_email=['foobar@foo.com', 'foobar2@foo.com'], from_email='foo@foo.com')

        notification.build_msg = Mock()
        notification.build_msg.return_value = []

        # should build two messages on multi send
        notification.send(multi=True)
        self.assertTrue(notification.build_msg.called)
        self.assertEquals(notification.build_msg.call_count, 2)

    @patch('flask_mail.Mail.send')
    @patch('beacon.notifications.send_email.delay')
    @patch('beacon.notifications.render_template', return_value='a test')
    def test_notification_send_single(self, send, send_email, render_template):
        '''Test non-multi only builds one message even with multiple emails
        '''
        notification = Notification(to_email=['foobar@foo.com', 'foobar2@foo.com'], from_email='foo@foo.com')

        notification.build_msg = Mock()
        notification.build_msg.return_value = []

        # should build two messages on multi send
        notification.send(multi=False)
        self.assertTrue(notification.build_msg.called)
        self.assertEquals(notification.build_msg.call_count, 1)
