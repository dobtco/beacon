# -*- coding: utf-8 -*-

import csv

def convert_empty_to_none(val):
    '''Converts empty or "None" strings to None Types

    Arguments:
        val: The field to be converted

    Returns:
        The passed value if the value is not an empty string or
        'None', ``None`` otherwise.
    '''
    return val if val not in ['', 'None'] else None

def extract(file_target, first_row_headers=[]):
    '''Pulls csv data out of a file target.

    Arguments:
        file_target: a file object

    Keyword Arguments:
        first_row_headers: An optional list of headers that can
            be used as the keys in the returned DictReader

    Returns:
        A :py:class:`~csv.DictReader` object.
    '''
    data = []

    with open(file_target, 'rU') as f:
        fieldnames = first_row_headers if len(first_row_headers) > 0 else None
        reader = csv.DictReader(f, fieldnames=fieldnames)
        for row in reader:
            data.append(row)

    return data