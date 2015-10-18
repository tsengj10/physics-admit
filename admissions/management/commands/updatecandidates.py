from django.core.management.base import BaseCommand, CommandError

import csv
from datetime import date

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
      inf = csv.eader(csvfile)
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
          for i in range(1,len(fields)):
            if i >= len(row):
              break
            if re.match('^college[1-6]$', fields[i]):
              change = change or changecollege(s, fields[i], row[i])
            elif fields[i] == "date":
              pattime = datetime.datetime.strptime(row[i], '%d/%m/%Y')
            elif fields[i] == "maths" or fields[i] == "pat_maths":
              s.pat_maths = row[i]
              s.pat_time = pattime
              change = True
            elif fields[i] == "physics" or fields[i] == "pat_physics":
              s.pat_physics = row[i]
              s.pat_time = pattime
              change = True

          if change:
            self.stdout.write("Data changed for {} (ucas {})".format(row[0], s.ucas_id)
            s.save()

