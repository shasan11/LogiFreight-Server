from django.core.cache import cache
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from django.utils.deprecation import MiddlewareMixin

from core.seeders.seed_default import seed_all_defaults


class DefaultDataSeedMiddleware(MiddlewareMixin):
    """
    Put this middleware at the TOP of MIDDLEWARE.
    It seeds defaults once per schema (tenant) using cache lock.
    """

    CACHE_LOCK_TTL_SECONDS = 60
    CACHE_DONE_TTL_SECONDS = 60 * 60 * 12  # 12 hours (adjust)

    def process_request(self, request):
        # avoid seeding for static/media/admin if you want
        path = getattr(request, "path", "") or ""
        if path.startswith("/static/") or path.startswith("/media/"):
            return None

        schema_name = getattr(connection, "schema_name", "default")  # works with django-tenants
        if schema_name == "public":
            return None

        done_key = f"default_seed_done:{schema_name}"
        if cache.get(done_key):
            return None

        lock_key = f"default_seed_lock:{schema_name}"
        got_lock = cache.add(lock_key, "1", timeout=self.CACHE_LOCK_TTL_SECONDS)
        if not got_lock:
            return None

        try:
            seed_all_defaults(schema_name=schema_name)
            cache.set(done_key, "1", timeout=self.CACHE_DONE_TTL_SECONDS)
        except (OperationalError, ProgrammingError):
            # DB tables not ready (migrations running) => don't die on requests
            return None

        return None
