from django.core.urlresolvers import reverse
from django.db.models import Count, Q
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from pjapp import models as app_models
from pjapp import forms as app_forms

def home(request):
    paths = app_models.Path.objects.filter(
        listed_publicly=True,                         
    )
    tags = app_models.Tag.objects.annotate(
        path_count=Count('path',distinct=True)
    ).filter(
        path__in = paths
    ).order_by(
        '-path_count',
        'text',
    )
    
    context = {
        'paths': paths,
        'path_tags': tags,
    }
    if request.user.is_authenticated():
        context['ongoing_paths'] = request.user.recordedpath_set.filter(date_ended=None)
        context['finished_paths'] = request.user.recordedpath_set.exclude(date_ended=None)
    return render(
                  request,
                  "pjapp/playing/home.html",
                  context,
                  )


def play_step(request, **kwargs):
    context = {}
    step = get_object_or_404(
                             app_models.RecordedStep,
                             pk = kwargs.get('pk', None),
                             recorded_path__user = request.user)
    context['step'] = step
    context['comments'] = step.get_activity().comments.filter(
                                                        Q(user = request.user)
                                                        | Q(public = True),
                                                        )
    context['status_icon'] = {
                              'P': 'fa-arrow-right',
                              'S': 'fa-step-forward',
                              'D': 'fa-check',
                              }[step.status]
    if step.status != 'P' and step.next_step is None and step.recorded_path.is_ongoing():
        context['show_continue'] = True
    return render(
                  request,
                  "pjapp/playing/play_step.html",
                  context,
                  )

def path_next(request, **kwargs):
    context = {}
    recorded_path = get_object_or_404(
                             app_models.RecordedPath,
                             pk = kwargs.get('pk', None),
                             user = request.user
                             )
    step = recorded_path.steps.last()
        
    context['step'] = step
    context['comments'] = step.get_activity().comments.filter(
                                                        Q(user = request.user)
                                                        | Q(public = True),
                                                        )
    
    activityqs = app_models.Activity.objects.filter(
                                         project = recorded_path.path.project
                                         )
    if recorded_path.path and not step.has_custom_activity():
        linksqs = app_models.PathLink.objects.filter(
                                          path = recorded_path.path,
                                          from_activity = step.activity,
                                          )
        context['destinations'] = [{
                                   'title': link.get_to_activity_title(),
                                   'id': link.to_activity_id,
                                   } for link in linksqs]
        context['hide_other'] = True
        otherqs = activityqs.exclude(
                                     backward_links__in = linksqs,
                                     )
    else:
        context['destinations'] = []
        context['hide_other'] = False
        otherqs = activityqs.all()
    context['other_destinations'] = [{
                                      'title': activity.title,
                                      'id': activity.id
                                      } for activity in otherqs]
    alldests = context['destinations'] + context['other_destinations']
    has_none = len([dest for dest in alldests if dest['id'] == None])
    if not has_none:
        context['other_destinations'] += [{
                                           'title': 'End of trajectory',
                                           'id': None
                                           }]

    context['custom_destinations'] = app_models.CustomActivity.objects.filter(
                                                                  project = recorded_path.path.project,
                                                                  user = request.user,
                                                                          )
    return render(
                  request,
                  "pjapp/playing/after_step.html",
                  context,
                  )

def is_number(val):
    try:
        int(val)
        return True
    except:
        return False

def next(request, recorded_path):
    
    path_index = recorded_path.steps.count()
    if path_index:
        from_step = recorded_path.steps.last()
    else:
        from_step = None
    
    custom_activity_field = request.POST.get('custom-activity-id','')
    next_activity_field = request.POST.get('next-activity-id','')
    
    if custom_activity_field == 'CREATE':
        next_activity = app_models.CustomActivity.objects.create(
                                                         user = request.user,
                                                         project = recorded_path.path.project,
                                                         )
        to_step = app_models.RecordedStep.objects.create(
                                              recorded_path = recorded_path,
                                              custom_activity = next_activity,
                                              path_index = path_index,
                                              )
        if from_step:
            from_step.next_step = to_step
            from_step.save()
        destination = "%s?next=%s"%(
                                    reverse(
                                            'pjapp:play:edit_custom_activity',
                                            kwargs = {'pk': next_activity.id },
                                            ),
                                    reverse(
                                            'pjapp:play:play_step',
                                            kwargs = {'pk': to_step.pk },
                                            ),
                                    )
        return HttpResponseRedirect(destination)
    
    if not is_number(custom_activity_field) and not is_number(next_activity_field):
        recorded_path.date_ended = timezone.now()
        recorded_path.save()
        return redirect('pjapp:play:home')
    
    if is_number(next_activity_field):
        next_activity = get_object_or_404(
                                      app_models.Activity,
                                      pk = next_activity_field,
                                      project = recorded_path.path.project
                                      )
        to_step = app_models.RecordedStep.objects.create(
                                              recorded_path = recorded_path,
                                              activity = next_activity,
                                              path_index = path_index,
                                              is_canonical = (request.POST.get('is-canonical','0') == '1'),
                                              )
    if is_number(custom_activity_field):
        next_activity = get_object_or_404(
                                      app_models.CustomActivity,
                                      pk = custom_activity_field,
                                      project = recorded_path.path.project
                                      )
        to_step = app_models.RecordedStep.objects.create(
                                              recorded_path = recorded_path,
                                              custom_activity = next_activity,
                                              path_index = path_index,
                                              )
    if from_step:
        from_step.next_step = to_step
        from_step.save()
    return redirect(
                    'pjapp:play:play_step',
                    pk = to_step.pk,
                    )

