from django.core.urlresolvers import reverse_lazy
from django.conf.urls import url, include
from django.conf import settings
from django.contrib import admin
from django.views.generic import RedirectView

urlpatterns = [
               
    url(r'^admin/', admin.site.urls),
    url(r'^ckeditor/', include('ckeditor_uploader.urls')),
    url(r'^app/', include('pjapp.urls')),
    url(r'^widgets/', include('pjwidgets.urls')),
    url(r'^$', RedirectView.as_view(pattern_name='pjapp:home')),
    
]

if 'consent' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'^consent/', include('consent.urls')),
    ]