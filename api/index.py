import sys
import os

# Add smart_transport project root to path
BASE = os.path.join(os.path.dirname(__file__), '..', 'smart_transport')
sys.path.insert(0, os.path.abspath(BASE))

os.environ['DJANGO_SETTINGS_MODULE'] = 'smart_transport.settings'

from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()
