# -*- coding: utf-8 -*-
from flask_assets import Bundle, Environment

less = Bundle(
    'less/main.less',
    filters='less',
    output='public/css/common.css',
    depends=('less/*.less', 'less/**/*.less', 'less/**/**/*.less')
)

opportunities_less = Bundle(
    'less/main.less',
    filters='less',
    output='public/css/front.css',
    depends=('less/*.less', 'less/**/*.less')
)

ie8 = Bundle(
    'libs/html5shiv/dist/html5shiv.js',
    'libs/html5shiv/dist/html5shiv-printshiv.js',
    'libs/respond/dest/respond.min.js',
    filters='uglifyjs',
    output='public/js/html5shiv.js'
)

vendorjs = Bundle(
    'libs/jquery/dist/jquery.js',
    'libs/bootstrap/dist/js/bootstrap.js',
    'libs/moment/moment.js',
    'libs/eonasdan-bootstrap-datetimepicker/src/js/bootstrap-datetimepicker.js',
    filters='uglifyjs',
    output='public/js/common.js'
)

opportunitiesjs = Bundle(
    'js/*.js',
    filters='uglifyjs',
    output='public/js/front.js'
)

assets = Environment()
test_assets = Environment()

# register our javascript bundles
assets.register('ie8', ie8)
assets.register('vendorjs', vendorjs)
assets.register('opportunitiesjs', opportunitiesjs)

# register our css bundles
assets.register('css_all', less)
assets.register('opportunities_less', opportunities_less)
