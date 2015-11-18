from django.core.management.base import BaseCommand, CommandError

import re
import csv
from datetime import date, datetime

from admissions.models import *

def changecollege(candidate, field, newvalue):
  if len(newvalue) > 3:
    # compare against full college name
    if getattr(candidate, field) == None or newvalue != getattr(candidate, field).name:
      c = College.objects.get(name=newvalue)
      if c:
        setattr(candidate, field, c)
        return True
  else:
    # compare against college code
    nv = newvalue.upper()
    #sys.stdout.write("Field {}, old = {}, new = {}\n".format(field, getattr(candidate,field).adss_code, nv))
    if getattr(candidate, field) == None or nv != getattr(candidate, field).adss_code:
      c = College.objects.get(adss_code=nv)
      if c:
        setattr(candidate, field, c)
        return True
  return False

class Command(BaseCommand):
  help = 'Update candidate fields from csv'

  def add_arguments(self, parser):
    parser.add_argument('filename', nargs='?', default='test')

  def handle(self, *args, **options):
    filename = options['filename']
    with open(filename, 'r') as csvfile:
      inf = csv.reader(csvfile)
      first = True
      for row in inf:
        if first:
          fields = row
          first = False
        else:
          try:
            if fields[0] == 'pk':
              s = Candidate.objects.get(pk=row[0])
            elif fields[0] == 'ucas_id':
              s = Candidate.objects.get(ucas_id=row[0])
          except ObjectDoesNotExist:
            self.stderr.write('Candidate with {0}={1} does not exist'.format(fields[0],row[0]))
            continue

          change = False
          changepat = False
          pattime = datetime.datetime(2015,11,4,14,0,0,0)
          for i in range(1,len(fields)):
            fname = fields[i].lower()
            if i >= len(row):
              break
            if re.match('^college[1-6]$', fname):
              change = change or changecollege(s, fname, row[i])
            elif fname == "date":
              pattime = datetime.datetime.strptime(row[i], '%d/%m/%Y')
            elif fname == "maths" or fname == "pat_maths":
              s.pat_maths = row[i]
              s.pat_time = pattime
              change = True
            elif fname == "physics" or fname == "pat_physics":
              s.pat_physics = row[i]
              s.pat_time = pattime
              change = True
            elif re.match('^Q[0-9]+$', fname) and len(row[i]) > 0:
              current_value = getattr(s.pat, fname)
              if s.pat.date == None or float(current_value) != float(row[i]):
                setattr(s.pat, fname, float(row[i]))
                changepat = True

          if change:
            self.stdout.write("Data changed for {} (ucas {})".format(row[0], s.ucas_id))
            s.save()
          if changepat:
            self.stdout.write("PAT details changed for {} (ucas {})".format(row[0], s.ucas_id))
            s.pat.date = pattime.date()
            s.pat.save()

