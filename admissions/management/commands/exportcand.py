from django.core.management.base import BaseCommand, CommandError

import csv
import sys

from admissions.models import *

class Command(BaseCommand):
  output_transaction = True
  help = "Export candidate information to stdout in csv form"
    
  def handle(self, *args, **options):
    out = csv.writer(sys.stdout, quoting=csv.QUOTE_ALL)
    fields = [ 'pk', 'ucas_id','surname','forenames','preferred_name', 'birth_date', 'selected_college', 'school_details' ]
    for f in args:
      fields.append(f)
    out.writerow(fields)
    for s in Candidate.objects.all().order_by('info__surname','info__forenames').select_related('info').prefetch_related('info__schools'):
      c = s.info
      data = [ s.pk, s.ucas_id, c.surname, c.forenames, c.preferred_name, c.birth_date, s.college_selected.adss_code ]
      school_list = c.schools.filter(student=c).order_by('-start_date')
      if len(school_list) > 0:
        data.append(school_list[0].school_details)
      else:
        data.append("")
      for f in args:
        data.append(getattr(s,f))
      out.writerow(data)

