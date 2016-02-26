# Beacon

[![Circle CI](https://circleci.com/gh/dobtco/beacon.svg?style=shield&circle-token=33da8bd876a2490ae1ad74337251100b491eac36)](https://circleci.com/gh/dobtco/beacon)

Beacon is an application for cities to advertise their contract opportunities.

It was originally developed by Code for America 2015 fellows as part of the [Pittsburgh Purchasing Suite](https://github.com/codeforamerica/pittsburgh-purchasing-suite), and is now being maintained by the [Department of Better Technology](https://www.dobt.co).

This repository is currently under *active development and reorganization*, with the goal of creating a redeployment pattern similar to that of [Councilmatic](https://github.com/datamade/django-councilmatic) or [Alavateli](https://github.com/mysociety/alaveteli). We do not recommend using this codebase until this has been completed.

## Technical stuff

Beacon is a [Flask](http://flask.pocoo.org/) app. It uses [Postgres](http://www.postgresql.org/) for a database and uses [bower](http://bower.io/) to manage most of its dependencies. It also uses [less](http://lesscss.org/) to compile style assets. In production, the project uses [Celery](http://celery.readthedocs.org/en/latest/) with [Redis](http://redis.io/) as a broker to handle backgrounding various tasks. Big thanks to the [cookiecutter-flask](https://github.com/sloria/cookiecutter-flask) project for a nice kickstart.

### Dependencies

- Python 2.7 with [virtualenv](https://readthedocs.org/projects/virtualenv/)
- node.js
- Postgresql

### Installation and setup

First, create a virtualenv and activate it. Then:

```bash
git clone git@github.com:dobtco/beacon.git
cd beacon
createdb beacon

# set environment variables - it is recommended that you set these for your
# your virtualenv, using a tool like autoenv or by modifying your activate script
export ADMIN_EMAIL='youremail@someplace.net'
export DEFAULT_DOMAIN='someplace.net'
export CONFIG=beacon.settings.DevConfig

# Install dependencies, add tables to the database, and insert seed data
make setup

# start your server
python manage.py server
```

If you run into trouble, or wish to perform the installation tasks manually, take a look at the detailed instructions in [INSTALL.md](https://github.com/dobtco/beacon/blob/master/INSTALL.md)

### Testing

In order to run the tests, you will need to create a test database:

```bash
createdb beacon_test;
```

To run the tests, run

```bash
script/cibuild
```

from inside the root directory. To view coverage information, open `cover/index.html` in your browser.

## License

See [LICENSE.md](https://github.com/dobtco/beacon/blob/master/LICENSE.md).
