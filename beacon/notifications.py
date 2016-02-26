# -*- coding: utf-8 -*-

import collections

from werkzeug import secure_filename
from werkzeug.datastructures import FileStorage

from flask import render_template, current_app
from flask_mail import Message

from beacon.compat import basestring
from beacon.tasks import send_email

import html2text

class Notification(object):
    '''Build a new notification object

    A notification object is a light wrapper around the Flask-Mail `Message`_
    object that also handles compiling and building HTML and text
    templates.

    Arguments:
        to_email: list of valid email addresses
        from_email: from email address, defaults to the app's
            configured ``MAIL_DEFAULT_SENDER``
        cc_email: list of valid email addresses
        subject: subject line for the email that will be sent
        html_template: path to a jinja html template to be compiled
        attachments: list of `FileStorage`_ objects
        reply_to: valid email that will be used and reply-to
        convert_args: Flag as to whether to convert all additional \**kwargs
            passed to the Notification as a dictionary to the html/txt
            templates
        *args: A list of additional arguments
        **kwargs: Remaining keywords arguments to be consumed when rendering
            the html/text templates
    '''
    def __init__(
        self, to_email=[], from_email=None,
        cc_email=[], subject='',
        html_template='/beacon/emails/email_admins.html',
        attachments=[], reply_to=None,
        convert_args=False, *args, **kwargs
    ):
        self.to_email = self.handle_recipients(to_email)
        self.from_email = from_email if from_email else current_app.config['MAIL_DEFAULT_SENDER']
        self.reply_to = reply_to
        self.cc_email = self.handle_recipients(cc_email)
        self.subject = subject
        self.html_body = self.build_msg_body(html_template, convert_args, *args, **kwargs)
        self.txt_body = html2text.html2text(self.html_body)
        self.attachments = attachments

    def build_msg_body(self, template, convert_args, *args, **kwargs):
        '''Build an HTML or text message body for an email

        Arguments:
            template: Path to an HTML/text template
            convert_args: Whether to convert the passed kwargs into a single
                dictionary that can be iterated through by the default admin
                template.
            *args: A list of additional arguments
            **kwargs: Remaining keywords arguments to be consumed when rendering
                the html/text templates

        Returns:
            Rendered HTML/text template to be attached to the Notification
        '''
        if convert_args:
            return render_template(template, kwargs=self.convert_models(dict(kwargs)))
        return render_template(template, *args, **kwargs)

    def convert_models(self, kwarg_dict):
        '''Convert a list of keyword arguments to a dictionary

        Modifies the passed-in dictionary to replace lists in the models with their
        ``__unicode__`` representations for easier reading.

        Arguments:
            kwarg_dict: A dictionary of kwargs, taken from instantiation of
                the Notification

        Returns:
            Modified dictionary with list values replaced by more readable
            representations of their elements
        '''
        for key, value in kwarg_dict.iteritems():
            if isinstance(value, (set, list)):
                tmp_list = []
                for v in value:
                    if hasattr(v, '__unicode__'):
                        tmp_list.append(v.__unicode__())
                    else:
                        tmp_list.append(v)
                kwarg_dict[key] = '; '.join(tmp_list)
            else:
                pass

        return kwarg_dict

    def _flatten(self, l):
        '''Returns a flat generator object from artibrary-depth iterables

        Arguments:
            l: A nested iterable of any depth

        Yields:
            el: A top-level element in the passed iterable
            sub: A non-top-level element in the passed iterable
        '''
        for el in l:
            if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
                for sub in self._flatten(el):
                    yield sub
            else:
                yield el

    def flatten(self, l):
        '''Coerces the generator from _flatten to a list and return it

        Example
            .. code-block:: python

            >>> flatten([('a',), ('multi',), ['nested', 'thing']])
            >>> # ['a', 'multi', 'nested', 'thing']

        Arguments:
            l: A nested iterable of any depth

        Returns:
            A flattened list
        '''
        return list(self._flatten(l))

    def handle_recipients(self, recipient):
        '''Turns string/list/nested list of recipients into a list of recipient emails

        Arguments:
            recipient: All sorts of forms of recipients (string, unicode, list,
                list of lists)

        Returns:
            List of recipients with depth one
        '''
        if isinstance(recipient, str) or isinstance(recipient, unicode):
            recipient = [recipient]
        elif isinstance(recipient, collections.Iterable):
            recipient = set(recipient)
            recipient = self.flatten(recipient)
        else:
            raise Exception('Unsupported recipient type: {}'.format(type(recipient)))
        return recipient

    def build_msg(self, recipient):
        '''Builds a `Message`_ object with body, attachments

        Argument:
            recipient: A formatted single-depth list of email addresses

        Returns:
            `Message`_ object
        '''
        try:
            current_app.logger.info(
                'EMAILTRY | Sending message:\nTo: {}\n:From: {}\nSubject: {}'.format(
                    recipient, self.from_email, self.subject
                )
            )

            msg = Message(
                subject='[Beacon] {}'.format(self.subject),
                html=self.html_body, body=self.txt_body,
                sender=self.from_email, reply_to=self.reply_to,
                recipients=self.handle_recipients(recipient), cc=self.cc_email
            )

            for attachment in self.attachments:
                if (
                    isinstance(attachment, FileStorage) and
                    secure_filename(attachment.filename) != ''
                ):
                        msg.attach(
                            filename=secure_filename(attachment.filename),
                            content_type=attachment.content_type,
                            data=attachment.stream.read()
                        )

            return msg

        except Exception, e:
            current_app.logger.info(
                'EMAILFAIL | Error: {}\nTo: {}\n:From: {}\nSubject: {}'.format(
                    e, self.to_email, self.from_email, self.subject
                )
            )
            return False

    def _build(self, multi=False):
        '''Builds a single or collection of `Message`_ objects

        Keyword Arguments:
            multi: If True, multi will build an individual Notification for each
                recipient. If False, a single Notification will be created with
                all of the recipients visible in the ``to`` line.

        Returns:
            List of `Message`_ objects
        '''
        msgs = []
        if multi:
            for to in self.to_email:
                msgs.append(self.build_msg(to))
        else:
            msgs.append(self.build_msg(self.to_email))

        return msgs

    def send(self, multi=False, async=True):
        '''Send a single or group of notifications

        Keyword Arguments:
            multi: If True, multi will build an individual Notification for each
                recipient. If False, a single Notification will be created with
                all of the recipients visible in the ``to`` line.
            async: If True, the sending will be kicked out to a Celery worker
                process. If False, the sending will occur on the main request thread
        '''
        msgs = self._build(multi)

        if async:
            send_email.delay(msgs)
        else:
            send_email.run(msgs)
        return True
