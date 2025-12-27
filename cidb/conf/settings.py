from pathlib import Path

import django_stubs_ext
import environ
from django.urls import reverse_lazy

from cidb.conf.apm.sentry_config import configure_sentry

django_stubs_ext.monkeypatch()

from cidb.conf.logging import configure_logging  # noqa: E402

configure_logging()

BASE_DIR = Path(__file__).resolve().parent.parent
DJANGO_ROOT = BASE_DIR / "cidb"

env = environ.Env()

DEBUG = env.bool("DEBUG", default=False)
SECRET_KEY = env.str("SECRET_KEY", default="insecure-secret-key" if DEBUG else environ.Env.NOTSET)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["http://127.0.0.1"])

INTERNAL_IPS = ["127.0.0.1"]

INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "cidb.src.core.apps.CoreConfig",
    "cidb.src.db.apps.DbConfig",
    "cidb.src.incidents.apps.IncidentsConfig",
    "corsheaders",
    "unfold",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]

LOGGING_CONFIG: None = None

MIDDLEWARE = [
    "cidb.src.core.middleware.RequestLoggingMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "cidb.src.core.middleware.AuthHeaderMiddleware",
    "cidb.src.core.middleware.VisitorTrackingMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cidb.conf.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cidb.conf.wsgi.application"

DATABASES = {
    "default": env.db(default="postgres://postgres:postgres@postgres:5432/postgres"),
}
DATABASES["default"]["CONN_MAX_AGE"] = 600
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

VALKEY_URL = env.str("VALKEY_URL", default="valkey://valkey:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_valkey.cache.ValkeyCache",
        "LOCATION": VALKEY_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_valkey.client.DefaultClient",
        },
        "KEY_PREFIX": "cidb",
        "TIMEOUT": 3600,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = env.str("STATIC_ROOT", default="/app/staticfiles")

AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default="")
AWS_S3_ACCESS_KEY_ID = env.str("AWS_S3_ACCESS_KEY_ID", default="")
AWS_S3_SECRET_ACCESS_KEY = env.str("AWS_S3_SECRET_ACCESS_KEY", default="")
AWS_S3_CUSTOM_DOMAIN = env.str(
    "AWS_S3_CUSTOM_DOMAIN",
    default=f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com",
)

MEDIA_LOCATION = "media"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIA_LOCATION}/"  # noqa: E231

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "location": MEDIA_LOCATION,
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# noinspection PyUnresolvedReferences
AUTH_USER_MODEL = "core.ACAUser"
LOGIN_URL = "admin:login"
LOGIN_REDIRECT_URL = "/admin/"
LOGOUT_REDIRECT_URL = "/"

configure_sentry()

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["https://cidb.dev", "https://incidents.caves.org"],
)
CORS_EXPOSE_HEADERS = [
    "CIDB-User-Authenticated",
    "CIDB-User-ID",
    "CIDB-User-Email",
    "CIDB-User-Name",
    "CIDB-User-Is-Staff",
    "CIDB-User-Is-Editor",
]

if DEBUG:
    CORS_ALLOWED_ORIGINS += ["http://localhost:5173", "http://127.0.0.1:5173"]

SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True

UNFOLD = {
    "SITE_TITLE": "CIDB Admin",
    "SITE_HEADER": "CIDB",
    "SITE_SUBHEADER": "Caving Incident Database",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Incidents",
                "icon": "warning",
                "items": [
                    {
                        "title": "Incidents",
                        "icon": "article",
                        "link": reverse_lazy("admin:incidents_incident_changelist"),
                    },
                    {
                        "title": "Caves",
                        "icon": "landscape",
                        "link": reverse_lazy("admin:incidents_cave_changelist"),
                    },
                    {
                        "title": "Locations",
                        "icon": "location_on",
                        "link": reverse_lazy("admin:incidents_location_changelist"),
                    },
                    {
                        "title": "Geographic Areas",
                        "icon": "public",
                        "link": reverse_lazy("admin:incidents_geographicarea_changelist"),
                    },
                    {
                        "title": "Tags",
                        "icon": "label",
                        "link": reverse_lazy("admin:incidents_tag_changelist"),
                    },
                    {
                        "title": "Injuries",
                        "icon": "healing",
                        "link": reverse_lazy("admin:incidents_injury_changelist"),
                    },
                ],
            },
            {
                "title": "People",
                "icon": "people",
                "items": [
                    {
                        "title": "People",
                        "icon": "person",
                        "link": reverse_lazy("admin:incidents_person_changelist"),
                    },
                    {
                        "title": "Incident Persons",
                        "icon": "group",
                        "link": reverse_lazy("admin:incidents_incidentperson_changelist"),
                    },
                ],
            },
            {
                "title": "Publications",
                "icon": "library_books",
                "items": [
                    {
                        "title": "Publications",
                        "icon": "menu_book",
                        "link": reverse_lazy("admin:incidents_publication_changelist"),
                    },
                    {
                        "title": "Authors",
                        "icon": "edit",
                        "link": reverse_lazy("admin:incidents_author_changelist"),
                    },
                    {
                        "title": "Documents",
                        "icon": "description",
                        "link": reverse_lazy("admin:incidents_document_changelist"),
                    },
                    {
                        "title": "Publication Pages",
                        "icon": "insert_drive_file",
                        "link": reverse_lazy("admin:incidents_publicationpage_changelist"),
                    },
                ],
            },
            {
                "title": "Sources",
                "icon": "source",
                "items": [
                    {
                        "title": "Source Files",
                        "icon": "folder_open",
                        "link": reverse_lazy("admin:incidents_sourcefile_changelist"),
                    },
                    {
                        "title": "Source Extracts",
                        "icon": "content_cut",
                        "link": reverse_lazy("admin:incidents_sourceextract_changelist"),
                    },
                    {
                        "title": "Incident References",
                        "icon": "link",
                        "link": reverse_lazy("admin:incidents_incidentreference_changelist"),
                    },
                ],
            },
            {
                "title": "Reports & Analytics",
                "icon": "analytics",
                "items": [
                    {
                        "title": "Content Reports",
                        "icon": "flag",
                        "link": reverse_lazy("admin:incidents_contentreport_changelist"),
                    },
                    {
                        "title": "Search Queries",
                        "icon": "search",
                        "link": reverse_lazy("admin:incidents_searchquery_changelist"),
                    },
                    {
                        "title": "Search Clicks",
                        "icon": "mouse",
                        "link": reverse_lazy("admin:incidents_searchclick_changelist"),
                    },
                ],
            },
            {
                "title": "Data Management",
                "icon": "storage",
                "items": [
                    {
                        "title": "Duplicate Groups",
                        "icon": "content_copy",
                        "link": reverse_lazy("admin:incidents_duplicategroup_changelist"),
                    },
                    {
                        "title": "Incident Embeddings",
                        "icon": "psychology",
                        "link": reverse_lazy("admin:incidents_incidentembedding_changelist"),
                    },
                    {
                        "title": "Operation Logs",
                        "icon": "history",
                        "link": reverse_lazy("admin:incidents_dataoperationlog_changelist"),
                    },
                ],
            },
            {
                "title": "Users & Auth",
                "icon": "admin_panel_settings",
                "items": [
                    {
                        "title": "Users",
                        "icon": "person",
                        "link": reverse_lazy("admin:core_acauser_changelist"),
                    },
                    {
                        "title": "Visitors",
                        "icon": "visibility",
                        "link": reverse_lazy("admin:core_visitor_changelist"),
                    },
                    {
                        "title": "Groups",
                        "icon": "groups",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
        ],
    },
}
