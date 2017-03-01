from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from consent.models import ConsentItem, UserConsent
from consent.forms import ConsentFormSet
from django.conf import settings

@login_required
def consent_view(request):
    user_consent, created = UserConsent.objects.get_or_create(
        user = request.user,
    )
    formset = ConsentFormSet(request.POST or None, queryset=ConsentItem.objects.all())
    next = (request.POST or request.GET).get('next',settings.BASE_URL)
    if formset.is_valid():
        user_consent.consented = True
        user_consent.save()
        return redirect(next)
    else:
        user_consent.consented = False
        user_consent.save()
    context = {
        'formset': formset,
        'next': next,
    }
    return render(request, "consent/consent.html", context)

@user_passes_test(lambda u: u.is_superuser)
def move_consent_item(request, pk=None, direction=None):
    consent_item = get_object_or_404(
        ConsentItem,
        pk = pk
    )
    if direction == 'up':
        consent_item.move_up()
    elif direction == 'down':
        consent_item.move_down()
    return redirect('admin:consent_consentitem_changelist')