#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import os
from flask import current_app
from flask_script import Manager, Shell, Server
from flask_migrate import MigrateCommand
from flask.ext.assets import ManageAssets

from beacon.app import create_app
from beacon.database import db
from beacon.utils import connect_to_s3, upload_file

from beacon.models.public import AppStatus
from beacon import jobs as nightly_jobs

app = create_app()

HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'tests')

manager = Manager(app)

def _make_context():
    """Return context dict for a shell session so you can access
    app, db, and the User model by default.
    """
    return {'app': app, 'db': db}

@manager.option('-e', '--email', dest='email', default=None)
@manager.option('-r', '--role', dest='role', default=None)
@manager.option('-d', '--department', dest='dept', default='Other')
@manager.option('-p', '--password', dest='password', default='password')
def seed_user(email, role, dept, password):
    '''
    Creates a new user in the database.
    '''
    from beacon.models.users import User, Role, Department
    from flask_security import SQLAlchemyUserDatastore
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    seed_email = email if email else app.config.get('SEED_EMAIL')
    user_exists = User.query.filter(User.email == seed_email).first()
    department = Department.query.filter(
        Department.name == db.func.lower(dept)
    ).first()
    if user_exists:
        print 'User {email} already exists'.format(email=seed_email)
    else:
        try:
            user_datastore.create_user(
                email=seed_email,
                created_at=datetime.datetime.utcnow(),
                department=department if department else None,
                password=password,
                roles=[Role.query.get(int(role))]
            )
            db.session.commit()
            print 'User {email} successfully created!'.format(email=seed_email)
        except Exception, e:
            print 'Something went wrong: {exception}'.format(exception=e.message)
    return

@manager.option(
    '-f', '--file', dest='filepath',
    default='./beacon/importer/files/2015-07-01-nigp-cleaned.csv'
)
@manager.option('-r', '--replace', dest='replace', default=False)
def import_nigp(filepath, replace=False):
    if replace:
        print 'Deleting current categories...'
        db.session.execute(
            'DELETE FROM category'
        )
        db.session.commit
    from beacon.importer.nigp import main
    print 'Importing data from {filepath}\n'.format(filepath=filepath)
    main(filepath)
    print 'Import finished!'
    return

@manager.option('-u', '--user_id', dest='user')
@manager.option('-p', '--secret', dest='secret')
@manager.option('-b', '--bucket', dest='bucket')
@manager.option('-r', '--retries', dest='_retries', default=5)
def upload_assets(user, secret, bucket, _retries=5):
    access_key = user if user else os.environ['AWS_ACCESS_KEY_ID']
    access_secret = secret if secret else os.environ['AWS_SECRET_ACCESS_KEY']
    bucket = bucket if bucket else os.environ['S3_BUCKET_NAME']

    retries = 0

    import subprocess
    # build assets and capture the output
    print 'Building assets...'
    proc = subprocess.Popen(
        ['python', 'manage.py', 'assets', 'build'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    proc.wait()

    print 'Connecting to S3...'
    conn, bucket = connect_to_s3(access_key, access_secret, bucket)
    print 'Uploading files...'

    for path in proc.communicate()[0].split('\n')[:-1]:
        key = path.split('public')[1]
        print 'Uploading {}'.format(key)
        while retries <= _retries:
            try:
                upload_file(key, bucket, root=current_app.config['APP_DIR'] + '/static')
                break
            except Exception, e:
                print 'Error: {}'.format(e), 'Retrying...'
                retries += 1
        if retries > _retries:
            print 'File {} did not upload'.format(key)
        retries = 0

    for fontfile in os.listdir(os.path.join(current_app.config['APP_DIR'], 'static', 'fonts')):
        print 'Uploading {}'.format(fontfile)
        while retries <= _retries:
            try:
                upload_file(
                    fontfile, bucket, root=current_app.config['APP_DIR'] + '/static/fonts',
                    prefix='/static/fonts'
                )
                break
            except Exception, e:
                print 'Error: {}'.format(e), 'Retrying...'
                retries += 1
        if retries > _retries:
            print 'File {} did not upload'.format(fontfile)
        retries = 0

    print 'Uploading images...'
    for root, _, files in os.walk(current_app.config['APP_DIR'] + '/static/img'):
        for filepath in files:
            print 'Uploading {}'.format(filepath)
            while retries <= _retries:
                try:
                    upload_file(filepath, bucket, root=root, prefix='/static/img/')
                    break
                except Exception, e:
                    print 'Error: {}'.format(e), 'Retrying...'
                    retries += 1
            retries = 0

    print 'Uploading favicon...'
    retries = 0
    while retries <= _retries:
        try:
            upload_file('favicon.ico', bucket, root=current_app.config['APP_DIR'] + '/static', prefix='/static')
            break
        except Exception, e:
            print 'Error: {}'.format(e), 'Retrying...'
            retries += 1
    return

@manager.command
def all_clear():
    status = AppStatus.query.first()
    status.status = 'ok'
    status.last_updated = datetime.datetime.now()
    status.message = None
    db.session.commit()
    print 'All clear!'
    return

@manager.option('-r', '--s3user', dest='user')
@manager.option('-p', '--s3secret', dest='secret')
@manager.option('-t', '--s3bucket', dest='bucket')
@manager.command
def seed(user=None, secret=None, bucket=None):
    '''Seeds a test/dev instance with new data
    '''
    user = user if user else os.environ.get('AWS_ACCESS_KEY_ID')
    secret = secret if secret else os.environ.get('AWS_SECRET_ACCESS_KEY')
    bucket = bucket if bucket else os.environ.get('S3_BUCKET_NAME')
    # import seed nigp
    import_nigp('./beacon/importer/seed/2015-07-01-seed-nigp-cleaned.csv')
    print ''

@manager.command
def schedule_work(ignore_time=False):
    from beacon.jobs import JobBase
    for job in JobBase.jobs:
        job(time_override=ignore_time).schedule_job()
        db.session.commit()

@manager.command
def do_work(ignore_time=False):
    from beacon.jobs.job_base import JobStatus
    jobs = JobStatus.query.filter(JobStatus.status == 'new').all()
    for job in jobs:
        task = getattr(nightly_jobs, job.name)(time_override=ignore_time)
        task.run_job(job)

manager.add_command('server', Server(port=os.environ.get('PORT', 9000)))
manager.add_command('shell', Shell(make_context=_make_context))
manager.add_command('db', MigrateCommand)
manager.add_command('assets', ManageAssets)

if __name__ == '__main__':
    manager.run()
