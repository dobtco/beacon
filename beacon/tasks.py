# -*- coding: utf-8 -*-

from beacon.app import celery
from beacon.extensions import mail

@celery.task
def send_email(messages):
    with mail.connect() as conn:
        for message in messages:
            conn.send(message)
