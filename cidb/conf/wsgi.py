import os

from django.core.wsgi import get_wsgi_application

from cidb.conf.apm.logfire_config import configure_logfire

configure_logfire()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings")

application = get_wsgi_application()
