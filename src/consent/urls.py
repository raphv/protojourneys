from django.conf.urls import url
from consent import views

app_name = 'consent'

urlpatterns = [
     url(r'$', views.consent_view, name='consent'),
     url(r'move-item/(?P<pk>\d+)/(?P<direction>up|down)/$', views.move_consent_item, name='move-item')
]