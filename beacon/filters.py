# -*- coding: utf-8 -*-

import datetime
import string
import re

import pytz
import dateutil.parser
from flask import request, url_for, current_app
from flask_security import current_user

from beacon.compat import basestring
from jinja2 import evalcontextfilter, Markup

from beacon.models.users import User

# modified from https://gist.github.com/bsmithgall/372de43205804a2279c9
SMALL_WORDS = re.compile(r'^(a|an|and|as|at|but|by|en|etc|for|if|in|nor|of|on|or|per|the|to|vs?\.?|via)$', re.I)
SPACE_SPLIT = re.compile(r'\s+')
# taken from http://stackoverflow.com/a/267405
CAP_WORDS = re.compile(r'^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$|(^COSTARS$)|(^PA$)|(^PQ$)|(^LLC$)', re.I)
PUNC_REGEX = re.compile(r'[{}]'.format(re.escape(string.punctuation)))
# taken from python-titlecase: https://github.com/ppannuto/python-titlecase/blob/master/titlecase/__init__.py#L27
UC_INITIALS = re.compile(r'^(?:[A-Z]{1}\.{1}|[A-Z]{1}\.{1}[A-Z]{1})+$', re.I)
ONE_LETTER_NUMBERS = re.compile(r'^[A-Za-z]{1}\d+$')
PARAGRAPH = re.compile(r'(?:\r\n|\r|\n){2,}')

def format_currency(value):
    return "${:,.2f}".format(value)

def url_for_other_page(page):
    args = dict(request.view_args.items() + request.args.to_dict().items())
    args['page'] = page
    return url_for(request.endpoint, **args)

def thispage():
    try:
        args = dict(request.view_args.items() + request.args.to_dict().items())
        args['thispage'] = '{path}?{query}'.format(
            path=request.path, query=request.query_string
        )
        return url_for(request.endpoint, **args)
    # pass for favicon
    except AttributeError:
        pass

def _current_user():
    args = dict(request.view_args.items() + request.args.to_dict().items())
    args['_current_user'] = current_user
    return url_for(request.endpoint, **args)

def now():
    return pytz.UTC.localize(datetime.datetime.utcnow()).astimezone(current_app.config['DISPLAY_TIMEZONE'])

def better_title(string):
    '''drop in replacement for jinja default title filter

    modified from https://gist.github.com/bsmithgall/372de43205804a2279c9
    '''
    rv = []
    for ix, word in enumerate(re.split(SPACE_SPLIT, string)):
        _cleaned_word = PUNC_REGEX.sub('', word)
        if re.match(UC_INITIALS, word):
            rv.append(word.upper())
        elif re.match(SMALL_WORDS, _cleaned_word.strip()) and ix > 0:
            rv.append(word.lower())
        elif word.startswith('('):
            new_string = '('
            new_string += better_title(word.lstrip('('))
            rv.append(new_string)
        elif re.match(CAP_WORDS, _cleaned_word):
            rv.append(word.upper())
        elif re.match(ONE_LETTER_NUMBERS, _cleaned_word):
            rv.append(word.lower())
        else:
            rv.append(word[0].upper() + word[1:].lower())

    return ' '.join(rv)

def days_from_today(field):
    '''Takes a python date object and returns days from today
    '''
    if isinstance(field, datetime.date):
        return (
            datetime.date(field.year, field.month, field.day) -
            datetime.date.today()
        ).days
    elif isinstance(field, datetime.datetime):
        field = field.replace(tzinfo=pytz.utc)
        return (
            datetime.datetime(field.year, field.month, field.day) -
            datetime.datetime.now(pytz.utc)
        ).days
    else:
        return field

def format_days_from_today(field):
    '''Uses days_from_today to build readable "X days ago"
    '''
    days = days_from_today(field)
    if days == 0:
        return 'Today'
    elif days == 1:
        return '{} day from now'.format(abs(days))
    elif days > 1:
        return '{} days from now'.format(abs(days))
    elif days == -1:
        return '{} day ago'.format(abs(days))
    else:
        return '{} days ago'.format(abs(days))

def datetimeformat(date, fmt='%Y-%m-%d', to_date=True):
    if date is None:
        return ''

    if isinstance(date, basestring):
        date = dateutil.parser.parse(date)

    if isinstance(date, datetime.datetime) and not all(
        [date.second == 0, date.minute == 0, date.hour == 0, date.microsecond == 0]
    ):
        if date.tzinfo is not None:
            date = date.astimezone(current_app.config['DISPLAY_TIMEZONE'])
        else:
            date = pytz.UTC.localize(date).astimezone(current_app.config['DISPLAY_TIMEZONE'])

        if to_date:
            date = date.date()

    return date.strftime(fmt)

def print_user_name(user_id):
    return User.query.get(user_id).print_pretty_name()

def localize(date):
    return pytz.UTC.localize(date).astimezone(current_app.config['DISPLAY_TIMEZONE'])

def display_dedupe_array(arr):
    '''Dedupe and sort an array
    '''
    if arr:
        return '; '.join(sorted(list(set(arr))))
    return ''

@evalcontextfilter
def newline_to_br(eval_ctx, value):
    '''Replaces newline characters with <br> tags

    Adapted from http://flask.pocoo.org/snippets/28/
    '''
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') for p in PARAGRAPH.split(value))
    if eval_ctx and eval_ctx.autoescape:
        result = Markup(result)
    return result.lstrip()

def external_link_warning():
    '''Checks external link config setting and returns string needed to trigger extlink.js if True
    '''
    if current_app.config.get('EXTERNAL_LINK_WARNING') is not None:
        return 'js-external-link'
    return ''
