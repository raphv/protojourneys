from __future__ import unicode_literals

import json
from qrcode import QRCode
from qrcode.image.svg import SvgPathFillImage
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.html import format_html, mark_safe
from django.views.decorators.http import require_POST
from django.contrib.humanize.templatetags.humanize import naturaltime
from pjwidgets.models import ActivityWidget, CheckListInstance, OEmbedHtml, CodeContent, ScanQR, ScanQRInstance
from pjwidgets.oembed import get_oembed
from pjwidgets.forms import EditCodeContentForm
from pjapp.models import Activity, RecordedStep, Path, RecordedPath, Project
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

def dispatch_edit(request, *args, **kwargs):
    widget = get_object_or_404(
        ActivityWidget,
        pk = kwargs['pk'],
        activity__project__creator = request.user,
    )
    return widget.get_widget_instance().render_editor(request, *args, **kwargs)

def dispatch_preview(request, *args, **kwargs):
    widget = get_object_or_404(
        ActivityWidget,
        pk = kwargs['pk'],
    )
    context = {'widget': widget}
    return render(request, "pjwidgets/other/preview.html", context)

@require_POST
def delete_widget(request, *args, **kwargs):
    widget = get_object_or_404(
                               ActivityWidget,
                               pk = request.POST.get('widget_id',None),
                               activity__project__creator = request.user,
                               )
    widget.delete()
    next = request.POST.get('next',reverse('pjapp:author:home'))
    return redirect(next)

@require_POST
def add_widget(request, *args, **kwargs):
    activity =  get_object_or_404(
                               Activity,
                               pk = request.POST.get('activity_id',None),
                               project__creator = request.user,
                               )
    widget = ActivityWidget.objects.create(
                                           activity = activity,
                                           widget_name = request.POST['widget_name'],
                                           )
    return redirect('pjwidgets:edit_widget', pk=widget.id)

@require_POST
def move_widget(request, *args, **kwargs):
    widget = get_object_or_404(
                               ActivityWidget,
                               pk = request.POST.get('widget_id',None),
                               activity__project__creator = request.user,
                               )
    if request.POST.get('direction','up') == 'down':
        widget.move_down()
    else:
        widget.move_up()
    next = request.POST.get('next',reverse('pjapp:author:home'))
    return redirect(next)

@require_POST
def ajax_checklist(request, *args, **kwargs):
    clinstance = get_object_or_404(
        CheckListInstance,
        id = request.POST.get('id', None),
        user = request.user,
    )
    user_list = json.loads(request.POST['contents'])
    if not clinstance.checklist.allow_custom_items:
        base_list = clinstance.checklist.get_tag_list()
        user_list = [item for item in user_list if item in base_list]
    clinstance.set_tag_list(user_list)
    clinstance.save()
    return HttpResponse(
        json.dumps(user_list),
        content_type='application/json'
    )

@require_POST
def ajax_oembed(request, *args, **kwargs):
    res = {}
    url = request.POST.get('url','')
    try:
        if request.POST.get('force', False):
            raise Exception()
        oeh = OEmbedHtml.objects.get(
            url = url
        )
        res['success'] = True
        res['results'] = {
            'html': oeh.embed_html,
            'title': oeh.title,
            'provider_name': '%s (retrieved %s)'%(
                oeh.provider_name,
                naturaltime(oeh.last_updated),
            )
        }
    except:
        try:
            oembed_data = get_oembed(url)
            res['success'] = True
            res['results'] = oembed_data
            oeh, created = OEmbedHtml.objects.get_or_create(url=url)
            oeh.embed_html = oembed_data.get('html','')
            oeh.title = oembed_data.get('title','')
            oeh.provider_name = oembed_data.get('provider_name','')
            oeh.save()
        except Exception as e:
            raise e
            res['success'] = False
            res['message'] = e.message
    if res['success'] and not res['results'].get('html',''):
        img = format_html(
            '<img src="{}" width="{}" height="{}" />',
            res['results']['thumbnail_url'],
            res['results'].get('thumbnail_width',''),
            res['results'].get('thumbnail_height','') 
        ) if 'thumbnail_url' in res['results'] else ''
        res['results']['html'] = format_html(
            '<p class="errors">{}</p><p>{}{}</p>',
            "No embed code available for this URL",
            mark_safe(img),
            res['results'].get('description',''),
        )
    return HttpResponse(
        json.dumps(res),
        content_type='application/json'
    )

def qr_encode(request):
    data = request.GET.get('data','')
    qrc = QRCode(
        box_size = 20,
        image_factory = SvgPathFillImage,
    )
    qrc.add_data(data)
    img = qrc.make_image()
    strio = StringIO()
    img.save(strio)
    res = strio.getvalue()
    strio.close()
    return HttpResponse(
        res,
        content_type='image/svg+xml'
    )

def artcode_encode(request, **kwargs):
    code = kwargs.get('code','')
    regions = [int(region) for region in code.split(':')]
    context = {
        'regions': [{
             'height': region,
             'range': range(region)
         } for region in regions],
        'highest_region': max(regions),
    }
    return render(request, 'pjwidgets/other/artcode.svg', context, content_type='image/svg+xml')

