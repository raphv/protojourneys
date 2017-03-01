import json
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from pjapp import forms as app_forms
from pjapp import models as app_models

def tag_autocomplete(request):
    tags = app_models.Tag.objects.filter(text__icontains=request.GET['term'])
    taglist = [tag.text for tag in tags]
    return HttpResponse(
                        json.dumps(taglist),
                        content_type='application/json'
                        )

def home(request):
    projects = app_models.Project.objects.filter( creator = request.user )
    tags = app_models.Tag.objects.annotate(
                                project_count=Count('project',distinct=True)
                                ).filter(
                                         project_count__gt=0
                                         ).order_by(
                                                    '-project_count',
                                                    'text'
                                                    )
    context = {
               'projects': projects,
               'project_tags': tags,
               }
    return render(request, "pjapp/authoring/home.html", context)

def explore_project(request, **kwargs):
    context = {}
    project = get_object_or_404(
                                app_models.Project,
                                pk = kwargs.get('pk', None),
                                creator = request.user,
                                )
    context['project'] = project
    context['path_tags'] = app_models.Tag.objects.filter(path__project=project)
    context['activity_tags'] = app_models.Tag.objects.filter(activity__project=project)
    return render(request, "pjapp/authoring/explore_project.html", context)

def explore_path(request, **kwargs):
    context = {}
    path = get_object_or_404(
                      app_models.Path,
                      pk=kwargs.get('pk', None),
                      project__creator = request.user,
                      )
    context['path'] = path
    position_indexes = path.positions.exclude(block_position_y=None).values_list('block_position_y')
    position_indexes = set([pi[0] for pi in position_indexes])
    context['activity_blocks'] = [
                                  path.positions.filter(block_position_y=pi).select_related('activity')
                                  for pi in position_indexes
                                  ]
    context['unsorted_activities'] = path.positions.filter(block_position_y=None).select_related('activity')
    links = path.links.all()
    link_dict = [
                  {
                   'from': link.from_activity_id if link.from_activity_id else '_START_',
                   'to': link.to_activity_id if link.to_activity_id else '_END_',
                   'id': link.id,
                   }
                  for link in links
                  ]
    blocks_dict = [{
       'activity_id': block.activity_id,
       'activity_name': block.activity.title,
       'pos_x': block.block_position_x, 
    } for block in path.positions.all()]
    context['links'] = links
    context['links_json'] = json.dumps(link_dict)
    context['blocks_json'] = json.dumps(blocks_dict)
    context['share_url'] = request.build_absolute_uri(
         location = reverse('pjapp:play:start_path', kwargs={'slug': path.slug})
     )
    context['user_count'] = User.objects.filter(recordedpath__path=path).distinct().count()
    return render(request, "pjapp/authoring/explore_path.html", context)

def path_usage_details(request, **kwargs):
    context = {}
    path = get_object_or_404(
                      app_models.Path,
                      pk=kwargs.get('pk', None),
                      project__creator = request.user,
                      )
    context['path'] = path
    context['user_count'] = User.objects.filter(recordedpath__path=path).distinct().count()
    commentqs = app_models.Comment.objects.filter(recorded_path__path=path)
    if not request.user.is_superuser:
        commentqs = commentqs.filter(
            Q(public=True)
            | Q(user=request.user)
        )
    context['comments'] = commentqs
    context['activitycount'] = app_models.Activity.objects.filter(
        steps__recorded_path__path=path
    ).distinct().count()
    context['stepcount'] = app_models.RecordedStep.objects.filter(
        recorded_path__path=path
    ).count()
    context['customactivities'] = app_models.CustomActivity.objects.filter(
        steps__recorded_path__path=path
    ).distinct().count()
    context['popular_activities'] = path.get_activities().annotate(
        step_count = Count('steps')
    ).order_by('-step_count')
    return render(request, "pjapp/authoring/path_usage_detail.html", context)

def review_path(request, **kwargs):
    path = get_object_or_404(
                            app_models.RecordedPath,
                            pk = kwargs.get('pk', None),
                            path__project__creator = request.user,
                            )
    comments = path.comments
    if path.user != request.user and not request.user.is_superuser:
        comments = comments.filter(public=True)
    context = { 'recpath': path, 'comments': comments }
    return render(
                  request,
                  "pjapp/authoring/review_path.html",
                  context,
                  )

def explore_activity(request, **kwargs):
    context = {}
    activity = get_object_or_404(
                      app_models.Activity,
                      pk=kwargs.get('pk', None),
                      project__creator = request.user,
                      )
    context['activity'] = activity
    paths = app_models.Path.objects.filter(
                                           positions__activity=activity
                                           )
    context['paths'] = paths.distinct()
    context['tags'] = app_models.Tag.objects.filter(
                                         path__in=paths
                                         ).distinct()
    if request.user.is_superuser:
        context['comments'] = activity.comments.all()
    else:
        context['comments'] = activity.comments.filter(
                                                       Q(public=True)
                                                       | Q(user=request.user)
                                                       )
    return render(request, "pjapp/authoring/explore_activity.html", context)

def preview_activity(request, **kwargs):
    context = {}
    activity = get_object_or_404(
                      app_models.Activity,
                      pk=kwargs.get('pk', None),
                      project__creator = request.user,
                      )
    context['activity'] = activity
    return render(request, "pjapp/authoring/preview_activity.html", context)

