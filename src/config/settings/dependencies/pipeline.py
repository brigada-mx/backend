"""
Bug(s) in django-pipeline mean that it reads everything under STATICFILE_DIRS
and copies all of it to STATIC_ROOT on every petition. Because NFS reads
are slow, this destroys performance if there are lots of files under
STATIC_URL. Therefore, all node_modules directories must be outside of
STATIC_URL.

WARNING: any .less or .sass file will be compiled into a .css file in
development. If these files are not in .gitignore, the compiled versions
will be added to version control!

Notes: pipeline causes Django to source static files, in dev, from
STATIC_ROOT, instead of STATICFILE_DIRS. STATIC_ROOT is no longer
merely a directory where things are collected to de deployed to
production. The documentation for the package is weak sauce...
"""

PIPELINE = {
    # enable compression of static files under pipeline
    'PIPELINE_ENABLED': True,
    'PIPELINE_COLLECTOR_ENABLED': True,
    'CSS_COMPRESSOR': 'pipeline.compressors.yuglify.YuglifyCompressor',
    'JS_COMPRESSOR': 'pipeline.compressors.yuglify.YuglifyCompressor',
    'COMPILERS': (
        'pipeline.compilers.less.LessCompiler',
    ),
    'STYLESHEETS': {
        'landing': {
            'source_filenames': (
                'landing/css/landing.less',
            ),
            'output_filename': 'dist/landing/css/style.min.css'
        },
        'docs': {
            'source_filenames': (
                'docs/css/docs.less',
                'vendor/alertifyjs/alertify.css',
            ),
            'output_filename': 'dist/docs/css/style.min.css'
        },
        'endless': {
            'source_filenames': (
                'endless/css/pace.css',
                'endless/css/endless.css',
                'endless/css/endless-skin.css',
                'css/bootstrap_overrides.less',
                'endless/css/morris.css',
                'css/endless_overrides.less',
            ),
            'output_filename': 'dist/endless/css/style.min.css'
        },
        'staff': {
            'source_filenames': (
                'pickadate/lib/themes/default.css',
                'pickadate/lib/themes/default.date.css',
                'pickadate/lib/themes/default.time.css',
                'vendor/alertifyjs/alertify.css',
                'css/staff.less',
                'css/general_overrides.less',
            ),
            'output_filename': 'dist/css/staff.min.css'
        },
        'staff_reservation': {
            'source_filenames': (
                'ladda/dist/ladda.min.css',
                'vendor/alertifyjs/alertify.css',
                'selectize/dist/css/selectize.css',
                'reservations/css/reservation.css',
            ),
            'output_filename': 'dist/staff/css/new-reservation.css'
        },
        'reservations_public': {
            'source_filenames': (
                'bootstrap/dist/css/bootstrap.min.css',
                'font-awesome/css/font-awesome.min.css',
                'ladda/dist/ladda.min.css',
                'pickadate/lib/compressed/themes/default.css',
                'pickadate/lib/compressed/themes/default.date.css',
                'pickadate/lib/compressed/themes/default.time.css',
                'eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker.min.css',
                'public/css/base.css',
                'reservations/css/reservation-lead.css',
                'reservations/css/style.css',
                'landing/css/calculator.less'
            ),
            'output_filename': 'dist/css/reservations_public.min.css'
        }
    },
    'JAVASCRIPT': {
        'endless': {
            'source_filenames': (
                # Waypoint
                'endless/js/waypoints.min.js',
                # LocalScroll
                'endless/js/jquery.localscroll.min.js',
                # ScrollTo
                'endless/js/jquery.scrollTo.min.js',
                # Modernizr
                'endless/js/modernizr.min.js',
                # Popup Overlay
                'endless/js/jquery.popupoverlay.min.js',
                # morris
                'endless/js/morris.min.js',
                'endless/js/rapheal.min.js',
                # Slimscroll
                'endless/js/jquery.slimscroll.min.js',
                # Endless
                'endless/js/endless/endless.js',
            ),
            'output_filename': 'dist/endless/js/scripts.min.js'
        },
        'landing': {
            'source_filenames': (
                'vendor/js/waypoints.min.js',
                'landing/js/landing.js',
            ),
            'output_filename': 'dist/landing/js/landing.min.js'
        },
        'formsets': {
            'source_filenames': (
                'vendor/js/jquery.formset.js',
                'js/formsets.js',
            ),
            'output_filename': 'dist/js/formsets.js'
        },
        'staff': {
            'source_filenames': (
                'iCheck/icheck.min.js',
                'jquery-cookie/jquery.cookie.js',
                'vendor/js/jquery.formset.js',
                'vendor/alertifyjs/alertify.js',
                'underscore/underscore-min.js',
                'pickadate/lib/picker.js',
                'pickadate/lib/picker.date.js',
                'pickadate/lib/picker.time.js',
                'moment/moment.js',
            ),
            'output_filename': 'dist/js/staff.js'
        },
        'staff_reservation': {
            'source_filenames': (
                'selectize/dist/js/standalone/selectize.js',
                'jquery.payment/lib/jquery.payment.js',
                'ladda/dist/spin.min.js',
                'ladda/js/ladda.js',
                'ladda/js/ladda.jquery.js',
                'vendor/alertifyjs/alertify.js',
            ),
            'output_filename': 'dist/staff/js/new-reservation.js'
        },
        'reservations_public': {
            'source_filenames': (
                'jquery.payment/lib/jquery.payment.js',
                'moment/moment.js',
                'pickadate/lib/compressed/picker.js',
                'pickadate/lib/compressed/picker.date.js',
                'pickadate/lib/compressed/picker.time.js',
                'moment/min/moment.min.js',
                'eonasdan-bootstrap-datetimepicker/build/js/bootstrap-datetimepicker.min.js',
                'ladda/dist/spin.min.js',
                'ladda/js/ladda.js',
                'ladda/js/ladda.jquery.js',
                'iCheck/icheck.min.js',
            ),
            'output_filename': 'dist/js/reservations_public.js'
        }
    }
}
