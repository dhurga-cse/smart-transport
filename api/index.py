import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'smart_transport'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'smart_transport.settings'

import django
django.setup()

from django.core.handlers.wsgi import WSGIHandler
app = WSGIHandler()
