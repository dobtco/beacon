# -*- coding: utf-8 -*-
'''Helper utilities and decorators.'''

import datetime
import re
import os
import random
import string
import time
import email
import pytz

from boto.s3.connection import S3Connection

from wtforms.validators import InputRequired, StopValidation

from flask import current_app

# modified from https://gist.github.com/bsmithgall/372de43205804a2279c9
SMALL_WORDS = re.compile(r'^(a|an|and|as|at|but|by|en|etc|for|if|in|nor|of|on|or|per|the|to|vs?\.?|via)$', re.I)
SPACE_SPLIT = re.compile(r'[\t ]')
# taken from http://stackoverflow.com/a/267405
CAP_WORDS = re.compile(r'^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$|(^COSTARS$)|(^PA$)|(^PQ$)|(^LLC$)')
PUNC_REGEX = re.compile(r'[{}]'.format(re.escape(string.punctuation)))
# taken from python-titlecase: https://github.com/ppannuto/python-titlecase/blob/master/titlecase/__init__.py#L27
UC_INITIALS = re.compile(r'^(?:[A-Z]{1}\.{1}|[A-Z]{1}\.{1}[A-Z]{1})+$', re.I)

def random_id(n):
    '''Returns random id of length n

    Taken from: http://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python/2257449#2257449
    '''
    return ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(n)
    )

def connect_to_s3(access_key, access_secret, bucket_name):
    conn = S3Connection(
        aws_access_key_id=access_key,
        aws_secret_access_key=access_secret
    )
    bucket = conn.get_bucket(bucket_name)
    return conn, bucket

def upload_file(filename, bucket, input_file=None, root=None, prefix='/static', from_file=False):
    filepath = os.path.join(root, filename.lstrip('/')) if root else filename
    _file = bucket.new_key(
        '{}/{}'.format(prefix, filename)
    )
    aggressive_headers = _get_aggressive_cache_headers(_file)
    if from_file:
        _file.set_contents_from_file(input_file, headers=aggressive_headers, replace=True)
    else:
        _file.set_contents_from_filename(filepath, headers=aggressive_headers)
    _file.set_acl('public-read')
    return _file.generate_url(expires_in=0, query_auth=False)

def _get_aggressive_cache_headers(key):
    '''
    Utility for setting file expiry headers on S3
    '''
    metadata = key.metadata

    # HTTP/1.0 (5 years)
    metadata['Expires'] = '{} GMT'.format(
        email.Utils.formatdate(
            time.mktime((datetime.datetime.utcnow() + datetime.timedelta(days=365 * 5)).timetuple())
        )
    )

    if 'css' in key.name.lower():
        metadata['Content-Type'] = 'text/css'
    else:
        metadata['Content-Type'] = key.content_type

    # HTTP/1.1 (5 years)
    metadata['Cache-Control'] = 'max-age=%d, public' % (3600 * 24 * 360 * 5)

    return metadata

def build_downloadable_groups(val, iterable):
    '''Sorts and dedupes related lists

    Handles quoting, deduping, and sorting
    '''
    return '"' + '; '.join(
        sorted(list(set([i.__dict__[val] for i in iterable])))
    ) + '"'

def localize_now():
    return pytz.UTC.localize(datetime.datetime.now()).astimezone(current_app.config['DISPLAY_TIMEZONE'])

def localize_today():
    return pytz.UTC.localize(datetime.datetime.today()).astimezone(current_app.config['DISPLAY_TIMEZONE']).date()

def localize_datetime(date):
    '''Take a naive (UTC) datetime object and normalize it to the display timezone
    '''
    if date:
        return pytz.UTC.localize(date).astimezone(current_app.config['DISPLAY_TIMEZONE'])
    return ''

def localize_and_strip(date):
    '''Take a naive (UTC) datetime object, normalize it to the display timezone, and remove tzinfo
    '''
    return pytz.UTC.localize(date).astimezone(current_app.config['DISPLAY_TIMEZONE']).replace(tzinfo=None)

class RequiredIf(InputRequired):
    # a validator which makes a field required if
    # another field is set and has a truthy value
    # http://stackoverflow.com/questions/8463209/how-to-make-a-field-conditionally-optional-in-wtforms
    # thanks to Team RVA for pointing this out

    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super(RequiredIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception(
                'no field named "%s" in form' %
                other_field.label.text if other_field.label else self.other_field_name
            )
        if bool(other_field.data) and not bool(field.data):
            raise StopValidation(
                'You filled out "%s" but left this blank -- please fill this out as well.' %
                other_field.label.text if other_field.label else self.other_field_name
            )
