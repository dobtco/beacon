# -*- coding: utf-8 -*-

import time
import datetime
import urllib2
import json

from flask import jsonify, current_app, Blueprint

from beacon.extensions import cache
from beacon.models.public import AppStatus

blueprint = Blueprint(
    'public', __name__, url_prefix='/app',
    static_folder="../static"
)

@blueprint.route('/_status')
def status():
    '''Reports about App Status
    '''
    response = {
        'status': 'ok',
        'dependencies': ['Celery', 'Postgres', 'Redis', 'S3', 'Sendgrid'],
        'resources': {}
    }

    # order the try/except blocks in the reverse order of seriousness
    # in terms of an outage
    try:
        url = 'https://sendgrid.com/api/stats.get.json?api_user={user}&api_key={_pass}&days={days}'.format(
            user=current_app.config['MAIL_USERNAME'],
            _pass=current_app.config['MAIL_PASSWORD'],
            days=datetime.date.today().day
        )

        sendgrid = json.loads(urllib2.urlopen(url).read())
        sent = sum([m['delivered'] + m['repeat_bounces'] for m in sendgrid])
        response['resources']['Sendgrid'] = '{}% used'.format((100 * float(sent)) / int(
            current_app.config.get('SENDGRID_MONTHLY_LIMIT', 12000)
        ))

    except Exception, e:
        response['status'] = 'Sendgrid is unavailable: {}'.format(e)

    try:
        # TODO: figure out some way to figure out if s3 is down
        pass
    except Exception, e:
        response['status'] = 'S3 is unavailable: {}'.format(e)

    try:
        redis_up = cache.cache._client.ping()
        if not redis_up:
            response['status'] = 'Redis is down or unavailable'
    except Exception, e:
        response['status'] = 'Redis is down or unavailable'

    try:
        status = AppStatus.query.first()
        if status.status != 'ok':
            if response['status'] != 'ok':
                response['status'] += ' || {}: {}'.format(status.status, status.message)
            else:
                response['status'] = '{}: {}'.format(status.status, status.message)
    except Exception, e:
        response['status'] = 'Database is unavailable: {}'.format(e)

    response['updated'] = int(time.time())
    return jsonify(response)
