from threading import local
from django.contrib.auth.decorators import login_required
from django.utils.deprecation import MiddlewareMixin

 
_user = local()

 
class CurrentUserMiddleware(MiddlewareMixin):
    
    def process_request(self, request):
        try:
            _user.value = request.user
        except:
            pass
 
def get_current_user():
    try:
        return _user.value
    except AttributeError:
        return None
    except:
        return None
    
 