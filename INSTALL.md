##### Detailed installation instructions

If you want to walk through the complete setup captured above in `make setup`, use the following commands to bootstrap your development environment:

**python app**:

```bash
# clone the repo
git clone https://github.com/bsmithgall/beacon-standalone
# change into the repo directory
cd beacon-standalone
# install python dependencies
# NOTE: if you are using postgres.app, you will need to make sure to
# set your PATH to include the bin directory. For example:
# export PATH=$PATH:/Applications/Postgres.app/Contents/Versions/9.4/bin/
pip install -r requirements/dev.txt
# if you are looking to deploy, you won't need dev dependencies.
# uncomment & run this command instead:
# pip install -r requirements.txt
```

**NOTE**: The app's configuration lives in [`settings.py`](https://github.com/codeforamerica/beacon-standalone/blob/master/beacon/settings.py). When different configurations (such as `DevConfig`) are referenced in the next sections, they are contained in that file.

**email**:

The app uses [Flask-Mail](https://pythonhosted.org/Flask-Mail/) to handle sending emails. This includes emails about subscriptions to various contracts, notifications about contracts being followed, and others. In production, the app relies on [Sendgrid](https://sendgrid.com/), but in development, it uses the [Gmail SMTP server](https://support.google.com/a/answer/176600?hl=en). If you don't need to send emails, you can disable emails by setting `MAIL_SUPPRESS_SEND = True` in the `DevConfig` configuration object.

If you would like to send email over the Gmail SMTP server, you will need to add two environment variables: `MAIL_USERNAME` and `MAIL_PASSWORD`. You can use Google's [app passwords](https://support.google.com/accounts/answer/185833?hl=en) to create a unique password only for the app.

**database**:

```bash
createdb beacon;
```

If you have Postgres running on a non-standard port, you'll need to export a `DATABASE_URL` environment variable with a proper [SQLAlchemy database configuration string](http://docs.sqlalchemy.org/en/rel_1_0/core/engines.html#postgresql).

```bash
# upgrade your database to the latest version
python manage.py db upgrade
```

By default, SQLAlchemy logging is turned off. If you want to enable it, you'll need to add a `SQLALCHEMY_ECHO` flag to your environment.

**front-end**:

If you haven't installed [npm](https://www.npmjs.com/), please consult this [howto](https://github.com/codeforamerica/howto/blob/master/Node.js.md#install) for the best way to do so. On Mac, you can also use [homebrew](http://brew.sh/).

Once you install node, run the following:

```bash
# install bower, less, and uglifyjs
# you may need to use sudo
npm install -g bower
npm install -g uglifyjs
npm install -g less
# use bower to install the dependencies
bower install
```

**login and user accounts**

A manage task has been created to allow you to quickly create a user to access the admin and other staff-only tasks. To add an email, run the following command (NOTE: if you updated your database as per above, you will probably want to give youself a role of 1, which will give you superadmin privledges), putting your email/desired role in the appropriate places:

```bash
python manage.py seed_user -e <your-email-here> -r <your-desired-role> -p <your-desired password>
# if you leave the password blank, it will default to `password`
```

**WARNING** The password you create on seeding will be stored as plaintext. Please reset this password as soon as possible!

**up and running**

If you boot up the app right now, it will have no data. If you want to add some data, a small manage task has been added to allow for quick data importation.

```bash
# run the data importers
python manage.py seed
```

Now you should be ready to roll with some seed data to get you started!

```bash
# run the server
python manage.py server
```

**Celery and Redis**

To get started with development, you won't need to do any additional setup. However, if you want to emulate the production environment on your local system, you will need to install Redis and configure Celery. To do everything, you'll need to run Redis (our broker), Celery (our task queue), and the app itself all at the same time.

Get started by installing redis. On OSX, you can use [homebrew](http://brew.sh/):

```bash
brew install redis
```

Once this is all installed, you should see a handy command you can use to start the Redis cluster locally (something like the following):

```bash
redis-server /usr/local/etc/redis.conf
```

Now, redis should be up and running. Before we launch our web app, we'll need to configure it to use our Celery/Redis task queue as opposed to using the [eager fake queue](http://celery.readthedocs.org/en/latest/configuration.html#celery-always-eager). Navgate to `beacon/settings.py`. In the `DevConfig`, there should be three settings related to Celery. Commenting out `CELERY_ALWAYS_EAGER` and un-commenting `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` will signal the app to use Redis for Celery's broker.

At this point, you'll be abel to boot up the celery worker. Our app's celery workers live in `beacon/celery_worker.py`. Start them as follows:

```bash
celery --app=beacon.celery_worker:celery worker --loglevel=debug
```

You can log at a higher level than debug (info, for example), if you want to get fewer messages.  Finally, we'll need to start our web app. You can do this as normal:

```bash
python manage.py server
```

When all of these are running, you should be ready to go!
