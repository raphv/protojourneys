from functools import wraps
from django.contrib.auth.decorators import login_required
from django.utils.decorators import available_attrs
from django.http import HttpResponseRedirect, QueryDict
from django.core.urlresolvers import reverse
from consent.models import UserConsent

def consent_required(view_func):
    
    @login_required
    @wraps(view_func, assigned=available_attrs(view_func))
    def decorated_view(request, *args, **kwargs):
        user_consent, created = UserConsent.objects.get_or_create(
            user = request.user,
        )
        if user_consent.consented:
            return view_func(request, *args, **kwargs)
        q = QueryDict(mutable=True)
        q['next'] = request.get_full_path()
        url = '%s?%s'%(
            reverse('consent:consent'),
            q.urlencode(safe='/')
        )
        return HttpResponseRedirect(url)
    
    return decorated_view