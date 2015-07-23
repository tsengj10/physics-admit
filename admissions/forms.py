from django.forms import ModelForm

import datetime

from admissions.models import College

class CollegeForm(ModelForm):
  class Meta:
    model = College
    exclude = [ 'name', 'adss_code', 'key', ]