@require_POST
def next_step(request):
    from_step = get_object_or_404(
                                  app_models.RecordedStep,
                                  pk = request.POST['step-id'],
                                  recorded_path__user = request.user,
                                  )
    return next(request, from_step.recorded_path)

@require_POST
def finish_step(request):
    from_step = get_object_or_404(
                                  app_models.RecordedStep,
                                  pk = request.POST['step-id'],
                                  recorded_path__user = request.user,
                                  )
    from_step.status = request.POST['step-status']
    from_step.date_ended = timezone.now()
    from_step.save()
    return redirect(
                    'pjapp:play:path_next',
                    pk = from_step.recorded_path.pk,
                    )

def start_path(request, **kwargs):
    context = {}
    path = get_object_or_404(
        app_models.Path,
        slug = kwargs.get('slug', None),
    )
    context['path'] = path
    destinations = path.links.filter(from_activity=None)
    context['ongoing_paths'] = request.user.recordedpath_set.filter(
        date_ended = None,
        path = path
    )
    context['destinations'] = app_models.Activity.objects.filter(
                                                         backward_links__in = destinations
                                                         )
    context['other_destinations'] = app_models.Activity.objects.filter(
                                                               project = path.project
                                                               ).exclude(
                                                                         backward_links__in = destinations
                                                                         )
    context['custom_destinations'] = app_models.CustomActivity.objects.filter(
                                                                          project = path.project,
                                                                          user = request.user,
                                                                              )
    return render(
                  request,
                  "pjapp/playing/start_path.html",
                  context,
                  )

@require_POST
def start_path_next(request):
    path = get_object_or_404(
                             app_models.Path,
                             pk=request.POST['path-id']
                             )
    project = path.project
    recorded_path = app_models.RecordedPath.objects.create(
                                                user = request.user,
                                                path = path,
                                                title = request.POST.get('title', ''),
                                                )
    return next(request, recorded_path)

def review_path(request, **kwargs):
    path = get_object_or_404(
                            app_models.RecordedPath,
                            pk = kwargs.get('pk', None),
                            user = request.user,
                            )
    if request.method == 'POST':
        path.title = request.POST['title']
        path.save()
    context = { 'recpath': path }
    return render(
                  request,
                  "pjapp/playing/review_path.html",
                  context,
                  )

def resume_path(request, **kwargs):
    path = get_object_or_404(
                            app_models.RecordedPath,
                            pk = kwargs.get('pk', None),
                            user = request.user,
                            )
    if path.is_ongoing():
        last_step = path.steps.last()
        if last_step.status == 'P':
            return redirect('pjapp:play:play_step', pk = last_step.id)
        else:
            return redirect('pjapp:play:path_next', pk = path.id)
    else:
        return redirect('pjapp:play:review_path', pk = path.id)

@require_POST
def ajax_comment(request):
    create_dict = {
               'user':             request.user,
               'rating':           request.POST.get('rating', ''),
               'public':           (request.POST.get('public', '0') == '1'),
               'content':          request.POST.get('content', ''),
               'image':            request.FILES.get('image', None),
               }
    activity_id = request.POST.get('activity_id', None)
    if activity_id:
        create_dict['activity_id'] = activity_id
    custom_activity_id = request.POST.get('custom_activity_id', None)
    if custom_activity_id:
        create_dict['custom_activity_id'] = custom_activity_id
    recpath_id = request.POST.get('recorded_path_id', None)
    if recpath_id:
        create_dict['recorded_path_id'] = recpath_id
    doc_item = app_models.Comment.objects.create(**create_dict)
    context = {'comment': doc_item}
    return render(
                  request,
                  "pjapp/partials/comment.html",
                  context
                  )

def edit_custom_activity(request, **kwargs):
    context = {}
    activity = get_object_or_404(
                                app_models.CustomActivity,
                                pk = kwargs['pk'],
                                user = request.user,
                                )
    context['activity'] = activity
    if request.method == 'POST':
        form = app_forms.CustomActivityForm(request.POST, instance = activity)
        if form.is_valid():
            activity = form.save()
            return HttpResponseRedirect(
                                        request.POST.get('next', reverse('pjapp:play:home'))
                                        )
        else:
            context['next'] = request.POST.get('next','')
    else:
        form = app_forms.CustomActivityForm(instance = activity)
        context['next'] = request.GET.get('next','')
    context['form'] = form
    return render(request, "pjapp/playing/edit_custom_activity.html", context)

@require_POST
def delete_recorded_path(request):
    path = get_object_or_404(
                                app_models.RecordedPath,
                                pk = request.POST['recorded_path_id'],
                                user = request.user,
                                )
    path.delete()
    next = request.POST.get('next',reverse('pjapp:play:home'))
    return HttpResponseRedirect(next)