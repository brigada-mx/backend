# BOWER SETTINGS
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

BOWER_INSTALLED_APPS = (
    'underscore#1.8.3',
    'sifter#0.4.5',
    'js-cookie#2.0.4',
    'jquery-zoom#1.7.15',
    'iCheck#1.0.2',
    'jquery.cookie#1.4.1',
    'spin.js#2.0.2',
    'lightbox2#2.8.2',
    'jquery.payment#1.3.2',
    'jquery#2.2.1',
    'microplugin#0.0.3',
    'datatables.net-dt#1.10.11',
    'moment-timezone#0.4.1',
    'pickadate#3.5.6',
    'moment#2.10.6',
    'jquery-cookie#1.4.1',
    'font-awesome#4.7.0',
    'bootstrap#3.3.5',
    'eonasdan-bootstrap-datetimepicker#4.17.37',
    'datatables.net#1.10.11',
    'selectize#0.12.1',
    'seiyria-bootstrap-slider#6.1.6',
    'ladda#0.9.8',
    'bootstrap-switch#3.3.2',
    'bootstrap-daterangepicker#2.1.24',
    'dragula.js#3.7.1',
    'signature_pad#1.5.3',
    'materialize#0.97.8',
)

BOWER_COMPONENTS_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'components')