def code_callback(request, **kwargs):
    context = {}
    recorded_step = None
    codecontent = get_object_or_404(
         CodeContent,
         pk = kwargs.get('codecontent_id')
    )
    if 'step_id' in kwargs:
        recorded_step = get_object_or_404(
            RecordedStep,
            pk = kwargs['step_id'],
            recorded_path__user = request.user,
        )
    else:
        candidate_steps = RecordedStep.objects.filter(
            status = 'P',
            activity__widgets__scanqr__active_codes = codecontent,
            recorded_path__user = request.user,
        )
        if not candidate_steps.count():
            activities = Activity.objects.filter(
                widgets__scanqr__active_codes = codecontent
            )
            context['activities'] = activities
            paths = Path.objects.filter(
                listed_publicly = True,
                positions__activity__in = activities
            )
            context['paths'] = paths
            context['recorded_paths'] = RecordedPath.objects.filter(
                user = request.user,
                date_ended = None,
                path__in = paths
            )
            return render(request, "pjwidgets/other/qr-none.html", context)
        if candidate_steps.count() > 1:
            context['codecontent'] = codecontent
            context['candidate_steps'] = candidate_steps.order_by('-date_started')
            return render(request, "pjwidgets/other/qr-many.html", context)
        recorded_step = candidate_steps[0]
    scanqr = recorded_step.activity.widgets.filter(scanqr__active_codes = codecontent)[0].scanqr
    codeinstance, created = ScanQRInstance.objects.get_or_create(
        scanqr = scanqr,
        user = request.user,
        recordedstep = recorded_step
    )
    codeinstance.code = codecontent
    codeinstance.save()
    return redirect('pjapp:play:play_step', pk=recorded_step.pk)

def artcode_experience(request, **kwargs):
    project = get_object_or_404(
        Project,
        pk=kwargs.get('project_id',None)
    )
    res = {
        'actions': [{
            'codes': [code.artcode],
            'match': 'any',
            'name': code.title,
            'showDetail': False,
            'url': request.build_absolute_uri(reverse(
                'pjwidgets:codecallback',
                kwargs={'codecontent_id':code.id}
            )),
        } for code in project.codecontent_set.exclude(artcode='')],
        'author': project.creator.username,
        'availabilities': [{}],
        'description': project.get_description_text(),
        'icon': '',
        'image': '',
        'id': request.build_absolute_uri(),
        'name': project.title,
        'pipeline': ['tile', 'detect',],
    }
    resp = HttpResponse(
        json.dumps(res),
        content_type = 'application/%s'%request.GET.get('format','x-artcode')
    )
    if 'format' not in request.GET:
        resp['Content-Disposition'] = 'attachment; filename="project-%d.artcode"'%project.id
    return resp
    
def create_code_content(request, **kwargs):
    project = get_object_or_404(
        Project,
        pk = kwargs['project_id'],
        creator = request.user,
    )
    next = request.POST.get('next', request.GET.get('next','pjapp:author:home'))
    if request.method == 'POST':
        form = EditCodeContentForm(request.POST)
        if form.is_valid():
            codecontent = form.save(commit=False)
            codecontent.project = project
            codecontent.save()
            return redirect(next)
    else:
        form = EditCodeContentForm()
    context = {
        'project': project,
        'form': form,
        'next': next,
    }
    return render(request, "pjwidgets/other/create_code_content.html", context)

def edit_code_content(request, **kwargs):
    codecontent = get_object_or_404(
        CodeContent,
        pk = kwargs['codecontent_id'],
        project__creator = request.user,
    )
    next = request.POST.get('next', request.GET.get('next','pjapp:author:home'))
    if request.method == 'POST':
        form = EditCodeContentForm(request.POST, instance=codecontent)
        if form.is_valid():
            form.save()
            return redirect(next)
    else:
        form = EditCodeContentForm(instance=codecontent)
    context = {
        'form': form,
        'next': next,
    }
    return render(request, "pjwidgets/other/edit_code_content.html", context)

@require_POST
def delete_code_content(request):
    codecontent = get_object_or_404(
        CodeContent,
        pk = request.POST['codecontent_id'],
        project__creator = request.user,
    )
    codecontent.delete()
    return redirect(request.GET.get('next','pjapp:author:home')) 

@require_POST
def switch_code_availability(request):
    availability = (request.POST.get('availability','0') == '1')
    codecontent = get_object_or_404(
        CodeContent,
        pk = request.POST['codecontent_id'],
        project__creator = request.user,
    )
    scanqr = get_object_or_404(
        ScanQR,
        widget_id = request.POST['widget_id'],
        widget__activity__project_id = codecontent.project_id,
    )
    if availability:
        scanqr.active_codes.add(codecontent)
    else:
        scanqr.active_codes.remove(codecontent)
    return redirect('pjwidgets:edit_widget',pk=scanqr.widget.id)

