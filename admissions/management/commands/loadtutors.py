from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, User

import csv

from admissions.models import *

class Command(BaseCommand):
  help = 'Load tutors'

  def add_arguments(self, parser):
    parser.add_argument('filename', nargs='?', default='tutors.csv')

  def handle(self, *args, **options):
    filename = options['filename']

    with open(filename, 'r') as csvfile:
      firstline = True
      f = csv.reader(csvfile, delimiter=',', quotechar='"')
      for row in f:
        if firstline:
          firstline = False
        else:
          user_id = row[0].strip()
          college_name = row[1].strip()
          first_name = row[2].strip()
          surname = row[3].strip()
          role = row[4].strip()
          email = row[5].strip()
          self.stdout.write('User {} ({} {})\n'.format(user_id, first_name, surname))

          is_superuser = (role == 'admin')
          is_staff = (role == 'admin')
          if role == 'readonly':
            gs = [ Group.objects.get(name='Readonly') ]
          else:
            if len(college_name) > 3:
              cs = College.objects.filter(name=college_name)
            else:
              cs = College.objects.filter(adss_code=college_name.upper())
            if len(cs) > 0:
              gs = [ Group.objects.get(name=cs[0].adss_code) ]
            else:
              self.stderr.write("Unrecognized college {}".format(college_name))
              continue

          u, created = User.objects.update_or_create(username=user_id,
                         defaults = { 'first_name': first_name,
                                      'last_name': surname,
                                      'is_active': True,
                                      'is_superuser': is_superuser,
                                      'is_staff': is_staff,
                                      'email': email,
                                      })
          self.stdout.write('{0} {1}'.format(user_id, 'created' if created else 'updated'))
          if u.groups != gs:
            u.groups = gs
            u.save()
            self.stdout.write('  groups updated')
