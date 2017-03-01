from django.core.urlresolvers import reverse
from django.contrib.auth import login, authenticate
from django.db.models import Max
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404
from pjapp import models as app_models
from pjapp import forms as app_forms
import math

def login_and_redirect(request, login_user):
    login(request, login_user)
    next = request.POST.get('next',reverse('pjapp:home'))
    return HttpResponseRedirect(next)

def register_or_login(request):
    context = {
               'currentuser': request.user
               }
    if request.method == 'POST':
        context['next'] = request.POST['next']
        if request.POST["action"] == 'register':
            form = app_forms.CustomRegisterForm(request.POST)
            if form.is_valid():
                new_user = form.save()
                new_user.email = request.POST["email"]
                new_user.save()
                login_user = authenticate(username=request.POST["username"], password=request.POST["password1"])
                return login_and_redirect(request, login_user)
            context['register_form'] = form
        elif request.POST["action"] == 'login':
            form = app_forms.CustomLoginForm(request.POST)
            if form.is_valid():
                login_user = authenticate(username=form.cleaned_data.get("user"), password=form.cleaned_data.get("password"))
                return login_and_redirect(request, login_user)
            context['login_form'] = form
    else:
        context['register_form'] = app_forms.CustomRegisterForm()
        context['login_form'] = app_forms.CustomLoginForm()
        context['next'] = request.GET.get('next',reverse('pjapp:home'))
    return render(request, "pjapp/register_or_login.html", context)

def get_svgpath_context(**kwargs):
    pixbase = 32
    if 'recorded_path_pk' in kwargs:
        recorded_path = get_object_or_404(
            app_models.RecordedPath,
            pk = kwargs['recorded_path_pk'],
        )
        path = recorded_path.path
        if path is None:
            raise Http404
    elif 'path_pk' in kwargs:
        recorded_path = None
        path = get_object_or_404(
            app_models.Path,
            pk = kwargs['path_pk'],
        )
    else:
        raise Http404
    context = {}
    linkedcontent = path.positions.exclude(block_position_y=None)
    maxdict = linkedcontent.aggregate(
        Max('block_position_x')
    )
    width = maxdict['block_position_x__max'] or 1
    height = path.positions.count()
    context['circle_r'] = 10
    context['check_circle_r'] = 9
    context['pixelwidth'] = pixbase * width
    context['pixelheight'] = pixbase * (height + 2)
    context['start_y'] = pixbase/2
    context['end_y'] = context['pixelheight'] - pixbase/2
    context['centre_x'] = context['pixelwidth']/2
    context['fullwidth'] = context['pixelwidth'] + 200
    context['arrowright'] = context['pixelwidth'] + 10
    context['textleft'] = context['pixelwidth'] + 12
    blocks = []
    xy = path.positions.values('block_position_y').annotate(Max('block_position_x'))
    xy = dict([(xxy['block_position_y'],xxy['block_position_x__max']) for xxy in xy])
    counter = 1
    for block in linkedcontent:
        blockres = {
            'id': block.activity_id,
            'title': block.activity.title,
            'y': (.5 + counter) * pixbase,
            'x': (width/2. - xy[block.block_position_y]/2. + block.block_position_x -.5) * pixbase,
            'statuses': [],
        }
        counter += 1
        blocks.append(blockres)
    for block in path.positions.filter(block_position_y=None):
        blockres = {
            'id': block.activity_id,
            'title': block.activity.title,
            'y': (.5 + counter) * pixbase,
            'x': (.5 + (counter%width)) * pixbase,
            'statuses': [],
        }
        counter += 1
        blocks.append(blockres)
    if recorded_path:
        context['start_status'] = 'done'
        if recorded_path.is_ongoing():
            current_activity = recorded_path.steps.last().activity_id
        else:
            current_activity = None
            context['end_status'] = 'done'
        done_activities = recorded_path.steps.filter(status='D').exclude(activity=None)
        done_activities = set([a.activity_id for a in done_activities]) if done_activities else []
        skipped_activities = recorded_path.steps.filter(status='S').exclude(activity=None)
        skipped_activities = set([a.activity_id for a in skipped_activities]) if skipped_activities else []
        for block in blocks:
            if block['id'] == current_activity:
                block['statuses'].append('current')
            if block['id'] in done_activities:
                block['statuses'].append('done')
            if block['id'] in skipped_activities:
                block['statuses'].append('skipped')
    blockdict = dict([(b['id'], b) for b in blocks])
    links = []
    for link in path.links.all():
        if link.from_activity is None:
            from_x = context['centre_x']
            from_y = context['start_y']
        else:
            block = blockdict[link.from_activity_id]
            from_x = block['x']
            from_y = block['y']
        if link.to_activity is None:
            to_x = context['centre_x']
            to_y = context['end_y']
        else:
            block = blockdict[link.to_activity_id]
            to_x = block['x']
            to_y = block['y']
        cx = (to_x + from_x)/2.
        cy = (to_y + from_y)/2.
        r = ((to_x-cx)**2+(to_y-cy)**2)**.5
        rr = (r-context['circle_r'])/r
        links.append({
            'from_x': (cx + (from_x - cx)*rr),
            'from_y': (cy + (from_y - cy)*rr),
            'to_x': (cx + (to_x - cx)*rr),
            'to_y': (cy + (to_y - cy)*rr),
        })
    context['blocks'] = blocks
    context['links'] = links
    return context

def svgpath(request, **kwargs):
    context = get_svgpath_context(**kwargs)
    return render(request, "pjapp/path.svg", context, content_type='image/svg+xml')