def create_project(request):
    context = {}
    if request.method == 'POST':
        form = app_forms.EditProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.creator = request.user
            project.save()
            return redirect('pjapp:author:explore_project',pk=project.id)
    else:
        form = app_forms.EditProjectForm()
    context['form'] = form
    return render(request, "pjapp/authoring/create_project.html", context)

def edit_project(request, **kwargs):
    context = {}
    project = get_object_or_404(
                                app_models.Project,
                                pk = kwargs['pk'],
                                creator = request.user,
                                )
    context['project'] = project
    if request.method == 'POST':
        form = app_forms.EditProjectForm(request.POST, instance = project)
        if form.is_valid():
            project = form.save()
            return redirect('pjapp:author:explore_project',pk=project.id)
    else:
        form = app_forms.EditProjectForm(instance = project)
    context['form'] = form
    return render(request, "pjapp/authoring/edit_project.html", context)

@require_POST
def delete_project(request):
    project = get_object_or_404(
                                app_models.Project,
                                pk = request.POST['project_id'],
                                creator = request.user,
                                )
    project.delete()
    next = request.POST.get('next',reverse('pjapp:author:home'))
    return HttpResponseRedirect(next)

def create_activity(request, **kwargs):
    context = {}
    project = get_object_or_404(
                                app_models.Project,
                                pk = kwargs['pk'],
                                creator = request.user,
                                )
    context['project'] = project
    if request.method == 'POST':
        form = app_forms.EditActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.project = project
            activity.save()
            url = reverse(
                'pjapp:author:explore_activity',
                kwargs = {'pk': activity.id},
            )
            return HttpResponseRedirect(url)
    else:
        form = app_forms.EditActivityForm()
    context['form'] = form
    return render(request, "pjapp/authoring/create_activity.html", context)

def edit_activity(request, **kwargs):
    context = {}
    activity = get_object_or_404(
                                app_models.Activity,
                                pk = kwargs['pk'],
                                project__creator = request.user,
                                )
    context['activity'] = activity
    if request.method == 'POST':
        form = app_forms.EditActivityForm(request.POST, instance = activity)
        if form.is_valid():
            activity = form.save()
            return redirect('pjapp:author:explore_activity',pk=activity.id)
    else:
        form = app_forms.EditActivityForm(instance = activity)
    context['form'] = form
    return render(request, "pjapp/authoring/edit_activity.html", context)

@require_POST
def delete_activity(request):
    activity = get_object_or_404(
                                app_models.Activity,
                                pk = request.POST['activity_id'],
                                project__creator = request.user,
                                )
    activity.delete()
    next = request.POST.get('next',reverse('pjapp:author:home'))
    return HttpResponseRedirect(next)

def create_path(request, **kwargs):
    context = {}
    project = get_object_or_404(
                                app_models.Project,
                                pk = kwargs['pk'],
                                creator = request.user,
                                )
    context['project'] = project
    if request.method == 'POST':
        form = app_forms.EditPathForm(request.POST)
        if form.is_valid():
            path = form.save(commit=False)
            path.project = project
            path.save()
            return redirect('pjapp:author:explore_path',pk=path.id)
    else:
        form = app_forms.EditPathForm()
    context['form'] = form
    return render(request, "pjapp/authoring/create_path.html", context)

def edit_path(request, **kwargs):
    context = {}
    path = get_object_or_404(
                                app_models.Path,
                                pk = kwargs['pk'],
                                project__creator = request.user,
                                )
    context['path'] = path
    if request.method == 'POST':
        form = app_forms.EditPathForm(request.POST, instance = path)
        if form.is_valid():
            path = form.save()
            return redirect('pjapp:author:explore_path',pk=path.id)
    else:
        form = app_forms.EditPathForm(instance = path)
    context['form'] = form
    return render(request, "pjapp/authoring/edit_path.html", context)

@require_POST
def delete_path(request):
    path = get_object_or_404(
                                app_models.Path,
                                pk = request.POST['path_id'],
                                project__creator = request.user,
                                )
    path.delete()
    next = request.POST.get('next',reverse('pjapp:author:home'))
    return HttpResponseRedirect(next)

@require_POST
def create_link(request):
    path = get_object_or_404(
                                app_models.Path,
                                pk = request.POST['path_id'],
                                project__creator = request.user,
                                )
    if request.POST.get('from_id',''):
        from_activity_id = app_models.Activity.objects.get(
                                            pk = request.POST['from_id'],
                                            project = path.project,
                                            ).id
    else:
        from_activity_id = None
    if request.POST.get('to_id',''):
        to_activity_id = app_models.Activity.objects.get(
                                            pk = request.POST['to_id'],
                                            project = path.project,
                                            ).id
    else:
        to_activity_id = None
    app_models.PathLink.objects.create(
                            path = path,
                            from_activity_id = from_activity_id,
                            to_activity_id = to_activity_id
                            )
    return redirect('pjapp:author:explore_path',pk=path.id)

@require_POST
def delete_link(request):
    path_link = get_object_or_404(
                                app_models.PathLink,
                                pk = request.POST['link_id'],
                                path__project__creator = request.user,
                                )
    path_id = path_link.path.id
    path_link.delete()
    return redirect('pjapp:author:explore_path',pk=path_id)