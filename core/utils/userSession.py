import logging
from threading import local
from django.utils.deprecation import MiddlewareMixin

# Logger for debugging purposes
logger = logging.getLogger(__name__)

# Thread-local storage
_user = local()


class CurrentUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        try:
            _user.id = getattr(request.user, 'id', None)
            _user.branch = getattr(request.user, 'branch', None)
            _user.branch_id = getattr(_user.branch, 'id', None)
        except Exception as e:
            logger.warning(f"CurrentUserMiddleware error: {e}")


def get_current_user():
    """
    Returns the current user's ID stored in thread-local storage.
    """
    return getattr(_user, 'id', None)


def get_current_user_branch():
    """
    Returns the current user's branch object stored in thread-local storage.
    """
    return getattr(_user, 'branch', None)


def get_current_user_branch_id():
    """
    Returns the current user's branch ID stored in thread-local storage.
    """
    return getattr(_user, 'branch_id', None)
