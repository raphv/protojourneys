from django.conf.urls import include, url
from django.views.generic import TemplateView
from django.conf import settings
from pjapp.views import common, playing, authoring
from django.contrib.admin.views.decorators import staff_member_required
if 'consent' in settings.INSTALLED_APPS:
    from consent.decorators import consent_required as access_decorator
else:
    from django.contrib.auth.decorators import login_required as access_decorator

app_name = 'pjapp'

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name="pjapp/home.html"), name='home'),
    url(r'^login/$', common.register_or_login, name='register_or_login'),
    url(r'^fake-mobile/$', TemplateView.as_view(template_name="pjapp/fake_mobile.html"), name='fake_mobile'),
    
    url(r'^trajectory/(?P<path_pk>\d+)/svg/$', access_decorator(common.svgpath), name='svg_path'),
    url(r'^trajectory/recorded/(?P<recorded_path_pk>\d+)/svg/$', access_decorator(common.svgpath), name='svg_path'),
]

play_patterns = ([    
    url(r'^$', playing.home, name='home'),
    url(r'^start/(?P<slug>[\w-]+)/$', access_decorator(playing.start_path), name='start_path'),
    url(r'^trajectory/start/$', access_decorator(playing.start_path_next), name='start_path_next'),
    url(r'^trajectory/step/(?P<pk>\d+)/$', access_decorator(playing.play_step), name='play_step'),
    url(r'^trajectory/next/(?P<pk>\d+)/$', access_decorator(playing.path_next), name='path_next'),
    url(r'^trajectory/next/$', access_decorator(playing.next_step), name='next_step'),
    url(r'^trajectory/finish-step/$', access_decorator(playing.finish_step), name='finish_step'),
    url(r'^trajectory/(?P<pk>\d+)/review/$', access_decorator(playing.review_path), name='review_path'),
    url(r'^trajectory/(?P<pk>\d+)/resume/$', access_decorator(playing.resume_path), name='resume_path'),
    url(r'^custom-activity/(?P<pk>\d+)/edit/$', access_decorator(playing.edit_custom_activity), name='edit_custom_activity'),
    url(r'^trajectory/delete/$', access_decorator(playing.delete_recorded_path), name='delete_recorded_path'),
    
    url(r'^ajax/submit-comment/$', access_decorator(playing.ajax_comment), name='ajax_comment'),
], 'play')

author_patterns = ([
    url(r'^$', staff_member_required(authoring.home), name='home'),
    url(r'^project/(?P<pk>\d+)/$', staff_member_required(authoring.explore_project), name='explore_project'),
    url(r'^trajectory/(?P<pk>\d+)/$', staff_member_required(authoring.explore_path), name='explore_path'),
    url(r'^trajectory/(?P<pk>\d+)/usage-details/$', staff_member_required(authoring.path_usage_details), name='path_usage_details'),
    url(r'^trajectory/(?P<pk>\d+)/review/$', staff_member_required(authoring.review_path), name='review_path'),
    url(r'^activity/(?P<pk>\d+)/$', staff_member_required(authoring.explore_activity), name='explore_activity'),
    url(r'^project/new/$', staff_member_required(authoring.create_project), name='create_project'),
    url(r'^project/(?P<pk>\d+)/edit/$', staff_member_required(authoring.edit_project), name='edit_project'),
    url(r'^project/delete/$', staff_member_required(authoring.delete_project), name='delete_project'),
    url(r'^project/(?P<pk>\d+)/new-activity/$', staff_member_required(authoring.create_activity), name='create_activity'),
    url(r'^activity/(?P<pk>\d+)/edit/$', staff_member_required(authoring.edit_activity), name='edit_activity'),
    url(r'^activity/(?P<pk>\d+)/preview/$', staff_member_required(authoring.preview_activity), name='preview_activity'),
    url(r'^activity/delete/$', staff_member_required(authoring.delete_activity), name='delete_activity'),
    url(r'^project/(?P<pk>\d+)/new-trajectory/$', staff_member_required(authoring.create_path), name='create_path'),
    url(r'^trajectory/(?P<pk>\d+)/edit/$', staff_member_required(authoring.edit_path), name='edit_path'),
    url(r'^trajectory/delete/$', staff_member_required(authoring.delete_path), name='delete_path'),
    url(r'^link/create/$', staff_member_required(authoring.create_link), name='create_link'),
    url(r'^link/delete/$', staff_member_required(authoring.delete_link), name='delete_link'),
    
    url(r'^ajax/tag-autocomplete/$', staff_member_required(authoring.tag_autocomplete), name='tag_autocomplete'),
], 'author')

urlpatterns += [
    url(r'^play/', include(play_patterns)),
    url(r'^author/', include(author_patterns)),
]