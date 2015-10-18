from django.forms import ModelForm
from django.forms.models import inlineformset_factory

import datetime

from admissions.models import College, InterviewTeam

class CollegeForm(ModelForm):
  class Meta:
    model = College
    exclude = [ 'name', 'adss_code', 'key', ]

InterviewTeamFormset = inlineformset_factory(College, InterviewTeam, 
    fields = [ 'names', 'location', 'notes', ],
    can_delete=True, extra=1)

