from django.core.management.base import BaseCommand, CommandError

import csv
from datetime import date

from admissions.models import *

def toBoolean(str):
  if len(str) > 0:
    return str[0].lower() in [ 'y', 't' ]
  else:
    return False

def toNullBoolean(str):
  if len(str) > 0:
    s = str.lower()
    if s[0] in [ 'y', 't' ]:
      return True
    elif s[0] == 'f' or s == 'n' or s == 'no':
      return False
    else:
      return None
  else:
    return None

def toFloat(str):
  if len(str) > 0:
    return float(str.replace(',',''))
  else:
    return None

class Command(BaseCommand):
  help = 'Load candidates'

  def add_arguments(self, parser):
    parser.add_argument('tag', nargs='?', default='test')

  def handle(self, *args, **options):
    tag = options['tag']

    # load candidates
    self.load_cand('admissions/fixtures/cand-{}.csv'.format(tag))
    # then reload to get the one-to-one relation right
    students = { }
    for ca in Candidate.objects.all().select_related('info'):
      students[ca.ucas_id] = ca

    # load qualifications
    self.load_qual(students, 'admissions/fixtures/qualj-{}.csv'.format(tag))

    # load education history
    self.load_ed(students, 'admissions/fixtures/ed-{}.csv'.format(tag))

  def load_cand(self, name):
    with open(name,'r') as csvfile:
      firstline = 1
      f = csv.reader(csvfile, delimiter=',', quotechar='"')
      for row in f:
        if firstline:
          firstline = 0
        else:
          ccode = Candidate.COURSE_FOURYEAR
          if row[15] == Candidate.COURSE_CODE_BAPHYS:
            ccode = Candidate.COURSE_THREEYEAR
          elif row[15] == Candidate.COURSE_CODE_PHYSPHIL:
            ccode = Candidate.COURSE_PHYSPHIL_ONLY

          #self.stdout.write('Candidate {0} {1}'.format(row[0], row[2]))
          a, created = Candidate.objects.update_or_create(ucas_id = row[0],
                         defaults = { 'college_selected':
                           College.objects.get(name=row[34]) if row[34] else None,
                           'course_type': ccode })
          self.stdout.write('{0} {1} {2}'.format(row[0], row[2], 'created' if created else 'updated'))

          s, created = CandidateInfo.objects.update_or_create(candidate = a,
                         defaults = {
                           'forenames': row[1],
                           'surname': row[2],
                           'preferred_name': row[3],
                           'title': row[4],
                           'gender': row[5],
                           'birth_date': datetime.datetime.strptime(row[9],'%d/%m/%Y'),
                           'disability_code': row[6],
                           'disability_notes': row[7],
                           'has_special_needs': (len(row[8]) > 0),
                           'interview_year': 2014,
                           'deferred_entry': toBoolean(row[16]),
                           'overseas': toBoolean(row[17]),
                           'declared_in_care': toNullBoolean(row[29]),
                           'overall': toNullBoolean(row[32]),
                           'access': toNullBoolean(row[27]),
                           'offa': toNullBoolean(row[31]),
                           'acorn': toNullBoolean(row[28]),
                           'polar': toNullBoolean(row[33]),
                           'gcse': toNullBoolean(row[30]),
                           'a_level': toNullBoolean(row[26]),
                           'school_pre16_performance': toFloat(row[20]),
                           'school_pre16_gold_performance': toFloat(row[21]),
                           'school_post16_performance': toFloat(row[24]),
                           'gcse_school_id': row[19],
                           'a_level_school_id': row[23],
                           'mobile': row[10],
                           'telephone': row[11],
                           'email': row[12],
                           'current_passport_country': row[14],
                           'verified_in_care': False })
          self.stdout.write('Candidate {0} {1}'.format(a, 'created' if created else 'updated'))

  def load_ed(self, students, name):
    with open(name,'r') as csvfile:
      firstline = 1
      f = csv.reader(csvfile, delimiter=',', quotechar='"')
      for row in f:
        if firstline:
          firstline = 0
        else:
          if row[7] in students.keys():
            #self.stdout.write('School {0} for student {1}'.format(row[8],row[7]))
            if len(row[9]) > 0:
              if len(row[4]) > 0:
                det = row[9] + ", " + row[4]
              else:
                det = row[9]
            else:
              det = row[4]
            sch, created = School.objects.update_or_create(student = students[row[7]].info,
                    defaults = {
                      'application_scheme': row[1],
                      'start_date': date(month = int(row[5]), year = int(row[11].replace(',','')), day=1),
                      'end_date': date(month = int(row[6]), year = int(row[12].replace(',','')), day=1),
                      'school_details': det,
                      'school_type': PhysicsSchoolType.objects.get(adss_type=(row[13] if row[13] else "U")),
                      'ucas_school_id': row[8],
                      'attendance': row[2]})
            self.stdout.write('School {0} {1}'.format(sch, 'created' if created else 'updated'))

  def load_qual(self, students, name):
    with open(name,'r') as csvfile:
      firstline = 1
      f = csv.reader(csvfile, delimiter=',', quotechar='"')
      for row in f:
        if firstline:
          firstline = 0
        else:
          if row[5] in students.keys():
            #self.stdout.write("Qualification {0} for student {1}".format(row[14],row[5]))
            q, created = Qualification.objects.update_or_create(student = students[row[5]].info,
                  defaults = {
                    'application_scheme': row[1],
                    'qualification_date': date(month = int(row[7]), year = int(row[8].replace(',','')), day=1),
                    'qualification_type': QualificationType.objects.get(name=row[10]) if row[10] else None,
                    'award_body': row[2],
                    'title': row[14],
                    'result': row[12],
                    'grade': row[6] if len(row[6]) > 0 else row[4],
                    'predicted_grade': (len(row[6]) > 0),
                    'test_centre': row[3],
                    'unit_grades': row[15]})
            self.stdout.write('Qualification {0} {1}'.format(q, 'created' if created else 'updated'))

