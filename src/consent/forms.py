from __future__ import unicode_literals

from django import forms
from consent.models import ConsentItem

CONSENT_CHOICES = ((True, 'Yes'), (False, 'No'))

class ConsentForm(forms.ModelForm):
    
    answer = forms.ChoiceField(choices=CONSENT_CHOICES, widget=forms.RadioSelect, label='')
    
    class Meta:
        model = ConsentItem
        fields = ['answer']
    
    def clean_answer(self):
        if str(self.instance.required_answer) != str(self.cleaned_data['answer']):
            raise forms.ValidationError(
                'You must answer "%s" to this question to proceed'%(
                    'Yes' if self.instance.required_answer else 'No')
            )

ConsentFormSet = forms.modelformset_factory(ConsentItem, form=ConsentForm, extra=0)

class ConsentAdminForm(forms.ModelForm):
    
    required_answer = forms.ChoiceField(choices=CONSENT_CHOICES)
    
    class Meta:
        model = ConsentItem
        fields = ['description', 'required_answer']
