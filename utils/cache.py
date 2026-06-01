from django.core.cache import caches


def get_cache():
    """Lazy access to the default cache to avoid startup failures."""
    return caches['default']
