from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission

import csv
from datetime import date

from admissions.models import *

class Command(BaseCommand):
  help = 'Start a new database instance from scratch'

  def handle(self, *args, **options):
    load_college_table()
    load_school_types()
    load_qual_types()
    create_college_groups()
    ovs = OverallState(state=OverallState.DEVELOPMENT)
    ovs.save()

def load_college_table():
  firstline = 1
  with open('admissions/fixtures/college-table.csv','rb') as csvfile:
    f = csv.reader(csvfile)
    for row in f:
      if firstline:
        firstline = 0
      else:
        p = College(name = row[0], \
                    adss_code = row[1], \
                    total_places = int(row[2]), \
                    physphil_places = int(row[3]), \
                    key = row[4]
                    )
        p.save()
        print('Created college {}'.format(p))

def load_school_types():
  firstline = 1
  with open('admissions/fixtures/school-types-phys.csv','rb') as csvfile:
    f = csv.reader(csvfile)
    for row in f:
      if firstline:
        firstline = 0
      else:
        p = PhysicsSchoolType(adss_type = row[0], \
                              adss_description = row[1], \
                              physics_type = row[2])
        p.save()
        print('Created school type {}'.format(p))

def toBoolean(str):
  if len(str) > 0:
    return str[0].lower() in [ 'y', 't' ]
  else:
    return False

def load_qual_types():
  firstline = 1
  with open('admissions/fixtures/qual-types.csv','rb') as csvfile:
    f = csv.reader(csvfile)
    for row in f:
      if firstline:
        firstline = 0
      else:
        p = QualificationType(name = row[0],
                              exam_type = row[1],
                              dual_award = toBoolean(row[2]),
                              short_course = toBoolean(row[3]),
                              short_name = row[4])
        p.save()
        print('Created qualification type {}'.format(p))

def create_college_groups():
  pns = ['add_logentry',
         'add_comment',
         'add_offer',
         'change_offer',
         'delete_offer',
         ]
  ps = []
  for pn in pns:
    ps.append(Permission.objects.get(codename=pn))
  colleges = College.objects.all()
  for college in colleges:
    group, created = Group.objects.get_or_create(name=college.adss_code)
    if created:
      group.permissions = ps
      group.save()
      print('Created user group "{1}" for "{0}"'.format(college, group))
  # and then add a read-only group
  group, created = Group.objects.get_or_create(name='Readonly')
  print('Created Readonly user group')

