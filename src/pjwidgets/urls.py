from django.conf import settings
from django.conf.urls import url
from pjwidgets import views
if 'consent' in settings.INSTALLED_APPS:
    from consent.decorators import consent_required as access_decorator
else:
    from django.contrib.auth.decorators import login_required as access_decorator

app_name = 'pjwidgets'

urlpatterns = [
    url(r'^delete/$', access_decorator(views.delete_widget), name='delete_widget'),
    url(r'^add/$', access_decorator(views.add_widget), name='add_widget'),
    url(r'^move/$', access_decorator(views.move_widget), name='move_widget'),
    url(r'^edit/(?P<pk>\d+)/$', access_decorator(views.dispatch_edit), name='edit_widget'),
    url(r'^preview/(?P<pk>\d+)/$', access_decorator(views.dispatch_preview), name='preview_widget'),
    
    url(r'^ajax/checklist/$', access_decorator(views.ajax_checklist), name='ajax_checklist'),
    
    url(r'^ajax/oembed/$', access_decorator(views.ajax_oembed), name='ajax_oembed'),
    
    url(r'^qrencode/$', access_decorator(views.qr_encode), name='qrencode'),
    url(r'^artcode/svg/(?P<code>(?:\d\:)+\d)/$', views.artcode_encode, name='artcode_encode'),
    url(r'^artcode/experience/(?P<project_id>\d+)/$', views.artcode_experience, name='artcode_experience'),
    url(r'^code-content/create/(?P<project_id>\d+)/$', access_decorator(views.create_code_content), name='create_code_content'),
    url(r'^code-content/edit/(?P<codecontent_id>\d+)/$', access_decorator(views.edit_code_content), name='edit_code_content'),
    url(r'^code-content/delete/$', access_decorator(views.delete_code_content), name='delete_code_content'),
    url(r'^code-availability/$', access_decorator(views.switch_code_availability), name='switch_code_availability'),
    url(r'^ccb/(?P<codecontent_id>\d+)/$', access_decorator(views.code_callback), name='codecallback'),
    url(r'^ccb/(?P<codecontent_id>\d+)/step/(?P<step_id>\d+)/$', access_decorator(views.code_callback), name='codecallback'),
]