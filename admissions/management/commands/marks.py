from django.core.management.base import BaseCommand, CommandError

from admissions.models import *
from admissions.views import ranked_offers

from Crypto.Cipher import AES
from Crypto import Random
import binascii
import datetime
import calendar

import re
import csv
import json

def render_monthyear(d):
  return '{0}/{1:0>2}'.format(d.month, d.year % 100)

def render_boolean(f):
  if f is None:
    return 'n'
  else:
    return 'y' if f else 'n'

class Command(BaseCommand):
  help = 'Make JSON base documents'

  def add_arguments(self, parser):
    parser.add_argument('time', nargs='?', type=int, default='0')

  def handle(self, *args, **options):
    if options['time'] > 0:
      start_time = options['time']
    else:
      start_time = calendar.timegm(datetime.datetime.utcnow().utctimetuple())

    # exam dictionaries
    self.qnames = { "A-level": "A",
               "AS-level": "AS",
               "Advanced Highers": "AH",
               "Scottish Highers": "AH",
               "Cambridge Pre-U Certificate (Principal Subject)": "CPU",
               "IB Diploma": "IB",
               "USA-American College Testing Program (ACT)": "ACT",
               "USA-SAT Reasoning Test": "SAT",
               #"USA-Advanced Placement Test": "AP",
               }
    self.titles = {}
    self.titles["A"] = { "Physics": "ph",
                    "Physics A": "ph",
                    "Mathematics": "m",
                    "Mathematics (MEI)": "m",
                    "Further Mathematics": "fm",
                    "Further Mathematics (MEI)": "fm",
                    "Mathematics (Further)": "fm",
                    }
    self.titles["AS"] = { "Physics": "ph",
                     "Physics A": "ph",
                     "Mathematics": "m",
                     "Mathematics (MEI)": "m",
                     "Further Mathematics": "fm",
                     "Further Mathematics (MEI)": "fm",
                     "Mathematics (Further)": "fm",
                     }
    self.titles["CPU"] = { "Physics (principal subject)": "ph",
                      "Mathematics (principal subject)": "m",
                      "Further Mathematics (principal subject)": "fm",
                    }
    self.titles["AH"] = { "Physics C069": "ph",
                     "Physics (Revised) C272": "ph",
                     "Physics C272": "ph",
                     "Maths: Maths 1, 2 & 3 C100": "m",
                     }
    self.titles["ACT"] = { "Reading": "r",
                      "Writing": "w",
                      "Mathematics": "m",
                      "Science": "s",
                      "English": "e",
                      }
    self.titles["SAT"] = { "Critical Reading": "r",
                      "Mathematics": "m",
                      "Writing": "w",
                      }
    self.school_types = {
        'C': 0,
        'G': 1,
        'I': 2,
        'M': 3,
        'S': 4,
        'U': 5,
        }
    self.course_types = {
        '3': 3,
        '4': 4,
        'P': 5,
        'Q': 6,
        }

    alls = []
    apps = []
    ntuple = []
    college = {}
    cs = College.objects.all()
    for c in cs:
      college[c.adss_code] = []
    collegekeys = { '': -1 }
    for c in cs:
      collegekeys[c.adss_code] = c.pk

    overallstate = OverallState.objects.current()
    statephase = OverallState.objects.current_ranking_phase()
    ss = Candidate.objects.all()
    for s in ss:
      j = self.make_json(s, overallstate, statephase)
      ntuple.append(self.make_ntrow(s, j, collegekeys))

    # stats ntuple
    f = open('json/details.csv', 'w')
    out = csv.writer(f, quoting=csv.QUOTE_NONE, delimiter=' ')
    for r in ntuple:
      out.writerow(r)

  def add_qual_summary(self, qual, q):
    qtype = q['t']
    # check if we recognize qualification type
    if qtype in self.qnames:
      if self.qnames[qtype] == "IB":
        if self.qnames[qtype] not in qual:
          qual[self.qnames[qtype]] = {}
        # for IB, need to get components for total, physics, mathematics
        qual[self.qnames[qtype]]['total'] = q['r']
      elif q['ti'] in self.titles[self.qnames[qtype]]:
        if self.qnames[qtype] not in qual:
          qual[self.qnames[qtype]] = {}
        qual[self.qnames[qtype]][self.titles[self.qnames[qtype]][q['ti']]] = q['r']

  def calc_sd(self, q, pred):
    """Calculate SDmaths.  1 should indicate study of single maths
       at A level, and 2 further maths at A level.  In between is
       studying further maths at AS (1.3), and having obtained
       further maths at already at AS (1.6).  We might later make
       a distinction between having obtained single or further maths
       at A level as well."""
    qtype = q['t']
    if qtype in self.qnames:
      qtype = self.qnames[qtype]
    else:
      return 0.0
    qti = q['ti']
    if qtype == "A" and qti in self.titles['A']:
      qcode = self.titles['A'][qti]
      if qcode == "fm":
        return 2.0
      elif qcode == "m":
        return 1.0
    elif qtype == "AS" and qti in self.titles['AS']:
      qcode = self.titles['AS'][qti]
      if qcode == "fm":
        return 1.3 if pred else 1.6
    return 0.0

  def order_qual_summary(self, qual):
    s = []
    #self.stdout.write("Qual summary {}".format(qual))
    examkeys = list(qual.keys())
    #self.stdout.write("Keys {}".format(examkeys))
    examkeys.sort()
    for k in examkeys:
      st = []
      tkeys = qual[k].keys()
      for t in tkeys:
        st.append(t + qual[k][t])
      s.append(k + ":" + ",".join(st))
    t = "; ".join(s)
    if len(t) == 0:
      t = '({})'.format(len(qual))
    return t

  def make_json(self, candidate, overallstate, statephase):
    student = candidate.info
    name = student.surname + ", " + student.forenames
    if len(student.preferred_name) > 0:
      name = name + " (" + student.preferred_name + ")"

    pm = candidate.pat_maths
    pp = candidate.pat_physics

    int1 = candidate.interview1
    int2 = candidate.interview2
    int3 = candidate.interview3
    int4 = candidate.interview4
    int5 = candidate.interview5
    js = pm + pp + 3*(int1 + int2) + 4*int3

    j = { \
      "pk": candidate.pk, \
      "status": "", \
      "offer": "", \
      "pm": "{}".format(pm), \
      "pp": "{}".format(pp), \
      "pt": "{}".format(pm+pp), \
      "i1": "{}".format(int1) if int1 > 0 else '', \
      "i2": "{}".format(int2) if int2 > 0 else '', \
      "i3": "{}".format(int3) if int3 > 0 else '', \
      "i4": "{}".format(int4) if int4 > 0 else '', \
      "i5": "{}".format(int5) if int5 > 0 else '', \
      "js": "{}".format(js) if js > 0 else '', \
      "rank": "{}".format(candidate.stored_rank), \
      "name": name, \
      "g": student.gender, \
      "y": student.matriculation_year(), \
      "scht": "U", \
      "course": candidate.course_type, \
      "sdm": "0", \
      "pred": "None", \
      "obt": "None", \
      "care": render_boolean(student.declared_in_care), \
      "gcse": render_boolean(student.gcse), \
      "alev": render_boolean(student.a_level), \
      "offa": render_boolean(student.offa), \
      "offa1": render_boolean(student.offa1), \
      "acorn": render_boolean(student.acorn), \
      "polar": render_boolean(student.polar), \
      "access": render_boolean(student.access), \
      "ovf": render_boolean(student.overall), \
      "c1" : candidate.college1.adss_code if candidate.college1 else '', \
      "c2" : candidate.college2.adss_code if candidate.college2 else '', \
      "c3" : candidate.college3.adss_code if candidate.college3 else '', \
      "c4" : candidate.college4.adss_code if candidate.college4 else '', \
      "c5" : candidate.college5.adss_code if candidate.college5 else '', \
      "c6" : candidate.college6.adss_code if candidate.college6 else '' \
      }

    # add details
    status = ranked_offers(candidate)
    if status == '':
      status = candidate.state
      if status == Candidate.STATE_APPLIED:
        status = ''
      elif status == Candidate.STATE_SUMMONED:
        status = '+' if overallstate == OverallState.LONGLIST else ''
      elif status == Candidate.STATE_DESUMMONED:
        status = 'Desum'
      if candidate.rescued:
        status = status + 'R'
      if candidate.reserved:
        status = status + 'K' # S (for keep)
    j['status'] = status
    offers = candidate.offer.filter(final=True)
    if offers.count() > 0:
      o = offers[0]
      j['offer'] = o.college.adss_code
    apd = {
      'id': candidate.ucas_id,
      'email': student.email,
      'bd': student.birth_date.strftime('%d/%m/%y'),
      # '{0}y{1}m'.format(ap.age.years, ap.age.months),
      'ovs': render_boolean(student.overseas),
      'spec': render_boolean(student.has_special_needs),
      'dcode': student.disability_code,
      'dis': student.disability_notes,
      'tel': student.telephone,
      'mob': student.mobile
    }
    j["det"] = apd

    # school details
    usepre = False
    usepost = False
    schd = []
    for sch in student.schools.all():
      sdet = {
        's': sch.start_date,
        'b': render_monthyear(sch.start_date),
        'e': render_monthyear(sch.end_date),
        'id': sch.ucas_school_id,
        'det': sch.school_details
        }
      if sch.ucas_school_id == student.gcse_school_id:
        sdet['pre'] = student.school_pre16_performance
        sdet['gold'] = student.school_pre16_gold_performance
        usepre = True
      if sch.ucas_school_id == student.a_level_school_id:
        sdet['post'] = student.school_post16_performance
        j['scht'] = sch.school_type.physics_type
        usepost = True
      schd.append(sdet)
    #self.stdout.write("School list for {}:  {}".format(name, schd))

    # sort first by start date, and then school id (school details not reliably well formed)
    # (this depends on python sort order being stable, which is true after python 2.2)
    schd.sort(key=lambda a: a['id'])
    schd.sort(key=lambda a: a['s'], reverse=True)
    for sch in schd:
      del sch['s']

    if not usepre:
      self.stdout.write('Pre16 school id {0} not found for student {1}'.format(
          student.gcse_school_id,name))
      schd.append({'b':'','e':'','id':student.gcse_school_id,'det':'',
                   'pre':student.school_pre16_performance,
                   'gold':student.school_pre16_gold_performance})
    if not usepost:
      self.stdout.write('Post16 school id {0} not found for student {1}'.format(
          student.a_level_school_id,name))
      schd.append({'b':'','e':'','id':student.a_level_school_id,'det':'',
                   'post':student.school_post16_performance})
    j["detsch"] = schd

    # student qualifications
    oqs = []
    pqs = []
    for q in student.qualifications.all():
      qtype = q.qualification_type.short_name if q.qualification_type.short_name else q.qualification_type.name
      qtype = qtype.replace('International Baccalaureate', 'IB')
      units = q.unit_grades.strip().replace('&#10;', '<br>')

      sq = {
        's': q.qualification_date,
        'd': render_monthyear(q.qualification_date),
        'b': q.award_body,
        't': qtype,
        'r': q.result,
        'ti': q.title,
        'g': q.grade,
        'u': units
        }
      if q.predicted_grade or q.result == 'Incomplete':
        sq['r'] = sq['g']
        if sq['r'] == 'Incomplete':
          sq['r'] = '?'
        pqs.append(sq)
      else:
        oqs.append(sq)

    sd = 0.0
    # sort by start date first, then title
    oqs.sort(key=lambda a: a['ti'])
    oqs.sort(key=lambda a: a['s'])
    oqual = {}
    for q in oqs:
      self.add_qual_summary(oqual, q)
      sd = max(sd, self.calc_sd(q, False))
      del q['s']
    oqs.reverse() # to list most recent first

    pqs.sort(key=lambda a: a['ti'])
    pqs.sort(key=lambda a: a['s'])
    pqual = {}
    for q in pqs:
      self.add_qual_summary(pqual, q)
      sd = max(sd, self.calc_sd(q, True))
      del q['s']
    pqs.reverse()

    j["detobt"] = oqs
    j["detpred"] = pqs
    j["sdm"] = "{}".format(sd)

    if len(pqual) > 0:
      j["pred"] = self.order_qual_summary(pqual)
    else:
      j["pred"] = '({})'.format(len(pqs))

    if len(oqual) > 0:
      j["obt"] = self.order_qual_summary(oqual)
    else:
      j["obt"] = '({})'.format(len(oqs))

    j["astar"] = student.qualifications.gcse_a_stars()

    # comments
    if candidate.comments.count() > 0:
      cmts = []
      for c in candidate.comments.all():
        cd = {}
        cd['who'] = c.commenter.get_full_name()
        cd['when'] = "{}".format(c.time)
        cd['t'] = c.text
        cmts.append(cd)
      j["comments"] = cmts

    return j

  def make_ntrow(self, cand, data, collegekeys):
    # row columns:  state pk id gender school sd course c1 c2 c3 c4 c5 c6 pm pp i1 i2 i3 i4 i5 offer offer_course
    #               0     1  2  3      4      5  6      7  8  9  10 11 12 13 14 15 16 17 18 19 20    21
    d = []
    d.append(cand.state)
    d.append(data['pk'])
    d.append(data['det']['id'])
    d.append(1 if data['g'] == 'M' else 2 if data['g'] == 'F' else 3)
    d.append(self.school_types[data['scht']])
    d.append(data['sdm'])
    d.append(self.course_types[data['course']])
    d.append(collegekeys[data['c1']])
    d.append(collegekeys[data['c2']])
    d.append(collegekeys[data['c3']])
    d.append(collegekeys[data['c4']])
    d.append(collegekeys[data['c5']])
    d.append(collegekeys[data['c6']])
    d.append(data['pm'] if data['pm'] else 0)
    d.append(data['pp'] if data['pp'] else 0)
    d.append(data['i1'] if data['i1'] else 0)
    d.append(data['i2'] if data['i2'] else 0)
    d.append(data['i3'] if data['i3'] else 0)
    d.append(data['i4'] if data['i4'] else 0)
    d.append(data['i5'] if data['i5'] else 0)
    pat = cand.pat
    d.append(pat.q1)
    d.append(pat.q2)
    d.append(pat.q3)
    d.append(pat.q4)
    d.append(pat.q5)
    d.append(pat.q6)
    d.append(pat.q7)
    d.append(pat.q8)
    d.append(pat.q9)
    d.append(pat.q10)
    d.append(pat.q11)
    d.append(pat.q12)
    d.append(pat.q13)
    d.append(pat.q14)
    d.append(pat.q15)
    d.append(pat.q16)
    d.append(pat.q17)
    d.append(pat.q18)
    d.append(pat.q19)
    d.append(pat.q20)
    d.append(pat.q21)
    d.append(pat.q22)
    d.append(pat.q23)
    d.append(pat.q24)
    d.append(pat.q25)
    return d

